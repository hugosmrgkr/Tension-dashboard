"""Read-only HTTP smoke checks for the isolated synthetic CP3 demo."""
import argparse,csv,io,json
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import urlencode
from datetime import datetime,timezone


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url',default='http://127.0.0.1:8080')
    parser.add_argument('--output',default='reports/cp3_main_consolidation/http-verification.json')
    args=parser.parse_args()
    def raw(path):
        with urlopen(args.url+path,timeout=30) as response:return response.read()
    def api(path):return json.loads(raw(path))
    assert api('/health')['database']=='postgresql'
    assert b'root' in raw('/')
    meta=api('/api/meta');data=api('/api/analytics');model=api('/api/model/baseline')
    assert (meta['participants'],meta['daily_records'],meta['session_records'])==(19,570,1140)
    assert model['available'] and model['artifact_integrity_verified'] and model['warehouse_batch_match']
    assert not model['target_approved'] and model['rows_test']==7
    local=json.loads(Path('models/baseline_metrics.json').read_text(encoding='utf-8'))
    assert model['scores']==local['scores'] and model['run_id']==local['run_id']
    assert all(row['active_days_week'] is not None for row in data['participants'])
    for session in ['Pagi','Malam']:
        params=dict(session=session,respondent_id='SIM001',start_date='2026-09-01',end_date='2026-09-03')
        query=urlencode(params);selected=api('/api/analytics?'+query)
        assert selected['kpis']['sessions']==3 and len(selected['daily_rows'])==3
        rows=list(csv.DictReader(io.StringIO(raw('/api/data/export/sessions?'+query).decode('utf-8-sig'))))
        assert len(rows)==3 and {row['session'] for row in rows}=={session}
    forecasts=[]
    for row in model['actual_vs_predicted']:
        forecast=api('/api/model/predict-baseline?'+urlencode(dict(respondent_id=row['respondent_id'],asof_date=row['date'])))
        assert forecast['prediction_mmHg']==round(row['naive'],2)
        forecasts.append(forecast)
    assert data['filtered_quality']['missing_sleep_hours']==6
    assert data['filtered_quality']['missing_smoke_count']==550
    empty=api('/api/analytics?start_date=2027-01-01&end_date=2027-01-02')
    assert empty['empty'] and empty['trend']==[] and empty['kpis']['mean_sbp'] is None
    report=dict(verified_at_utc=datetime.now(timezone.utc).isoformat(),url=args.url,postgresql=True,
        counts=dict(profiles=19,daily=570,sessions=1140),kpis=data['kpis'],filtered_quality=data['filtered_quality'],
        model_run_id=model['run_id'],artifact_integrity_verified=True,warehouse_batch_match=True,scores=model['scores'],
        checks=dict(nginx_spa=True,filters_and_exports=True,all_heldout_naive_predictions_match_artifact=True,empty_filter=True,cp2_weekly_activity_present=True),
        forecasts=forecasts)
    output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report['checks'],indent=2))

if __name__=='__main__':main()
