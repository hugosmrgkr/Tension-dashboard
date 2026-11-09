import os
from pathlib import Path
# Isolated SQLite database for the test suite. Must be set before importing app.db.
ROOT=Path(__file__).resolve().parents[2]
os.environ['DATABASE_URL']='sqlite:///'+str(ROOT/'test_tmp.db')
os.environ['SAMPLE_DATA_DIR']=str(ROOT/'data/sample')
os.environ['MODEL_DIR']=str(ROOT/'models')
os.environ['ENABLE_IMPORT']='false'
from fastapi.testclient import TestClient
from app.main import app
from app.pipeline import prepare, DataQualityError
import pandas as pd
import pytest

def test_01_api_seed_and_grain():
    with TestClient(app) as c:
        h=c.get('/health');assert h.status_code==200
        m=c.get('/api/meta');assert m.status_code==200
        data=m.json();assert data['participants']==19;assert data['daily_records']==570;assert data['session_records']==1140
        assert data['source_kind']=='synthetic'
        a=c.get('/api/analytics').json();assert a['kpis']['respondents']==19;assert a['kpis']['sessions']==1140
        assert a['kpis']['daily_records']==570
        assert len(a['session_rows'])==1140;assert len(a['daily_rows'])==570
        assert set(x['session'] for x in a['session_rows'])=={'Pagi','Malam'}
        assert all(1<=x['stress']<=5 for x in a['scatter'] if x['stress'] is not None)
        assert all(0<=x['sleep_hours']<=18 for x in a['scatter'] if x['sleep_hours'] is not None)

def test_02_filters_and_date_grain():
    with TestClient(app) as c:
        a=c.get('/api/analytics',params={'start_date':'2026-09-01','end_date':'2026-09-01'}).json()
        assert a['kpis']['daily_records']==19;assert a['kpis']['sessions']==38
        b=c.get('/api/analytics',params={'session':'Pagi'}).json()
        assert b['kpis']['sessions']==570;assert b['kpis']['daily_records']==570
        c2=c.get('/api/analytics',params={'respondent_id':'SIM001'}).json()
        assert c2['kpis']['respondents']==1;c3=c.get('/api/analytics',params={'province':'PROVINSI PALSU'}).json();assert c3['empty']

def test_03_baseline_metrics_are_real_and_split_by_id():
    with TestClient(app) as c:
        r=c.get('/api/model/baseline');assert r.status_code==200
        d=r.json();assert d['available'];assert d['rows_training']>0 and d['rows_test']>0
        assert not(set(d['respondents_train'])&set(d['respondents_test']))
        assert len(d['scores'])==2
        p=c.get('/api/model/predict-baseline?respondent_id=SIM001').json()
        assert p['is_synthetic'] and not p['is_diagnosis'] and p['prediction_mmHg']>60

def test_04_import_secure_by_default_and_export_anonymized():
    with TestClient(app) as c:
        p=c.get('/api/data/export/participants');assert p.status_code==200
        assert 'Nama lengkap' not in p.text and 'DATA SIMULASI 001' not in p.text
        d=c.post('/api/data/import-pair');assert d.status_code in (403,422)

def test_05_duplicate_id_date_is_quarantined_not_autofixed():
    p=pd.read_csv(ROOT/'data/sample/Data_Responden_Sintetis.csv',dtype=str,keep_default_na=False)
    d=pd.read_csv(ROOT/'data/sample/Data_Harian_Sintetis.csv',dtype=str,keep_default_na=False)
    d=pd.concat([d,d.iloc[[0]]],ignore_index=True)
    pp,dd,ss,q=prepare(p,d)
    assert len(dd)==570 and len(ss)==1140 and q['duplicate_pairs']==1 and q['rejected_daily']==1

@pytest.fixture(scope='session',autouse=True)
def cleanup_tmp_db():
    yield
    path=ROOT/'test_tmp.db'
    if path.exists():path.unlink()
