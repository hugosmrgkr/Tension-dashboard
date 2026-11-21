"""Stage 2 contract guards on real P2 artifacts, copied into disposable folders."""
import hashlib
from io import BytesIO
import json
from pathlib import Path
import shutil

import joblib
import numpy as np
import pandas as pd
import pytest
from sqlalchemy.orm import Session

from app import model_registry as registry
from app.baseline import FEATURES, make_training
from app.model_service import load_serving_model, ModelUnavailable
from app.models import SourceState
from test_cp3_stage1 import client, loaded  # noqa: F401

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def bundle(tmp_path):
    folder = tmp_path / 'models/experiments'
    shutil.copytree(ROOT / 'models/experiments', folder)
    return folder


def read_info(folder):
    return json.loads((folder / 'comparison_metrics.json').read_text(encoding='utf-8'))


def rehash_metrics(folder, change):
    """Valid hash on deliberately invalid metadata: test contract guards, not only hashing."""
    path = folder / 'comparison_metrics.json'
    info = read_info(folder)
    change(info)
    raw = (json.dumps(info, indent=2)+'\n').encode()
    path.write_bytes(raw)
    manifest_path = folder / 'comparison_manifest.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['metrics_sha256'] = hashlib.sha256(raw).hexdigest()
    manifest_path.write_text(json.dumps(manifest), encoding='utf-8')


def forbid_load(monkeypatch):
    monkeypatch.setattr(registry.joblib, 'load', lambda *args, **kwargs: pytest.fail('Must reject before unpickling'))


def test_existing_model_output_unchanged_and_additive_metadata(bundle, prepared):
    info = read_info(bundle)
    direct = joblib.load(BytesIO((bundle / info['model_file']).read_bytes()))
    row = make_training(*prepared[:3]).iloc[[0]][FEATURES]
    model, adapted = load_serving_model(bundle, data_version=info['provenance']['prepared_content_sha256'])
    np.testing.assert_allclose(model.predict(row), direct.predict(row), rtol=0, atol=0)
    assert adapted['run_id'] == info['run_id'] and adapted['comparison'] == info['comparison']
    assert adapted['compatibility_status'] == 'matched' and adapted['warehouse_batch_match'] is True
    assert adapted['metrics_scope'] == 'synthetic_historical_test'


def test_metadata_never_unpickles_and_unknown_legacy_batch_is_explicit(bundle, monkeypatch):
    forbid_load(monkeypatch)
    info = registry.load_metadata(bundle)
    assert info['artifact_integrity_verified'] and info['warehouse_batch_match'] is None
    assert info['compatibility_status'] == 'batch_unverified'


@pytest.mark.parametrize('kind', ['actual', 'empty', 'unknown', None])
def test_non_synthetic_source_refused_before_unpickle(bundle, monkeypatch, kind):
    forbid_load(monkeypatch)
    with pytest.raises(registry.RegistryError) as error:
        registry.load_model(bundle, source_kind=kind)
    assert error.value.code == 'SOURCE_RESTRICTED'


@pytest.mark.parametrize('version,code', [('0'*64, 'DATASET_MISMATCH'), ('invalid', 'DATASET_METADATA_INVALID'),
                                        (False, 'DATASET_METADATA_INVALID')])
def test_batch_mismatch_or_malformed_fingerprint_is_not_silently_accepted(bundle, monkeypatch, version, code):
    forbid_load(monkeypatch)
    with pytest.raises(registry.RegistryError) as error:
        registry.load_model(bundle, data_version=version)
    assert error.value.code == code


@pytest.mark.parametrize('name', ['comparison_metrics.json', 'linear_regression_synthetic.joblib'])
def test_tampering_refused_before_unpickle(bundle, monkeypatch, name):
    (bundle / name).write_bytes(b'tampered')
    forbid_load(monkeypatch)
    with pytest.raises(ModelUnavailable):
        load_serving_model(bundle)


@pytest.mark.parametrize('mutator', [
    lambda d: d.update(features=list(reversed(FEATURES))),
    lambda d: d.update(target='different_target'),
    lambda d: d.update(horizon_days=14),
    lambda d: d.update(history_days=14),
    lambda d: d.update(feature_schema_version='future-v2'),
    lambda d: d.update(is_synthetic=False),
    lambda d: d.update(source_kind='actual'),
    lambda d: d.update(target_approved=True),
    lambda d: d.update(run_id='different-run'),
    lambda d: d.update(model_file='another.joblib'),
    lambda d: d.update(feature_ranges={'age': {'min': 'bad', 'max': 100}}),
    lambda d: d['comparison'][0]['test'].update(rmse=float('nan')),
    lambda d: d.update(provenance=[]),
    lambda d: d.update(selection={}),
])
def test_valid_hash_does_not_bypass_contract_checks(bundle, monkeypatch, mutator):
    rehash_metrics(bundle, mutator)
    forbid_load(monkeypatch)
    with pytest.raises(registry.RegistryError):
        registry.load_model(bundle)


@pytest.mark.parametrize('name', ['../outside.joblib', '/outside.joblib', 'C:\\outside.joblib',
                                '..\\outside.joblib', 'sub/model.joblib'])
def test_manifest_path_traversal_refused(bundle, monkeypatch, name):
    path = bundle / 'comparison_manifest.json'
    manifest = json.loads(path.read_text())
    manifest['model_file'] = name
    path.write_text(json.dumps(manifest))
    forbid_load(monkeypatch)
    with pytest.raises(registry.RegistryError) as error:
        registry.load_model(bundle)
    assert error.value.code == 'MODEL_INCOMPATIBLE'


def test_crlf_metadata_is_compatible_but_binary_is_strict(bundle):
    for name in ['comparison_metrics.json', 'comparison_manifest.json']:
        path = bundle / name
        path.write_bytes(path.read_bytes().replace(b'\r\n', b'\n').replace(b'\n', b'\r\n'))
    assert registry.load_model(bundle)[1]['artifact_integrity_verified']


def test_verified_but_non_model_binary_is_rejected(bundle):
    info = read_info(bundle)
    path = bundle / info['model_file']
    joblib.dump({'not': 'an estimator'}, path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    rehash_metrics(bundle, lambda data: data.update(model_sha256=digest))
    manifest_path = bundle / 'comparison_manifest.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['model_sha256'] = digest
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ModelUnavailable):
        load_serving_model(bundle)


def test_missing_files_fail_closed(tmp_path):
    with pytest.raises(ModelUnavailable):
        load_serving_model(tmp_path / 'missing')


@pytest.fixture
def api(loaded, bundle, monkeypatch):
    monkeypatch.setenv('MODEL_DIR', str(bundle.parent))
    monkeypatch.setenv('RATE_LIMIT_PER_MINUTE', '10000')
    return loaded


def test_api_comparison_and_prediction_share_model_and_provenance(api):
    metadata = api.get('/api/model/comparison').json()
    response = api.get('/api/model/predict', params={'respondent_id': 'SIM001'})
    assert response.status_code == 200, response.text
    prediction = response.json()
    assert metadata['warehouse_batch_match'] is True and prediction['warehouse_batch_match'] is True
    assert metadata['run_id'] == prediction['model']['version']
    assert metadata['training_data_version'] == prediction['training_data_version']
    assert prediction['is_synthetic'] and not prediction['is_diagnosis']


@pytest.mark.parametrize('quality,expected', [
    (json.dumps({'prepared_content_sha256': '0'*64}), 'DATASET_MISMATCH'),
    (json.dumps({'prepared_content_sha256': 'bad'}), 'DATASET_METADATA_INVALID'),
    ('[]', 'DATASET_METADATA_INVALID'), ('broken-json', 'DATASET_METADATA_INVALID'),
])
def test_api_known_bad_batch_blocks_prediction_and_evaluation(api, warehouse_engine, quality, expected):
    with Session(warehouse_engine) as db:
        db.get(SourceState, 1).quality_json = quality
        db.commit()
    response = api.get('/api/model/predict', params={'respondent_id': 'SIM001'})
    assert response.status_code == 409 and response.json()['error_code'] == expected
    metadata = api.get('/api/model/comparison').json()
    assert metadata['available'] is False and metadata['error_code'] == expected
    assert 'prediction_mmHg' not in response.json()


def test_api_missing_legacy_fingerprint_is_warned_not_claimed_matched(api, warehouse_engine):
    with Session(warehouse_engine) as db:
        db.get(SourceState, 1).quality_json = '{}'
        db.commit()
    response = api.get('/api/model/predict', params={'respondent_id': 'SIM001'})
    assert response.status_code == 200
    data = response.json()
    assert data['warehouse_batch_match'] is None and data['compatibility_status'] == 'batch_unverified'
    assert any('Fingerprint batch' in note for note in data['notes'])


def test_actual_dataset_stays_restricted(api, warehouse_engine):
    with Session(warehouse_engine) as db:
        db.get(SourceState, 1).source_kind = 'actual'
        db.commit()
    assert api.get('/api/model/predict', params={'respondent_id': 'SIM001'}).status_code == 409
    assert api.get('/api/model/comparison').json()['available'] is False
    assert api.get('/api/analytics').status_code == 403
