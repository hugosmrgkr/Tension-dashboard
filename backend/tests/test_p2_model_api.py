"""P2-02: endpoint prediksi memakai artefak terlatih; paritas fitur training/inferensi; input & error."""
import json
import shutil
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from app import main
from app.baseline import FEATURES, make_training
from app.model_comparison import run_comparison
from app.model_service import inference_features, load_serving_model, ModelUnavailable
from test_cp3_stage1 import client, loaded  # noqa: F401
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope='module')
def model_dir(tmp_path_factory):
    base = tmp_path_factory.mktemp('models')
    run_comparison(ROOT / 'data/sample/Data_Responden_Sintetis.csv', ROOT / 'data/sample/Data_Harian_Sintetis.csv', base / 'experiments')
    return base


@pytest.fixture
def api(loaded, model_dir, monkeypatch):
    monkeypatch.setenv('MODEL_DIR', str(model_dir))
    return loaded


def test_feature_parity_with_training_for_every_window(prepared):
    p, d, s, _ = prepared
    frame = make_training(p, d, s)
    for row in frame.itertuples():
        built = inference_features(p, d, s, row.respondent_id, row.asof_date)
        expected = np.array([getattr(row, f) for f in FEATURES], dtype=float)
        got = np.array([np.nan if built['features'][f] is None else built['features'][f] for f in FEATURES], dtype=float)
        np.testing.assert_allclose(got, expected, equal_nan=True)


def test_predict_returns_model_output_and_metadata(api):
    rid = api.get('/api/meta').json()['respondent_ids'][0]
    r = api.get('/api/model/predict', params={'respondent_id': rid})
    assert r.status_code == 200, r.text
    body = r.json()
    assert 80 < body['prediction_mmHg'] < 220 and body['is_diagnosis'] is False and body['target_approved'] is False
    assert body['model']['algorithm'] == 'Linear Regression' and body['model']['version'] and body['model']['horizon_days'] == 7
    assert set(body['features_used']) == set(FEATURES) and 'SINTETIS' in body['status']
    assert any('baseline naif' in n for n in body['notes'])  # model tidak mengalahkan naif -> peringatan jujur


def test_predict_matches_direct_model_call(api, model_dir, prepared):
    import joblib
    p, d, s, _ = prepared
    frame = make_training(p, d, s).iloc[0]
    model, _info = load_serving_model(model_dir / 'experiments')
    direct = float(model.predict(pd.DataFrame([frame[FEATURES].astype(float)]))[0])
    r = api.get('/api/model/predict', params={'respondent_id': frame.respondent_id, 'asof_date': frame.asof_date})
    assert r.status_code == 200 and r.json()['prediction_mmHg'] == pytest.approx(direct, abs=0.01)


def test_invalid_inputs_are_rejected(api):
    rid = api.get('/api/meta').json()['respondent_ids'][0]
    assert api.get('/api/model/predict').status_code == 422
    assert api.get('/api/model/predict', params={'respondent_id': ''}).status_code == 422
    assert api.get('/api/model/predict', params={'respondent_id': 'x' * 41}).status_code == 422
    assert api.get('/api/model/predict', params={'respondent_id': 'SIM-TIDAK-ADA'}).status_code == 404
    assert api.get('/api/model/predict', params={'respondent_id': rid, 'asof_date': 'bukan-tanggal'}).status_code == 422
    assert api.get('/api/model/predict', params={'respondent_id': rid, 'asof_date': '1999-01-01'}).status_code == 422
    assert api.post('/api/model/predict', params={'respondent_id': rid}).status_code == 405


def test_first_days_lack_seven_day_history(api):
    meta = api.get('/api/meta').json()
    r = api.get('/api/model/predict', params={'respondent_id': meta['respondent_ids'][0], 'asof_date': meta['min_date']})
    assert r.status_code == 422 and 'berturut' in r.json()['detail']


def test_missing_or_tampered_artifact_fails_closed(api, model_dir, tmp_path, monkeypatch):
    rid = api.get('/api/meta').json()['respondent_ids'][0]
    broken = tmp_path / 'm'
    shutil.copytree(model_dir, broken)
    (broken / 'experiments/linear_regression_synthetic.joblib').write_bytes(b'rusak')
    monkeypatch.setenv('MODEL_DIR', str(broken))
    assert api.get('/api/model/predict', params={'respondent_id': rid}).status_code == 409
    monkeypatch.setenv('MODEL_DIR', str(tmp_path / 'kosong'))
    assert api.get('/api/model/predict', params={'respondent_id': rid}).status_code == 409
    with pytest.raises(ModelUnavailable):
        load_serving_model(tmp_path / 'kosong')


def test_comparison_endpoint_serves_verified_artifact(api, model_dir):
    body = api.get('/api/model/comparison').json()
    assert body['available'] and body['artifact_integrity_verified'] and body['target_approved'] is False
    assert len(body['comparison']) == 4


def test_non_synthetic_source_blocks_prediction(api, warehouse_engine):
    from app.models import SourceState
    with Session(warehouse_engine) as db:
        db.get(SourceState, 1).source_kind = 'actual'
        db.commit()
    assert api.get('/api/model/predict', params={'respondent_id': 'SIM001'}).status_code == 409
    assert api.get('/api/model/comparison').json()['available'] is False
