"""History comes from the exact seven daily observations used for inference."""
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.baseline import make_training
from app.model_service import inference_features
from app.models import SourceState
from test_cp3_stage1 import client, loaded  # noqa: F401


def test_history_matches_features_and_origin_without_future_rows(prepared):
    profiles, days, sessions, _ = prepared
    row = make_training(profiles, days, sessions).iloc[0]
    built = inference_features(profiles, days, sessions, row.respondent_id, row.asof_date)
    history = built['history_daily']
    dates = [r['date'] for r in history]
    assert dates == list(pd.date_range(row.history_start, row.asof_date).strftime('%Y-%m-%d'))
    assert len(history) == 7 and len(set(dates)) == 7
    assert max(dates) < row.target_start
    np.testing.assert_allclose(np.mean([r['sbp'] for r in history]), built['features']['past_7d_sbp'])
    np.testing.assert_allclose(np.mean([r['dbp'] for r in history]), built['features']['past_7d_dbp'])


def test_api_history_uses_selected_origin_and_same_id(loaded, prepared):
    row = make_training(*prepared[:3]).iloc[0]
    response = loaded.get('/api/model/predict', params={'respondent_id': row.respondent_id, 'asof_date': row.asof_date})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body['respondent_id'] == row.respondent_id and body['last_date'] == row.asof_date
    assert body['history_grain'] == 'respondent-date' and len(body['history_daily']) == 7
    assert body['history_daily'][0]['date'] == row.history_start
    assert body['history_daily'][-1]['date'] == row.asof_date
    assert body['forecast_start'] == row.target_start and body['forecast_end'] == row.target_end
    np.testing.assert_allclose(np.mean([r['sbp'] for r in body['history_daily']]), body['reference_naive_mmHg'], atol=.005)
    # One aggregate prediction; no seven-point fabricated forecast or predicted DBP.
    assert 'prediction_daily' not in body and 'predicted_dbp' not in body


def test_actual_source_does_not_expose_history(loaded, warehouse_engine):
    with Session(warehouse_engine) as db:
        db.get(SourceState, 1).source_kind = 'actual'
        db.commit()
    response = loaded.get('/api/model/predict', params={'respondent_id': 'SIM001'})
    assert response.status_code == 409 and 'history_daily' not in response.json()
