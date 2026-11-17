"""Read-only acceptance checks against an explicitly started local synthetic API.

Does not start servers, import data, train or change the warehouse. The URL must
be loopback; prepare a disposable environment before calling this verifier.
"""
import argparse
import csv
from datetime import datetime, timezone
import io
import json
import math
from pathlib import Path
from urllib.parse import urlencode, urlsplit
from urllib.request import urlopen


def verify(url, require_postgres=False):
    parsed = urlsplit(url)
    if parsed.scheme not in ('http', 'https') or parsed.hostname not in ('localhost', '127.0.0.1', '::1'):
        raise ValueError('Gunakan URL API pengujian loopback secara eksplisit.')
    if parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ('', '/'):
        raise ValueError('URL harus origin lokal tanpa kredensial, query atau path.')
    base = url.rstrip('/')
    def raw(path):
        with urlopen(base+path, timeout=30) as response:
            return response.read()
    def api(path):
        return json.loads(raw(path))
    health = api('/api/health')
    if require_postgres:
        assert health['database'] == 'postgresql'
    meta = api('/api/meta')
    assert meta['source_kind'] == 'synthetic' and not meta['access_restricted'] and not meta['warehouse_empty']
    assert [meta[k] for k in ('participants', 'daily_records', 'session_records')] == [19, 570, 1140]
    analytics = api('/api/analytics')
    model = api('/api/model/comparison')
    assert model['available'] and model['artifact_integrity_verified'] and model['warehouse_batch_match'] is True
    assert model['data_version'] == model['training_data_version'] == meta['data_version']
    assert model['metrics_scope'] == 'synthetic_historical_test' and model['target_approved'] is False
    assert len(model['actual_vs_predicted']) == model['rows_test'] == 7
    key = model['selected_model'].lower().replace(' ', '_').replace('-', '_')
    predictions = []
    for row in model['actual_vs_predicted']:
        body = api('/api/model/predict?'+urlencode({'respondent_id': row['respondent_id'], 'asof_date': row['date']}))
        assert body['model']['version'] == model['run_id']
        assert body['source_kind'] == 'synthetic' and not body['is_diagnosis']
        assert body['prediction_mmHg'] == round(row[key], 2)
        assert body['data_version'] == meta['data_version']
        history = body['history_daily']
        assert len(history) == 7 and len({day['date'] for day in history}) == 7
        assert history[-1]['date'] == body['last_date'] == row['date']
        assert all(body['history_start'] <= day['date'] < body['forecast_start'] for day in history)
        assert math.isclose(sum(day['sbp'] for day in history)/7, body['features_used']['past_7d_sbp'], abs_tol=1e-10)
        assert math.isclose(body['reference_naive_mmHg'], body['features_used']['past_7d_sbp'], abs_tol=.005001)
        predictions.append(body)
    for session in ('Pagi', 'Malam'):
        query = urlencode(dict(respondent_id='SIM001', session=session, start_date='2026-09-01', end_date='2026-09-03'))
        filtered = api('/api/analytics?'+query)
        rows = list(csv.DictReader(io.StringIO(raw('/api/data/export/sessions?'+query).decode('utf-8-sig'))))
        assert len(rows) == filtered['kpis']['sessions'] == filtered['kpis']['daily_records'] == 3
        assert {row['session'] for row in rows} == {session}
    empty = api('/api/analytics?start_date=2030-01-01&end_date=2030-01-07')
    assert empty['empty'] and empty['trend'] == [] and empty['kpis']['mean_sbp'] is None
    return dict(verified_at=datetime.now(timezone.utc).isoformat(), url=base, database=health['database'],
                source_kind='synthetic', counts=dict(profiles=19, daily=570, sessions=1140), kpis=analytics['kpis'],
                data_version=meta['data_version'], model_run_id=model['run_id'], historical_test=True,
                checks=dict(artifact_integrity=True, source_and_batch_match=True, all_seven_historical_predictions=True,
                            history_matches_inference_features=True, no_future_rows_in_history=True,
                            filters_and_csv_same_scope=True, empty_without_fake_values=True),
                forecasts=predictions)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', required=True)
    parser.add_argument('--require-postgres', action='store_true')
    parser.add_argument('--output', default='reports/hugo_stage4/http-verification.json')
    args = parser.parse_args()
    result = verify(args.url, args.require_postgres)
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False)+'\n', encoding='utf-8')
    print(json.dumps(result['checks'], indent=2))


if __name__ == '__main__':
    main()
