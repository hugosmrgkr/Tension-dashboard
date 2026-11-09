"""Dashboard v1 serving extensions; reuse the isolated CP3 API fixtures."""
import math
import numpy as np
from sqlalchemy import select,func,update
from sqlalchemy.orm import Session
from test_cp3_stage1 import client,loaded
from app.models import Participant,DailyBehavior,BPSession


def test_demographics_count_people_once_and_follow_education_filter(loaded,warehouse_engine):
    data=loaded.get('/api/analytics').json()
    with Session(warehouse_engine) as db:
        total=db.scalar(select(func.count()).select_from(Participant))
        education=db.scalar(select(Participant.education).where(Participant.education.is_not(None)))
        expected=db.scalar(select(func.count()).select_from(Participant).where(Participant.education==education))
    for groups in data['demographics'].values():
        assert sum(row['n'] for row in groups)==total
    selected=loaded.get('/api/analytics',params={'education':education,'session':'Malam'}).json()
    assert len(selected['participants'])==expected
    assert all(row['education']==education for row in selected['participants'])
    assert sum(row['n'] for row in selected['demographics']['gender'])==expected
    csv=loaded.get('/api/data/export/participants',params={'education':education}).text
    assert len(csv.splitlines())==expected+1


def test_risk_categories_and_correlations_use_daily_grain(loaded,warehouse_engine):
    data=loaded.get('/api/analytics').json()
    for key in ['medication','smoked','sitting']:
        with Session(warehouse_engine) as db:
            expected=db.scalar(select(func.count()).select_from(DailyBehavior).where(getattr(DailyBehavior,key).is_not(None)))
        assert sum(row['n'] for row in data['categories'][key])==expected
        assert all(0<row['respondents']<=19 for row in data['categories'][key])
    assert all('smoke_count' in row and 'medication' in row for row in data['scatter'])
    result=next(row for row in data['correlations'] if row['field']=='smoke_count')
    with Session(warehouse_engine) as db:
        pairs=db.execute(select(DailyBehavior.smoke_count,func.avg(BPSession.sbp_mean))
            .join(BPSession,(DailyBehavior.participant_id==BPSession.participant_id)&(DailyBehavior.date_id==BPSession.date_id))
            .where(DailyBehavior.smoke_count.is_not(None),BPSession.sbp_mean.is_not(None),BPSession.dbp_mean.is_not(None))
            .group_by(DailyBehavior.id)).all()
    assert result['n']==len(pairs)==20
    assert math.isclose(result['r'],float(np.corrcoef(np.array(pairs,dtype=float).T)[0,1]),abs_tol=1e-8)
    morning=loaded.get('/api/analytics',params={'session':'Pagi'}).json()
    assert sum(row['n'] for row in morning['categories']['medication'])==570  # not doubled
    assert len(morning['scatter'])==570


def test_constant_numeric_field_and_empty_filters_do_not_invent_statistics(loaded,warehouse_engine):
    with Session(warehouse_engine) as db:
        db.execute(update(DailyBehavior).values(activity_minutes=0));db.commit()
    data=loaded.get('/api/analytics').json()
    result=next(row for row in data['correlations'] if row['field']=='activity_minutes')
    assert result['n']==570 and result['r'] is None
    empty=loaded.get('/api/analytics',params={'respondent_id':'UNKNOWN'}).json()
    assert all(rows==[] for rows in empty['demographics'].values())
    assert all(row['n']==0 and row['r'] is None for row in empty['correlations'])


def test_location_hierarchy_is_derived_from_profiles(loaded,warehouse_engine):
    meta=loaded.get('/api/meta').json()
    assert meta['education']
    with Session(warehouse_engine) as db:
        for province,cities in meta['cities_by_province'].items():
            expected=set(db.scalars(select(Participant.city).where(Participant.province==province,Participant.city.is_not(None))))
            assert set(cities)==expected


def test_empty_warehouse_demographics_and_associations_remain_empty(client):
    response=client.get('/api/analytics')
    assert response.status_code==200
    data=response.json()
    assert all(not groups for groups in data['demographics'].values())
    assert all(row['r'] is None and row['n']==0 for row in data['correlations'])
