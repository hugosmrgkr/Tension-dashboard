"""Leakage-safe experimental baseline for next-7-calendar-day average SBP.

For each respondent and day t, input is mean SBP on t-6..t, target is mean
SBP on t+1..t+7. Only complete windows from synthetic fixtures are used.
Group split by respondent ensures no individual is present in two partitions.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from .pipeline import prepare

FEATURES=['past_7d_sbp','past_7d_dbp','past_7d_sbp_std','age','bmi','past_7d_activity','past_7d_sleep','past_7d_stress']

def make_training(profiles,days,sessions):
    p=pd.DataFrame(profiles).set_index('respondent_id')
    sess=pd.DataFrame(sessions)
    day=pd.DataFrame(days)
    bp=sess.groupby(['respondent_id','date'],as_index=False).agg(sbp=('sbp_mean','mean'),dbp=('dbp_mean','mean'))
    panel=bp.merge(day,on=['respondent_id','date'],how='left')
    output=[]
    for rid,group in panel.groupby('respondent_id'):
        group=group.sort_values('date').reset_index(drop=True)
        for i in range(6,len(group)-7):
            prev=group.iloc[i-6:i+1];future=group.iloc[i+1:i+8]
            # All windows are exactly seven consecutive days; unavailable days => skip.
            if ((prev.date.max()-prev.date.min()).days!=6 or (future.date.max()-future.date.min()).days!=6 or
                (future.date.min()-prev.date.max()).days!=1 or prev.sbp.isna().any() or future.sbp.isna().any()): continue
            x={'respondent_id':rid,'asof_date':str(group.iloc[i].date),
                'past_7d_sbp':float(prev.sbp.mean()),'past_7d_dbp':float(prev.dbp.mean()),
                'past_7d_sbp_std':float(prev.sbp.std(ddof=0)), 'age':p.loc[rid,'age'],'bmi':p.loc[rid,'bmi'],
                'past_7d_activity':float(prev.activity_minutes.mean()),'past_7d_sleep':float(prev.sleep_hours.mean()),
                'past_7d_stress':float(prev.stress.mean()),'target':float(future.sbp.mean())}
            output.append(x)
    return pd.DataFrame(output)

def run_experiment(profile_csv,day_csv,out_dir):
    p,d,s,_=prepare(pd.read_csv(profile_csv,dtype=str,keep_default_na=False),pd.read_csv(day_csv,dtype=str,keep_default_na=False),synthetic=True)
    df=make_training(p,d,s)
    if df.empty or df.respondent_id.nunique()<8: raise ValueError('Dataset belum cukup untuk eksperimen group split')
    idx=np.arange(len(df)); groups=df.respondent_id.values
    split=GroupShuffleSplit(n_splits=1,test_size=.32,random_state=42)
    train_ix,test_ix=next(split.split(idx,groups=groups))
    xtrain=df.iloc[train_ix][FEATURES];xtest=df.iloc[test_ix][FEATURES]
    ytrain=df.iloc[train_ix].target;ytest=df.iloc[test_ix].target
    pipeline=Pipeline([('impute',SimpleImputer(strategy='median')),('scale',StandardScaler()),('regressor',LinearRegression())])
    pipeline.fit(xtrain,ytrain)
    predictions={'Naive 7-day mean':xtest.past_7d_sbp.values,'Linear Regression':pipeline.predict(xtest)}
    scores=[]
    for name,pred in predictions.items():
        scores.append({'model':name,'mae':round(float(mean_absolute_error(ytest,pred)),3),'rmse':round(float(np.sqrt(mean_squared_error(ytest,pred))),3),
                       'r2':round(float(r2_score(ytest,pred)),3)})
    samples=[]
    for i,(_,row) in enumerate(df.iloc[test_ix].iterrows()):
        samples.append({'respondent_id':row.respondent_id,'date':row.asof_date,'actual':round(float(ytest.iloc[i]),2),
                        'naive':round(float(predictions['Naive 7-day mean'][i]),2),
                        'linear':round(float(predictions['Linear Regression'][i]),2)})
    result={'status':'SIMULASI / EKSPERIMEN', 'target':'future_7d_mean_sbp',
       'description':'Rata-rata SBP pada tujuh hari kalender setelah tanggal prediksi; bukan diagnosis medis.',
       'dataset':'19 ID sintetis × 30 hari; satu baris training per tanggal dengan 7 hari histori dan 7 hari target.',
       'rows_training':int(len(train_ix)),'rows_test':int(len(test_ix)),
       'respondents_train':sorted(df.iloc[train_ix].respondent_id.unique().tolist()),
       'respondents_test':sorted(df.iloc[test_ix].respondent_id.unique().tolist()),
       'features':FEATURES,'split':'GroupShuffleSplit by respondent_id (random_state=42); no subject overlap',
       'scores':scores,'actual_vs_predicted':samples[:160],
       'limitation':'Evaluasi hanya pada dataset SINTETIS; peserta uji sedikit; target dan kebijakan pengukuran harus disetujui dosen. Tidak boleh diklaim sebagai hasil penelitian aktual.',
       'as_of':'2026-11-09', 'model':'Linear Regression (pembanding baseline naif)',
       'tuned':False,'real_model_validated':False}
    out=Path(out_dir);out.mkdir(exist_ok=True,parents=True)
    (out/'baseline_metrics.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    import joblib
    joblib.dump(pipeline,out/'linear_regression_synthetic.joblib')
    (out/'training_rows_preview.csv') if False else None
    return result
