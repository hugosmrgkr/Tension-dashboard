"""Reproductions and regression evidence for the final P0/P1 audit."""
import copy,json,shutil,subprocess
from pathlib import Path
import pandas as pd
from sqlalchemy import select,update
from sqlalchemy.orm import Session
from app.baseline import load_experiment,daily_bp
from app.pipeline import prepare
from app.models import BPSession,Participant,SourceState
from test_cp3_stage1 import client,loaded

ROOT=Path(__file__).resolve().parents[2]


def test_artifacts_survive_lf_and_crlf_checkout(tmp_path):
    for ending in [b'\n',b'\r\n']:
        folder=tmp_path/('lf' if ending==b'\n' else 'crlf');folder.mkdir()
        for source in (ROOT/'models').glob('baseline*.json'):
            folder.joinpath(source.name).write_bytes(source.read_bytes().replace(b'\r\n',b'\n').replace(b'\n',ending))
        shutil.copyfile(ROOT/'models/linear_regression_synthetic.joblib',folder/'linear_regression_synthetic.joblib')
        assert load_experiment(folder)['available'],f'Unavailable after checkout ending={ending!r}'


def test_cross_reading_components_are_pending_review(source_pair):
    source_pair[1].iloc[0,5]='';source_pair[1].iloc[0,6]=''
    p,d,s,q=prepare(*source_pair)
    assert s[0]['sbp1'] is not None and s[0]['dbp2'] is not None
    assert s[0]['sbp_mean'] is None and s[0]['dbp_mean'] is None
    assert q['valid_sessions']==1139
    row=daily_bp(s).iloc[0]
    assert row.sbp==s[1]['sbp_mean']  # only the other eligible session contributes


def test_contradictory_bp_is_retained_but_not_aggregated(source_pair):
    source_pair[1].iloc[0,4]='65';source_pair[1].iloc[0,5]='100'
    p,d,s,q=prepare(*source_pair)
    assert s[0]['sbp1']==65 and s[0]['dbp1']==100
    assert s[0]['sbp_mean'] is None and s[0]['dbp_mean'] is None


def test_conflicting_duplicate_does_not_choose_first_answer(source_pair):
    p,d=source_pair;duplicate=d.iloc[[0]].copy();duplicate.iloc[0,27]='5' if d.iloc[0,27]!='5' else '1'
    joined=pd.concat([d,duplicate],ignore_index=True)
    _,days,_,q=prepare(p,joined)
    assert len(days)==569 and q['rejected_daily']==2
    reverse=pd.concat([duplicate,d],ignore_index=True)
    assert len(prepare(p,reverse)[1])==569


def test_active_respondents_are_daily_ids_even_without_bp(loaded,warehouse_engine):
    with Session(warehouse_engine) as db:
        db.execute(update(BPSession).values(sbp1=None,sbp2=None,dbp1=None,dbp2=None,sbp_mean=None,dbp_mean=None));db.commit()
    data=loaded.get('/api/analytics').json()
    assert data['kpis']['respondents']==19
    assert data['kpis']['respondents_with_valid_bp']==0 and data['kpis']['mean_sbp'] is None
    assert data['empty'] is False and data['empty_reason']=='no_valid_sessions'


def test_private_paths_cannot_be_accidentally_added_to_git():
    paths=['data/actual/respondents.csv','data/private/export.xlsx','backend/.env.local','frontend/.env.production','credentials.json']
    for path in paths:
        assert subprocess.run(['git','check-ignore','--no-index','-q',path],cwd=ROOT).returncode==0,path


def test_public_metadata_does_not_disclose_actual_source_name(loaded,warehouse_engine):
    with Session(warehouse_engine) as db:
        state=db.get(SourceState,1);state.source_kind='actual';state.source_name='PRIVATE-NAME-SECRET.csv';db.commit()
    response=loaded.get('/api/meta');assert response.status_code==200
    assert 'PRIVATE-NAME-SECRET' not in response.text


def test_csv_formula_text_is_escaped(loaded,warehouse_engine):
    with Session(warehouse_engine) as db:
        row=db.scalar(select(Participant));rid=row.respondent_id;row.occupation='=HYPERLINK("https://example.invalid")';db.commit()
    response=loaded.get('/api/data/export/participants')
    frame=pd.read_csv(__import__('io').StringIO(response.text))
    assert frame.loc[frame.respondent_id==rid,'occupation'].iloc[0].startswith("'=" )


def test_api_rechecks_legacy_cross_readings_and_exposes_review(loaded,warehouse_engine):
    with Session(warehouse_engine) as db:
        row=db.scalar(select(BPSession));row.dbp1=None;row.sbp2=None
        # Deliberately leave the old derived means in the legacy warehouse.
        db.commit()
    data=loaded.get('/api/analytics').json()
    assert data['kpis']['sessions']==1139 and data['kpis']['respondents']==19
    assert data['filtered_quality']['pending_review_sessions']==1
    pending=[row for row in data['session_rows'] if row['review_status']=='pending_review']
    assert len(pending)==1 and pending[0]['sbp_mean'] is None and not pending[0]['is_valid']


def test_conflicting_profiles_do_not_choose_first_demographics(source_pair):
    p,d=source_pair;conflict=p.iloc[[0]].copy();conflict.iloc[0,3]='50' if p.iloc[0,3]!='50' else '40'
    profiles,days,_,quality=prepare(pd.concat([p,conflict],ignore_index=True),d)
    assert len(profiles)==18 and len(days)==540
    assert quality['rejected_profiles']==2 and quality['rejected_daily']==30


def test_model_bytes_and_metric_values_still_have_strict_integrity(tmp_path):
    for name in ['baseline_metrics.json','baseline_manifest.json','linear_regression_synthetic.joblib']:
        shutil.copyfile(ROOT/'models'/name,tmp_path/name)
    metrics=tmp_path/'baseline_metrics.json'
    original=metrics.read_bytes();metrics.write_bytes(original.replace(b'"rows_test": 7',b'"rows_test": 8'))
    assert not load_experiment(tmp_path)['available']
    metrics.write_bytes(original)
    model=tmp_path/'linear_regression_synthetic.joblib';model.write_bytes(model.read_bytes()+b'corruption')
    assert not load_experiment(tmp_path)['available']


def test_header_contract_accepts_whitespace_but_never_guesses_order(source_pair):
    from app.pipeline import DataQualityError
    import pytest
    p,d=source_pair;p.columns=['\ufeff '+str(name)+'  ' if i==0 else str(name).replace('\n','\r\n') for i,name in enumerate(p.columns)]
    assert len(prepare(p,d)[0])==19
    renamed=d.copy();names=list(renamed.columns);names[4],names[5]=names[5],names[4];renamed.columns=names
    with pytest.raises(DataQualityError):prepare(p,renamed)


def test_actual_quality_gate_blocks_unreviewed_issues(warehouse_engine,prepared):
    from app.etl_control import apply_validated
    from app.pipeline import DataQualityError
    import pytest
    with Session(warehouse_engine) as db:
        with pytest.raises(DataQualityError,match='pending review'):
            apply_validated(db,*prepared,kind='actual')


def test_extreme_and_suspicious_inputs_are_not_silently_used(source_pair):
    from app.pipeline import DataQualityError
    p,d=source_pair;d.iloc[0,4]='999';d.iloc[0,5]='999'
    _,days,sessions,q=prepare(p,d)
    assert sessions[0]['sbp_mean'] is None and q['invalid_bp_count']>=2
    d.iloc[0,2]='2005-08-29'
    _,days,_,q=prepare(p,d)
    assert len(days)==569 and q['rejected_daily']==1 and q['suspicious_dates']
