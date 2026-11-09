import copy
import json
import os
import subprocess
import sys
from pathlib import Path
import pandas as pd
import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.pipeline import prepare, load_warehouse, DataQualityError
from app.models import Participant, DailyBehavior, BPSession
from app.survey_schema import PROFILE_FIELDS, DAILY_FIELDS
from app.warehouse_audit import audit_warehouse


def test_contract_counts_units_and_no_source_mutation(source_pair):
    original=tuple(frame.copy(deep=True) for frame in source_pair)
    p,d,s,q=prepare(*source_pair)
    assert len(PROFILE_FIELDS)==24 and len(DAILY_FIELDS)==28
    assert (len(p),len(d),len(s))==(19,570,1140)
    assert all(isinstance(row['age'],int) and 0<=row['active_days_week']<=7 for row in p)
    assert all(row['active_days_week'] is not None for row in p)
    assert all(row['bmi']==round(row['weight_kg']/(row['height_cm']/100)**2,3) for row in p)
    assert len(q['before'])==len(q['after'])==52
    for a,b in zip(source_pair,original): pd.testing.assert_frame_equal(a,b)


def test_missing_categories_and_identity(prepared,source_pair):
    p,d,s,q=prepared
    assert sum(row['sleep_hours'] is None for row in d)==6
    assert sum(row['sitting'] is None for row in d)==3
    assert sum(row['smoke_count'] is None for row in d)==550
    assert not any('�' in (row['sitting'] or '') for row in d)
    source_pair[0].iloc[0,2]='PRIVATE PERSON MUST NOT LEAK'
    outputs=prepare(*source_pair)
    assert 'PRIVATE PERSON MUST NOT LEAK' not in json.dumps(outputs,default=str)


@pytest.mark.parametrize('dataset,column,value,field',[
    (0,23,'3.5 hari','active_days_week'),(0,20,'165 kg','height_cm'),
    (1,16,'45 kg','activity_minutes'),(1,16,'0.5','activity_minutes'),
    (1,27,'5.9','stress'),(1,27,'5 arbitrary text','stress'),
    (1,24,'Unknown smoking category','smoked'),(1,3,'25:72','morning_time'),
    (1,19,'0.25','sleep_hours'),
])
def test_invalid_nonkey_cells_are_null_and_reported(source_pair,dataset,column,value,field):
    source_pair[dataset].iloc[0,column]=value
    p,d,s,q=prepare(*source_pair)
    assert (len(p),len(d),len(s))==(19,570,1140)
    assert any(issue['field']==field and issue['row']==2 for issue in q['issues'])
    target=p[0] if dataset==0 else s[0] if field=='morning_time' else d[0]
    assert target['measured_at' if field=='morning_time' else field] is None


def test_normalize_case_units_and_decimal_separator(source_pair):
    source_pair[0].iloc[0,4]=' perempuan '
    source_pair[0].iloc[0,3]='55 tahun'
    source_pair[0].iloc[0,21]='60,7 kg'
    source_pair[1].iloc[0,16]='45 menit'
    p,d,s,q=prepare(*source_pair)
    assert p[0]['gender']=='Perempuan' and p[0]['age']==55 and p[0]['weight_kg']==60.7
    assert d[0]['activity_minutes']==45


def test_actual_sleep_is_not_inferred(source_pair):
    source_pair[1].iloc[0,18]='4\ufffd7 jam'
    p,d,s,q=prepare(*source_pair,synthetic=False)
    assert all(row['sleep_hours'] is None for row in d)
    assert q['issue_counts']['sleep_semantics_unconfirmed']==564
    assert q['issue_counts']['invalid_category']>0  # damaged sitting labels are fixture-only mappings
    assert prepare(*source_pair,synthetic=True)[1][0]['sitting']=='4\u20137 jam'


def test_duplicate_keys_and_unmatched_ids_are_quarantined(source_pair):
    p,d=source_pair
    p=pd.concat([p,p.iloc[[0]]],ignore_index=True)
    d=pd.concat([d,d.iloc[[0]]],ignore_index=True)
    p2,d2,s,q=prepare(p,d)
    assert (len(p2),len(d2),len(s))==(19,570,1140)
    assert q['raw_profiles']==20 and q['rejected_profiles']==1
    assert q['raw_daily']==571 and q['rejected_daily']==1
    assert q['uniqueness']['profile_duplicate_excess']==q['uniqueness']['daily_duplicate_excess']==1
    d.iloc[0,1]='MISSING-PROFILE'
    _,days,_,q=prepare(p,d)
    assert len(days)==570  # appended copy now replaces the quarantined original observation
    assert q['consistency']['unmatched_daily_rows']==1


@pytest.mark.parametrize('column,value',[(1,''),(2,'2026-02-30'),(2,'not-a-date')])
def test_invalid_daily_keys_are_not_loaded(source_pair,column,value):
    source_pair[1].iloc[0,column]=value
    _,d,s,q=prepare(*source_pair)
    assert len(d)==569 and len(s)==1138 and q['rejected_daily']==1


def test_schema_mismatch(source_pair):
    p,d=source_pair
    columns=list(d.columns);columns[4],columns[5]=columns[5],columns[4]
    with pytest.raises(DataQualityError): prepare(p,d[columns])
    with pytest.raises(DataQualityError): prepare(p.iloc[:,:-1],d)


def test_pressure_readings_mean_counts_and_anomalies(source_pair):
    source_pair[1].iloc[0,4]='invalid'
    p,d,s,q=prepare(*source_pair)
    assert s[0]['sbp1'] is None and s[0]['sbp_mean'] is None  # partial paired reading requires review
    assert s[0]['valid_sbp_count']==1 and q['invalid_bp_count']==1
    source_pair[1].iloc[0,6]='invalid'
    _,_,s,q=prepare(*source_pair)
    assert s[0]['sbp_mean'] is None and s[0]['valid_sbp_count']==0 and q['valid_sessions']==1139
    source_pair[1].iloc[0,4]='250';source_pair[1].iloc[0,6]='250'
    _,_,s,q=prepare(*source_pair)
    assert s[0]['sbp_mean']==250 and len(s)==1140
    assert any(flag['session_index']==1 for flag in q['pressure_anomalies']['flags'])
    assert q['pressure_anomalies']['removed_sessions']==0


def test_inverted_pressure_is_flagged_not_deleted(source_pair):
    source_pair[1].iloc[0,4]='65';source_pair[1].iloc[0,5]='100'
    _,_,s,q=prepare(*source_pair)
    assert s[0]['sbp1']==65 and s[0]['dbp1']==100
    assert q['issue_counts']['sbp_not_above_dbp']>=1


def test_cli_dry_run_never_connects_and_modes_are_exclusive():
    root=Path(__file__).resolve().parents[2]
    environment={**os.environ,'DATABASE_URL':'postgresql+psycopg://nobody@127.0.0.1:1/no_database',
                 'PYTHONDONTWRITEBYTECODE':'1'}
    command=[sys.executable,'-m','etl.import_data','--synthetic','--dry-run','--summary']
    result=subprocess.run(command,cwd=root,env=environment,capture_output=True,text=True,encoding='utf-8')
    assert result.returncode==0 and 'DRY RUN: no database changes' in result.stdout
    rejected=subprocess.run(command+['--commit'],cwd=root,env=environment,capture_output=True,text=True,encoding='utf-8')
    assert rejected.returncode==2


def test_warehouse_keys_counts_idempotency_and_atomicity(warehouse_engine,prepared):
    p,d,s,q=prepared
    with Session(warehouse_engine) as db:
        db.execute(text('CREATE TABLE cp2_legacy_sentinel (value INTEGER)'))
        db.execute(text('INSERT INTO cp2_legacy_sentinel VALUES (7)'));db.commit()
        load_warehouse(db,p,d,s,q)
        first=audit_warehouse(db)
        assert first['counts']==dict(dim_participant_v2=19,dim_date_v2=30,dim_session_v2=2,
                                     fact_bp_session_v2=1140,fact_daily_behavior_v2=570,dataset_state_v2=1)
        assert first['missing_active_days_week']==0 and not any(first['orphans'].values())
        assert all(value['pk']==['id'] for value in first['keys'].values())
        assert len(first['keys']['fact_bp_session_v2']['foreign_keys'])==3
        load_warehouse(db,p,d,s,q)
        second=audit_warehouse(db)
        assert first['natural_content_sha256']==second['natural_content_sha256']
        assert first['counts']==second['counts']
        assert db.scalar(text('SELECT value FROM cp2_legacy_sentinel'))==7
        malformed=copy.deepcopy(s);malformed[0]['respondent_id']='NOT-IN-PROFILE'
        with pytest.raises(KeyError):load_warehouse(db,p,d,malformed,q)
        assert audit_warehouse(db)['natural_content_sha256']==first['natural_content_sha256']
        day=db.scalar(select(DailyBehavior))
        db.add(DailyBehavior(participant_id=day.participant_id,date_id=day.date_id))
        with pytest.raises(IntegrityError):db.commit()
        db.rollback()
        db.add(BPSession(participant_id=999999,date_id=day.date_id,session_id=999999))
        with pytest.raises(IntegrityError):db.commit()
        db.rollback()
        db.execute(text('DROP TABLE cp2_legacy_sentinel'));db.commit()
