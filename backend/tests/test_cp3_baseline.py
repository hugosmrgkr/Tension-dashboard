import copy
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import mean_absolute_error,mean_squared_error,r2_score
from app.baseline import (FEATURES,make_training,partitions,fit_model,leakage_audit,
                          run_experiment,load_experiment,predict_naive)
from test_cp3_stage1 import client,loaded
from app import main


def test_complete_windows_and_strict_id_time_partition(prepared):
    frame=make_training(*prepared[:3]);parts=partitions(frame)
    assert len(frame)==323 and len(parts['train'])==60 and len(parts['test'])==7
    assert parts['cutoff']=='2026-09-18'
    audit=leakage_audit(parts['train'],parts['test'],fit_model(parts['train']))
    assert not audit['subject_overlap'] and audit['shared_measurement_id_dates']==0
    assert audit['labels_available_before_test'] and audit['test_overlapping_target_id_days']==0
    assert audit['training_overlapping_target_id_days']>0  # honest dependence within train


def test_future_measurements_and_behaviors_never_enter_features(prepared):
    p,d,s,_=copy.deepcopy(prepared);original=make_training(p,d,s)
    origin='2026-09-10';rid=original.respondent_id.iloc[0]
    for row in s:
        if row['respondent_id']==rid and str(row['date'])>origin:
            row['sbp_mean']+=25;row['dbp_mean']+=10
    for row in d:
        if row['respondent_id']==rid and str(row['date'])>origin:
            row['activity_minutes']=1000;row['sleep_hours']=20;row['stress']=5
    changed=make_training(p,d,s)
    a=original[(original.respondent_id==rid)&(original.asof_date==origin)].iloc[0]
    b=changed[(changed.respondent_id==rid)&(changed.asof_date==origin)].iloc[0]
    np.testing.assert_allclose(a[FEATURES].to_numpy(dtype=float),b[FEATURES].to_numpy(dtype=float),equal_nan=True)
    assert b.target==pytest.approx(a.target+25)


def test_post_cutoff_values_do_not_change_fitted_model(prepared):
    p,d,s,_=copy.deepcopy(prepared)
    before=partitions(make_training(p,d,s));model=fit_model(before['train'])
    for row in s:
        if str(row['date'])>before['cutoff']:row['sbp_mean']+=100
    after=partitions(make_training(p,d,s));other=fit_model(after['train'])
    np.testing.assert_allclose(model.named_steps['regressor'].coef_,other.named_steps['regressor'].coef_)
    assert before['test'].target.mean()!=after['test'].target.mean()


def test_missing_calendar_day_or_sbp_excludes_window(prepared):
    p,d,s,_=copy.deepcopy(prepared);rid=p[0]['respondent_id']
    for row in s:
        if row['respondent_id']==rid and str(row['date'])=='2026-09-10':row['sbp_mean']=None
    frame=make_training(p,d,s)
    assert not any((frame.respondent_id==rid)&(frame.history_start<='2026-09-10')&(frame.target_end>='2026-09-10'))
    sessions=[row for row in prepared[2] if not(row['respondent_id']==rid and str(row['date'])=='2026-09-10')]
    assert len(make_training(p,d,sessions))==len(frame)


def test_empty_training_feature_is_imputed_from_train_only(prepared):
    parts=partitions(make_training(*prepared[:3]));training=parts['train'].copy();training['past_7d_sleep']=np.nan
    model=fit_model(training);audit=leakage_audit(training,parts['test'],model)
    assert audit['imputer_matches_training_only'] and audit['scaler_matches_training_only']
    assert model.predict(parts['test'][FEATURES]).shape==(7,)


def test_artifacts_metrics_and_reload_are_reproducible(tmp_path):
    root=Path(__file__).resolve().parents[2];pair=[root/'data/sample'/name for name in ['Data_Responden_Sintetis.csv','Data_Harian_Sintetis.csv']]
    result=run_experiment(*pair,tmp_path/'model',tmp_path/'evidence')
    predictions=pd.read_csv(tmp_path/'evidence/primary_predictions.csv');test=pd.read_csv(tmp_path/'evidence/test_windows.csv')
    model=joblib.load(tmp_path/'model/linear_regression_synthetic.joblib')
    np.testing.assert_allclose(model.predict(test[FEATURES]),predictions.linear,atol=1e-10)
    for score,key in zip(result['scores'],['naive','linear']):
        assert score['mae']==pytest.approx(mean_absolute_error(predictions.actual,predictions[key]))
        assert score['rmse']==pytest.approx(np.sqrt(mean_squared_error(predictions.actual,predictions[key])))
        assert score['r2']==pytest.approx(r2_score(predictions.actual,predictions[key]))
    repeated=run_experiment(*pair,tmp_path/'second')
    np.testing.assert_allclose([x['mae'] for x in result['scores']],[x['mae'] for x in repeated['scores']],atol=1e-12)
    assert result['run_id']==repeated['run_id'] and load_experiment(tmp_path/'model')['available']
    (tmp_path/'model/baseline_metrics.json').write_text('{}',encoding='utf-8')
    assert not load_experiment(tmp_path/'model')['available']


def test_api_origin_prediction_matches_experiment_history(loaded,prepared):
    origin='2026-09-18';rid='SIM001'
    result=loaded.get('/api/model/predict-baseline',params={'respondent_id':rid,'asof_date':origin})
    assert result.status_code==200,result.text
    prediction=result.json();training=make_training(*prepared[:3]);row=training[(training.respondent_id==rid)&(training.asof_date==origin)].iloc[0]
    assert prediction['prediction_mmHg']==round(row.past_7d_sbp,2)
    assert prediction['forecast_start']=='2026-09-19' and prediction['forecast_end']=='2026-09-25'
    assert not prediction['target_approved'] and prediction['artifact_run_id']
    assert loaded.get('/api/model/predict-baseline?respondent_id=SIM001&asof_date=2027-01-01').status_code==422


def test_api_rejects_corrupt_or_missing_artifacts_without_dummy_metrics(loaded,tmp_path,monkeypatch):
    monkeypatch.setenv('MODEL_DIR',str(tmp_path))
    (tmp_path/'baseline_metrics.json').write_text('{bad json',encoding='utf-8')
    metadata=loaded.get('/api/model/baseline').json()
    assert metadata['available'] is False and 'scores' not in metadata
    assert loaded.get('/api/model/predict-baseline?respondent_id=SIM001').status_code==409
