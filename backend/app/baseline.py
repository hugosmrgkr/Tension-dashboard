"""CP3 synthetic experiment. Target proposal unchanged; no clinical validity.

Forecast origin is END of day t. History t-6..t, target t+1..t+7.
Primary evaluation holds out IDs AND time, and spaces test targets by 7 days.
"""
import hashlib
import json
import platform
from datetime import date,datetime,timezone
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.model_selection import GroupShuffleSplit
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error,mean_squared_error,r2_score
from .pipeline import prepare

FEATURES=['past_7d_sbp','past_7d_dbp','past_7d_sbp_std','age','bmi','past_7d_activity','past_7d_sleep','past_7d_stress']
WINDOW_FIELDS=['respondent_id','asof_date','history_start','target_start','target_end',*FEATURES,'target']
TARGET='future_7d_mean_sbp'
CONFIG=dict(seed=42,heldout_id_fraction=.32,calendar_train_fraction=.60,test_target_stride_days=7)

def sha256(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def text_sha256(path):
    """Hash UTF-8 bytes with physical CRLF normalized to LF; content stays protected."""
    raw=Path(path).read_bytes();raw.decode('utf-8')
    return hashlib.sha256(raw.replace(b'\r\n',b'\n')).hexdigest()

def daily_bp(sessions):
    frame=pd.DataFrame(sessions).copy()
    from .bp_policy import assessed_frame
    frame=assessed_frame(frame)
    frame['date']=pd.to_datetime(frame.date).dt.normalize()
    # Matches historical baseline: available SBP per session, then equal day weight.
    return frame.groupby(['respondent_id','date'],as_index=False).agg(sbp=('sbp_mean','mean'),dbp=('dbp_mean','mean'))

def make_training(profiles,days,sessions):
    profiles=pd.DataFrame(profiles).set_index('respondent_id')
    days=pd.DataFrame(days).copy();days['date']=pd.to_datetime(days.date).dt.normalize()
    panel=daily_bp(sessions).merge(days,on=['respondent_id','date'],how='left',validate='one_to_one')
    output=[]
    for rid,group in panel.groupby('respondent_id'):
        group=group.sort_values('date').set_index('date')
        for origin in group.index:
            past_dates=pd.date_range(origin-pd.Timedelta(days=6),origin)
            future_dates=pd.date_range(origin+pd.Timedelta(days=1),origin+pd.Timedelta(days=7))
            if not past_dates.isin(group.index).all() or not future_dates.isin(group.index).all():continue
            prev=group.loc[past_dates];future=group.loc[future_dates]
            if prev.sbp.isna().any() or future.sbp.isna().any():continue
            output.append(dict(respondent_id=rid,asof_date=str(origin.date()),history_start=str(past_dates[0].date()),
                target_start=str(future_dates[0].date()),target_end=str(future_dates[-1].date()),
                past_7d_sbp=float(prev.sbp.mean()),past_7d_dbp=float(prev.dbp.mean()),past_7d_sbp_std=float(prev.sbp.std(ddof=0)),
                age=profiles.loc[rid,'age'],bmi=profiles.loc[rid,'bmi'],past_7d_activity=float(prev.activity_minutes.mean()),
                past_7d_sleep=float(prev.sleep_hours.mean()),past_7d_stress=float(prev.stress.mean()),target=float(future.sbp.mean())))
    return pd.DataFrame(output,columns=WINDOW_FIELDS)

def partitions(frame):
    if frame.empty or frame.respondent_id.nunique()<8:raise ValueError('At least 8 synthetic IDs with complete windows required for this technical experiment.')
    train,test=next(GroupShuffleSplit(n_splits=1,test_size=CONFIG['heldout_id_fraction'],random_state=CONFIG['seed']).split(frame,groups=frame.respondent_id))
    # Fixed 60% of observed calendar, chosen before evaluating model scores.
    first=pd.Timestamp(frame.history_start.min());last=pd.Timestamp(frame.target_end.max())
    cutoff=(first+pd.Timedelta(days=int(((last-first).days+1)*CONFIG['calendar_train_fraction'])-1)).date().isoformat()
    early=frame.iloc[train];early=early[early.target_end<=cutoff]
    rolling=frame.iloc[test];rolling=rolling[rolling.asof_date>=cutoff]
    anchors=[]
    for _,group in rolling.groupby('respondent_id',sort=True):
        previous_end=None
        for index,row in group.sort_values('asof_date').iterrows():
            if previous_end is None or row.target_start>previous_end:
                anchors.append(index);previous_end=row.target_end
    primary=frame.loc[anchors]
    if early.empty or len(primary)<2:raise ValueError('Insufficient time-purged windows; do not fabricate evaluation.')
    return dict(legacy_train=frame.iloc[train],legacy_test=frame.iloc[test],train=early,test=primary,rolling_test=rolling,cutoff=cutoff)

def fit_model(training):
    model=Pipeline([('impute',SimpleImputer(strategy='median',keep_empty_features=True)),('scale',StandardScaler()),('regressor',LinearRegression())])
    return model.fit(training[FEATURES],training.target)

def evaluate(model,test):
    actual=test.target.to_numpy();predictions={'Naive 7-day mean':test.past_7d_sbp.to_numpy(),'Linear Regression':model.predict(test[FEATURES])}
    scores=[]
    for name,prediction in predictions.items():
        scores.append(dict(model=name,mae=float(mean_absolute_error(actual,prediction)),rmse=float(np.sqrt(mean_squared_error(actual,prediction))),
                           r2=float(r2_score(actual,prediction)) if len(actual)>1 and np.ptp(actual)>0 else None))
    rows=test[['respondent_id','asof_date','target_start','target_end','target']].rename(columns={'asof_date':'date','target':'actual'}).copy()
    rows['naive']=predictions['Naive 7-day mean'];rows['linear']=predictions['Linear Regression']
    rows['naive_residual']=rows.actual-rows.naive;rows['linear_residual']=rows.actual-rows.linear
    return scores,rows

def window_keys(frame,start,end):
    return {(row.respondent_id,day.date().isoformat()) for row in frame.itertuples() for day in pd.date_range(getattr(row,start),getattr(row,end))}

def leakage_audit(training,test,model):
    train_keys=window_keys(training,'history_start','target_end');test_keys=window_keys(test,'history_start','target_end')
    target_keys=window_keys(test,'target_start','target_end')
    target_overlap=len(test)*7-len(target_keys)
    medians=training[FEATURES].median().fillna(0).to_numpy()
    imputed=model.named_steps['impute'].transform(training[FEATURES])
    result=dict(subject_overlap=sorted(set(training.respondent_id)&set(test.respondent_id)),
        shared_measurement_id_dates=len(train_keys&test_keys),train_target_end_max=training.target_end.max(),test_origin_min=test.asof_date.min(),
        labels_available_before_test=training.target_end.max()<=test.asof_date.min(),test_overlapping_target_id_days=target_overlap,
        imputer_matches_training_only=bool(np.allclose(model.named_steps['impute'].statistics_,medians)),
        scaler_matches_training_only=bool(np.allclose(model.named_steps['scale'].mean_,imputed.mean(axis=0))),
        training_overlapping_target_id_days=len(training)*7-len(window_keys(training,'target_start','target_end')))
    assert not result['subject_overlap'] and result['shared_measurement_id_dates']==0 and result['labels_available_before_test'] and target_overlap==0
    assert result['imputer_matches_training_only'] and result['scaler_matches_training_only']
    return result

def predict_naive(sessions,respondent_id,asof=None):
    day=daily_bp(sessions);day=day[(day.respondent_id==respondent_id)&day.sbp.notna()].sort_values('date')
    if asof:
        day=day[day.date<=pd.Timestamp(asof)]
        if day.empty or day.date.iloc[-1]!=pd.Timestamp(asof):raise ValueError('Tanggal prediksi tidak memiliki SBP yang tersedia.')
    if day.empty:raise LookupError('ID responden tidak tersedia atau tidak punya SBP valid')
    origin=day.date.iloc[-1];dates=pd.date_range(origin-pd.Timedelta(days=6),origin)
    if not dates.isin(day.date).all():raise ValueError('Dibutuhkan 7 hari kalender berturut-turut untuk baseline.')
    previous=day[day.date.isin(dates)]
    return dict(respondent_id=respondent_id,last_date=str(origin.date()),history_start=str(dates[0].date()),
        forecast_start=str((origin+pd.Timedelta(days=1)).date()),forecast_end=str((origin+pd.Timedelta(days=7)).date()),
        prediction_mmHg=round(float(previous.sbp.mean()),2),baseline='Rata-rata SBP 7 hari terakhir',target=TARGET,
        is_synthetic=True,is_diagnosis=False,status='DATA SINTETIS / SIMULASI - BUKAN DIAGNOSIS')

def run_experiment(profile_csv,day_csv,out_dir,report_dir=None):
    profiles,days,sessions,quality=prepare(pd.read_csv(profile_csv,dtype=str,keep_default_na=False),pd.read_csv(day_csv,dtype=str,keep_default_na=False),synthetic=True)
    if any(not row['respondent_id'].startswith('SIM') for row in profiles):
        raise ValueError('Eksperimen CP3 ini hanya untuk ID sintetis SIM; data aktual tidak boleh dilabeli simulasi.')
    frame=make_training(profiles,days,sessions);parts=partitions(frame)
    model=fit_model(parts['train']);scores,samples=evaluate(model,parts['test']);audit=leakage_audit(parts['train'],parts['test'],model)
    legacy_scores,legacy_predictions=evaluate(fit_model(parts['legacy_train']),parts['legacy_test'])
    rolling_scores,rolling_predictions=evaluate(model,parts['rolling_test'])
    provenance=dict(text_hash_mode='utf8-lf-v1',profile_sha256=text_sha256(profile_csv),daily_sha256=text_sha256(day_csv),prepared_content_sha256=quality['prepared_content_sha256'],
        code_sha256=text_sha256(__file__),bp_policy_sha256=text_sha256(Path(__file__).with_name('bp_policy.py')),pipeline_sha256=text_sha256(Path(__file__).with_name('pipeline.py')),versions=dict(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,sklearn=sklearn.__version__,joblib=joblib.__version__))
    run_id=hashlib.sha256(json.dumps(dict(provenance=provenance,config=CONFIG),sort_keys=True).encode()).hexdigest()[:20]
    result=dict(schema_version=2,run_id=run_id,status='DATA SINTETIS / SIMULASI - EKSPERIMEN',target=TARGET,target_approved=False,
        description='Rerata SBP harian t+1..t+7; origin akhir hari t. Usulan target, belum disetujui dosen.',
        dataset=f'{len(profiles)} ID sintetis, {len(days)} ID-tanggal, {len(sessions)} sesi; {len(frame)} complete windows.',
        rows_training=len(parts['train']),rows_test=len(parts['test']),respondents_train=sorted(parts['train'].respondent_id.unique().tolist()),
        respondents_test=sorted(parts['test'].respondent_id.unique().tolist()),features=FEATURES,config=CONFIG,cutoff=parts['cutoff'],
        split='Held-out respondent IDs + chronological label purge + non-overlapping 7-day test targets (seed=42)',
        scores=scores,actual_vs_predicted=json.loads(samples.to_json(orient='records',double_precision=15)),
        audit=audit,provenance=provenance,model='Linear Regression (pembanding baseline naif)',tuned=False,real_model_validated=False,
        as_of=date.today().isoformat(),limitation='DATA SINTETIS; hanya '+str(len(parts['test']))+' origin uji pada '+str(parts['test'].respondent_id.nunique())+' ID. Target belum disetujui. Training windows masih berkorelasi; profil statis diasumsikan diketahui sebelum origin. Bukan validasi klinis atau diagnosis.',
        secondary_evaluations=dict(legacy_subject_only=dict(rows_train=len(parts['legacy_train']),rows_test=len(parts['legacy_test']),scores=legacy_scores,
            overlapping_test_target_id_days=len(parts['legacy_test'])*7-len(window_keys(parts['legacy_test'],'target_start','target_end')),
            limitation='Same-calendar group split; overlapping test labels. Not a strict future-forecast estimate.'),
            purged_rolling=dict(rows_test=len(parts['rolling_test']),scores=rolling_scores,limitation='Held-out IDs/time, but adjacent test target windows overlap. Sensitivity only.')))
    out=Path(out_dir);out.mkdir(exist_ok=True,parents=True)
    joblib.dump(model,out/'linear_regression_synthetic.joblib')
    result['model_sha256']=sha256(out/'linear_regression_synthetic.joblib')
    (out/'baseline_metrics.json').write_bytes((json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode('utf-8'))
    (out/'baseline_manifest.json').write_bytes((json.dumps(dict(schema_version=3,metrics_hash_mode='utf8-lf-v1',run_id=run_id,metrics_sha256=text_sha256(out/'baseline_metrics.json'),model_sha256=result['model_sha256']),indent=2)+'\n').encode('utf-8'))
    if report_dir:
        report=Path(report_dir);report.mkdir(exist_ok=True,parents=True)
        frame.to_csv(report/'all_windows.csv',index=False)
        for key in ['train','test','rolling_test']:parts[key].to_csv(report/(key+'_windows.csv'),index=False)
        samples.to_csv(report/'primary_predictions.csv',index=False,float_format='%.15g')
        legacy_predictions.to_csv(report/'legacy_predictions.csv',index=False,float_format='%.15g')
        rolling_predictions.to_csv(report/'rolling_predictions.csv',index=False,float_format='%.15g')
        samples.assign(abs_linear_error=samples.linear_residual.abs()).sort_values('abs_linear_error',ascending=False).to_csv(report/'error_analysis.csv',index=False)
        (report/'experiment.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    return result

def load_experiment(folder):
    folder=Path(folder)
    try:
        manifest=json.loads((folder/'baseline_manifest.json').read_text(encoding='utf-8'))
        mode=manifest.get('metrics_hash_mode','raw-bytes')
        if mode not in ('raw-bytes','utf8-lf-v1'):raise ValueError('Unknown hash mode')
        metrics_hash=text_sha256(folder/'baseline_metrics.json') if mode=='utf8-lf-v1' else sha256(folder/'baseline_metrics.json')
        if metrics_hash!=manifest['metrics_sha256'] or sha256(folder/'linear_regression_synthetic.joblib')!=manifest['model_sha256']:
            raise ValueError('Artifact hash mismatch')
        result=json.loads((folder/'baseline_metrics.json').read_text(encoding='utf-8'))
        if result['schema_version']!=2 or result['run_id']!=manifest['run_id'] or result['target']!=TARGET:raise ValueError('Artifact contract mismatch')
        return {**result,'available':True,'artifact_integrity_verified':True}
    except (OSError,ValueError,KeyError,TypeError):
        return dict(available=False,message='Artefak baseline belum tersedia atau integritasnya gagal. Jalankan verifikasi CP3 secara offline; metrik tidak diganti data contoh.')
