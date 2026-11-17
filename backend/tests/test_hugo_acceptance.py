"""Acceptance: two CSVs -> isolated warehouse -> HTTP API -> verified model.

Uses existing disposable fixtures; never operates on an active warehouse.
"""
import csv
import io

import numpy as np
import pandas as pd
import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import security
from app.analytics_v2 import frames
from app.baseline import FEATURES, make_training
from app.models import BPSession, DailyBehavior, Participant, SourceState
from test_cp3_stage1 import client, loaded  # noqa: F401


def test_csv_warehouse_sql_kpi_and_filtered_export_agree(loaded, warehouse_engine, monkeypatch):
    with Session(warehouse_engine) as db:
        counts = [db.scalar(select(func.count()).select_from(model)) for model in (Participant, DailyBehavior, BPSession)]
        mean = db.scalar(select(func.avg(BPSession.sbp_mean)))
    assert counts == [19, 570, 1140]
    # Serving must use warehouse data, not reopen CSV fixtures as a fallback.
    monkeypatch.setattr(pd, 'read_csv', lambda *a, **k: pytest.fail('HTTP serving must not read CSV'))
    metadata = loaded.get('/api/meta').json()
    data = loaded.get('/api/analytics').json()
    assert [metadata[k] for k in ['participants', 'daily_records', 'session_records']] == counts
    assert data['kpis']['mean_sbp'] == pytest.approx(round(float(mean), 1))
    for session in ['Pagi', 'Malam']:
        q = dict(respondent_id='SIM001', start_date='2026-09-01', end_date='2026-09-03', session=session)
        scoped = loaded.get('/api/analytics', params=q).json()
        exported = loaded.get('/api/data/export/sessions', params=q)
        assert exported.status_code == 200
        rows = list(csv.DictReader(io.StringIO(exported.content.decode('utf-8-sig'))))
        assert len(rows) == scoped['kpis']['sessions'] == 3
        assert {r['respondent_id'] for r in rows} == {'SIM001'}
        assert {r['session'] for r in rows} == {session}


def test_every_historical_test_origin_matches_artifact_and_exact_training_features(loaded, prepared, warehouse_engine):
    expected_windows = make_training(*prepared[:3])
    with Session(warehouse_engine) as db:
        profiles, sessions, days = frames(db)
    warehouse_windows = make_training(profiles, days, sessions)
    keys = ['respondent_id', 'asof_date']
    pd.testing.assert_frame_equal(expected_windows.sort_values(keys).reset_index(drop=True),
                                  warehouse_windows.sort_values(keys).reset_index(drop=True), check_dtype=False)
    comparison = loaded.get('/api/model/comparison').json()
    assert comparison['available'] and comparison['warehouse_batch_match'] is True
    column = comparison['selected_model'].lower().replace(' ', '_').replace('-', '_')
    for example in comparison['actual_vs_predicted']:
        response = loaded.get('/api/model/predict', params={'respondent_id': example['respondent_id'], 'asof_date': example['date']})
        assert response.status_code == 200, response.text
        body = response.json()
        assert body['prediction_mmHg'] == pytest.approx(round(example[column], 2), abs=.005)
        assert body['model']['version'] == comparison['run_id']
        assert body['training_data_version'] == comparison['training_data_version']
        window = expected_windows[(expected_windows.respondent_id == example['respondent_id']) &
                                   (expected_windows.asof_date == example['date'])].iloc[0]
        np.testing.assert_allclose([body['features_used'][f] for f in FEATURES], window[FEATURES].to_numpy(dtype=float))
        assert len(body['history_daily']) == 7
        assert body['history_daily'][-1]['date'] == example['date']
        assert all(row['date'] < body['forecast_start'] for row in body['history_daily'])


@pytest.mark.parametrize('role', ['viewer', 'admin'])
def test_authenticated_real_pipeline_keeps_role_boundaries_and_actual_guard(loaded, warehouse_engine, monkeypatch, role):
    security.reset_state()
    tokens = {'viewer': 'acceptance-fixture-viewer', 'admin': 'acceptance-fixture-admin'}
    monkeypatch.setenv('AUTH_MODE', 'token')
    for name, token in tokens.items():
        monkeypatch.setenv(name.upper() + '_TOKEN_SHA256', security.sha256_hex(token))
    assert loaded.get('/api/meta').status_code == 401
    headers = {'Authorization': 'Bearer ' + tokens[role]}
    response = loaded.get('/api/model/predict', params={'respondent_id': 'SIM001'}, headers=headers)
    assert response.status_code == 200 and len(response.json()['history_daily']) == 7
    assert loaded.get('/api/data/export/sessions', headers=headers).status_code == (200 if role == 'admin' else 403)
    with Session(warehouse_engine) as db:
        db.get(SourceState, 1).source_kind = 'actual'
        db.commit()
    assert loaded.get('/api/analytics', headers=headers).status_code == 403
    blocked = loaded.get('/api/model/predict', params={'respondent_id': 'SIM001'}, headers=headers)
    assert blocked.status_code == 409
    assert 'history_daily' not in blocked.json() and 'prediction_mmHg' not in blocked.json()
    security.reset_state()
