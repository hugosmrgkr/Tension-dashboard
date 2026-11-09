import copy
import io
from datetime import date
from pathlib import Path
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, func
from sqlalchemy.orm import Session, sessionmaker
from app import main
from app.db import get_db
from app.models import Participant, BPSession, DailyBehavior, CalendarDate, SessionType, SourceState
from app.pipeline import load_warehouse, DataQualityError
from app.analytics_v2 import records
from app.etl_control import apply_validated
from app.warehouse_audit import audit_warehouse


@pytest.fixture
def client(warehouse_engine,monkeypatch):
    sessions=sessionmaker(bind=warehouse_engine,expire_on_commit=False)
    monkeypatch.setattr(main,'engine',warehouse_engine)
    monkeypatch.setenv('MODEL_DIR',str(Path(__file__).resolve().parents[2]/'models'))
    def database():
        with sessions() as db: yield db
    main.app.dependency_overrides[get_db]=database
    try:
        with TestClient(main.app) as c: yield c
    finally:
        main.app.dependency_overrides.pop(get_db,None)


@pytest.fixture
def loaded(client,prepared,warehouse_engine):
    with Session(warehouse_engine) as db: load_warehouse(db,*prepared)
    return client


def test_empty_database_has_no_seed_or_fallback(client,warehouse_engine,monkeypatch):
    monkeypatch.setattr(pd,'read_csv',lambda *a,**k:pytest.fail('Serving must not read CSV'))
    metadata=client.get('/api/meta').json()
    assert metadata['warehouse_empty'] and metadata['respondent_ids']==[]
    assert metadata['participants']==metadata['daily_records']==metadata['session_records']==0
    response=client.get('/api/analytics')
    assert response.status_code==200,response.text
    data=response.json()
    assert data['empty_reason']=='warehouse_empty' and data['message']
    assert data['kpis']['mean_sbp'] is None and data['trend']==[]
    assert data['participants']==data['session_rows']==data['daily_rows']==[]
    exported=client.get('/api/data/export/sessions')
    assert exported.status_code==200 and exported.text.lstrip('\ufeff').startswith('respondent_id,')
    assert len(exported.text.splitlines())==1
    with Session(warehouse_engine) as db:
        assert not any(audit_warehouse(db)['counts'].values())


def test_cp2_results_are_visible_in_api_and_match_sql(loaded,warehouse_engine):
    meta=loaded.get('/api/meta').json();data=loaded.get('/api/analytics').json()
    assert meta['etl_audit_version']=='cp2-1' and meta['data_version']
    assert (meta['participants'],meta['daily_records'],meta['session_records'])==(19,570,1140)
    assert all(row['active_days_week'] is not None for row in data['participants'])
    assert data['filtered_quality']['missing_sleep_hours']==6
    assert data['filtered_quality']['missing_sitting']==3
    assert data['filtered_quality']['missing_smoke_count']==550
    assert len(data['scatter'])==570 and sum(r['n'] for r in data['trend'])==1140
    with Session(warehouse_engine) as db:
        count,mean=db.execute(select(func.count(),func.avg(BPSession.sbp_mean)).where(BPSession.sbp_mean.is_not(None),BPSession.dbp_mean.is_not(None))).one()
    assert data['kpis']['sessions']==count and data['kpis']['mean_sbp']==round(mean,1)


@pytest.mark.parametrize('params,day_count,session_count',[
    ({'start_date':'2026-09-01','end_date':'2026-09-01'},19,38),
    ({'session':'Pagi'},570,570),({'session':'Malam'},570,570),
    ({'respondent_id':'SIM001'},30,60),
    ({'respondent_id':'SIM001','session':'Pagi','start_date':'2026-09-01','end_date':'2026-09-03'},3,3),
])
def test_filter_contract_kpi_rows_quality_and_export(loaded,params,day_count,session_count):
    data=loaded.get('/api/analytics',params=params).json()
    assert data['kpis']['daily_records']==len(data['daily_rows'])==day_count
    assert data['kpis']['sessions']==len(data['session_rows'])==session_count
    assert data['filtered_quality']['session_records']==session_count
    for kind,key in [('sessions','session_rows'),('daily','daily_rows'),('participants','participants')]:
        response=loaded.get('/api/data/export/'+kind,params=params)
        assert response.status_code==200,response.text
        table=pd.read_csv(io.BytesIO(response.content))
        assert len(table)==len(data[key])
        assert set(table.respondent_id)=={r['respondent_id'] for r in data[key]}
        if 'session' in params and kind=='sessions': assert set(table.session)=={params['session']}


def test_profile_filters_match_warehouse(loaded,warehouse_engine):
    with Session(warehouse_engine) as db:
        profile=db.scalar(select(Participant).order_by(Participant.id))
        for key in ['province','city','gender','occupation']:
            value=getattr(profile,key)
            expected=db.scalar(select(func.count()).select_from(BPSession).join(Participant).where(getattr(Participant,key)==value))
            data=loaded.get('/api/analytics',params={key:value}).json()
            assert data['kpis']['sessions']==expected
            assert all(r[key]==value for r in data['participants'])


def test_no_measurements_under_filter_means_no_fake_graphs(loaded):
    data=loaded.get('/api/analytics',params={'start_date':'2026-10-01','end_date':'2026-10-02'}).json()
    assert data['empty_reason']=='filters_empty'
    assert data['participants']==data['session_rows']==data['daily_rows']==data['trend']==[]
    assert data['kpis']['mean_sbp'] is None


@pytest.mark.parametrize('params',[{'start_date':'bad'},{'start_date':'2026-09-30','end_date':'2026-09-01'},
                                   {'session':'Other'},{'age_group':'Undefined'}])
def test_invalid_filters_rejected(loaded,params):
    assert loaded.get('/api/analytics',params=params).status_code==422


def test_incomplete_sessions_and_scoped_missing_stay_null(loaded,warehouse_engine):
    with Session(warehouse_engine) as db:
        row=db.scalar(select(BPSession).order_by(BPSession.id))
        rid=db.get(Participant,row.participant_id).respondent_id
        day=db.get(CalendarDate,row.date_id).date.isoformat()
        row.sbp1=row.sbp2=row.sbp_mean=None;row.valid_sbp_count=0
        behavior=db.scalar(select(DailyBehavior).where(DailyBehavior.participant_id==row.participant_id,DailyBehavior.date_id==row.date_id))
        behavior.sleep_hours=None;db.commit()
    data=loaded.get('/api/analytics',params={'respondent_id':rid,'start_date':day,'end_date':day}).json()
    assert len(data['session_rows'])==2 and data['kpis']['sessions']==1
    invalid=[row for row in data['session_rows'] if not row['is_valid']]
    assert len(invalid)==1 and invalid[0]['sbp_mean'] is None and invalid[0]['sbp1'] is None
    assert data['filtered_quality']['missing_sleep_hours']==1
    assert data['filtered_quality']['incomplete_sessions']==1
    assert data['quality']['missing_sleep']==6  # explicitly labelled whole-batch snapshot
    assert sum(row['n'] for row in data['trend'])==1


def test_database_updates_are_read_dynamically_and_id_is_exact(loaded,warehouse_engine,prepared):
    with Session(warehouse_engine) as db:
        profile=Participant(**{**prepared[0][0],'respondent_id':'SIM0010'})
        db.add(profile);db.flush()
        existing=db.scalar(select(BPSession).order_by(BPSession.id))
        db.add(DailyBehavior(participant_id=profile.id,date_id=existing.date_id,stress=3))
        db.add(BPSession(participant_id=profile.id,date_id=existing.date_id,session_id=existing.session_id,
                         sbp1=150,dbp1=90,sbp2=150,dbp2=90,sbp_mean=150,dbp_mean=90,valid_sbp_count=2,valid_dbp_count=2))
        db.commit()
    all_data=loaded.get('/api/analytics').json()
    assert all_data['kpis']['respondents']==20 and all_data['kpis']['sessions']==1141
    assert loaded.get('/api/meta').json()['daily_records']==571
    one=loaded.get('/api/analytics',params={'respondent_id':'SIM001'}).json()
    assert one['kpis']['sessions']==60 and {p['respondent_id'] for p in one['participants']}=={'SIM001'}


def test_actual_source_is_protected_with_same_serving_contract(loaded,warehouse_engine):
    with Session(warehouse_engine) as db:
        db.get(SourceState,1).source_kind='actual';db.commit()
    meta=loaded.get('/api/meta').json()
    assert meta['access_restricted'] and meta['participants'] is None
    assert meta['respondent_ids']==meta['province']==[]
    for path in ['/api/analytics','/api/quality','/api/data/export/sessions']:
        assert loaded.get(path).status_code==403


def test_website_has_no_write_endpoints(loaded):
    for path in ['/api/data/import-pair','/api/data/reset','/api/measurements']:
        assert loaded.post(path).status_code in (404,405)
    schema=loaded.get('/api/openapi.json').json()
    assert all('post' not in route and 'put' not in route and 'delete' not in route for route in schema['paths'].values())


def test_exports_are_not_silently_limited_to_5000():
    assert len(records(pd.DataFrame({'value':range(6000)})))==6000


def test_manual_promotion_requires_current_hash_and_source_confirmation(warehouse_engine,prepared):
    p,d,s,q=copy.deepcopy(prepared)
    with Session(warehouse_engine) as db:
        first=apply_validated(db,p,d,s,q,kind='synthetic')
        for options in [{},{'expected_current_hash':'wrong'}]:
            with pytest.raises(DataQualityError): apply_validated(db,p,d,s,q,kind='synthetic',**options)
            assert audit_warehouse(db)['natural_content_sha256']==first['natural_content_sha256']
        with pytest.raises(DataQualityError):
            apply_validated(db,p,d,s,q,kind='actual',expected_current_hash=first['natural_content_sha256'])
        second=apply_validated(db,p,d,s,q,kind='synthetic',expected_current_hash=first['natural_content_sha256'])
        assert second['natural_content_sha256']==first['natural_content_sha256']
