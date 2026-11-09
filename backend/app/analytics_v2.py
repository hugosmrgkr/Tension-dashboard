"""Reusable dashboard/EDA statistics, based on session and daily fact grain."""
import json
import pandas as pd
import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import Participant, CalendarDate, SessionType, BPSession, DailyBehavior, SourceState

def frames(db:Session):
    profiles=pd.read_sql(select(Participant),db.bind).drop(columns=['conditions_json'])
    dates=pd.read_sql(select(CalendarDate),db.bind)
    sessions=pd.read_sql(select(SessionType),db.bind)
    bp=pd.read_sql(select(BPSession).with_only_columns(*[c for c in BPSession.__table__.columns]),db.bind)
    daily=pd.read_sql(select(DailyBehavior),db.bind)
    prof=profiles.rename(columns={'id':'participant_id'})
    cal=dates[['id','date']].rename(columns={'id':'date_id'})
    se=sessions[['id','name']].rename(columns={'id':'session_id','name':'session'})
    session_frame=bp.merge(prof,on='participant_id',how='left',suffixes=('','_profile')).merge(cal,on='date_id',how='left').merge(se,on='session_id',how='left')
    daily_frame=daily.merge(prof,on='participant_id',how='left',suffixes=('','_profile')).merge(cal,on='date_id',how='left')
    return prof,session_frame,daily_frame

def filter_frames(profiles,bp,daily,q):
    common=[]
    for key in ('gender','province','city','occupation','respondent_id'):
        if q.get(key): common.append((key,q[key]))
    for key,val in common:
        bp=bp[bp[key]==val];daily=daily[daily[key]==val];profiles=profiles[profiles[key]==val] if key in profiles else profiles
    if q.get('start_date'):
        date=pd.Timestamp(q['start_date']);bp=bp[pd.to_datetime(bp.date)>=date];daily=daily[pd.to_datetime(daily.date)>=date]
    if q.get('end_date'):
        date=pd.Timestamp(q['end_date']);bp=bp[pd.to_datetime(bp.date)<=date];daily=daily[pd.to_datetime(daily.date)<=date]
    if q.get('session'):
        bp=bp[bp.session==q['session']]
    if q.get('age_group'):
        label=q['age_group']
        bp=bp[bp.age.apply(age_band)==label];daily=daily[daily.age.apply(age_band)==label];profiles=profiles[profiles.age.apply(age_band)==label]
    return profiles,bp,daily

def age_band(v):
    if pd.isna(v):return 'Tidak diketahui'
    v=int(v)
    if v<30:return '15–29'
    if v<45:return '30–44'
    if v<60:return '45–59'
    return '60+'

def records(frame,fields=None,limit=5000):
    if fields: frame=frame.reindex(columns=fields)
    frame=frame.head(limit).copy()
    for c in frame.columns:
        if pd.api.types.is_datetime64_any_dtype(frame[c]): frame[c]=frame[c].dt.strftime('%Y-%m-%d')
        elif frame[c].dtype=='object':frame[c]=frame[c].map(lambda x:x.isoformat() if hasattr(x,'isoformat') else x)
    return json.loads(frame.where(pd.notna(frame),None).to_json(orient='records',date_format='iso'))

def dataframe_to_json(frame):
    return records(frame,limit=10000)

def analytics(db:Session,query=None):
    query=query or {}
    p,s,d=filter_frames(*frames(db),query)
    valid=s[s.sbp_mean.notna() & s.dbp_mean.notna()].copy()
    state=db.get(SourceState,1)
    quality=json.loads(state.quality_json or '{}') if state else {}
    # Note: each daily row is ONE person/day, even when there are two BP sessions.
    daily_sbp=valid.groupby(['respondent_id','date'],as_index=False).agg(sbp_mean=('sbp_mean','mean'),dbp_mean=('dbp_mean','mean'))
    day_data=d.merge(daily_sbp,on=['respondent_id','date'],how='left')
    dates_count=int(d.date.nunique()) if len(d) else 0
    active=int(valid.respondent_id.nunique())
    daily_count=int(len(d))
    n_sessions=int(len(valid))
    sbp_mean=round(float(valid.sbp_mean.mean()),1) if n_sessions else None
    dbp_mean=round(float(valid.dbp_mean.mean()),1) if n_sessions else None
    if n_sessions:
        trend=valid.groupby(['date','session'],as_index=False).agg(sbp=('sbp_mean','mean'),dbp=('dbp_mean','mean'),n=('sbp_mean','size'))
        trend=trend.sort_values(['date','session'])
        trend=records(trend)
        boxes=records(valid[['session','sbp_mean','dbp_mean','age','respondent_id']].assign(age_group=valid.age.map(age_band)))
        heat=trend
        # daily grain for factors prevents double counting
        scatter=records(day_data[['respondent_id','date','sleep_hours','stress','activity_minutes','heavy_minutes','sbp_mean','dbp_mean','age','gender','salty_food','fruit','vegetable','caffeine','smoked','sitting','occupation']])
        scatter = [{**x, 'age_group':age_band(x.get('age'))} for x in scatter]
        def groups(col):
            a=day_data.dropna(subset=[col,'sbp_mean']).groupby(col,as_index=False).agg(sbp=('sbp_mean','mean'),n=('sbp_mean','size'))
            return records(a.rename(columns={col:'category'}).round({'sbp':1}))
        categories={key:groups(key) for key in ['salty_food','fruit','vegetable','caffeine','sitting','smoked','activity_type','occupation']}
        age_lines=valid.assign(age_group=valid.age.map(age_band)).groupby(['date','age_group'],as_index=False).agg(sbp=('sbp_mean','mean'),n=('sbp_mean','size'))
        small_multiples=records(age_lines)
    else:
        trend=[];boxes=[];heat=[];scatter=[];categories={k:[] for k in ['salty_food','fruit','vegetable','caffeine','sitting','smoked','activity_type','occupation']};small_multiples=[]
    profiles_daily=d.groupby('respondent_id',as_index=False).agg(days=('date','nunique')) if len(d) else pd.DataFrame(columns=['respondent_id','days'])
    participants=profiles_daily.merge(p,on='respondent_id',how='right').fillna({'days':0})
    display_cols=['respondent_id','age','gender','province','city','occupation','education','height_cm','weight_kg','bmi','active_days_week','days']
    comparison=None
    if len(d) and query.get('start_date') and query.get('end_date'):
        a=pd.Timestamp(query['start_date']);b=pd.Timestamp(query['end_date']);span=(b-a).days+1
        prev_start=(a-pd.Timedelta(days=span)).date();prev_end=(a-pd.Timedelta(days=1)).date()
        pp,ps,pdail=frames(db)
        old_query={**query,'start_date':str(prev_start),'end_date':str(prev_end)}
        _,ps,pdail=filter_frames(pp,ps,pdail,old_query)
        previous_valid=ps[ps.sbp_mean.notna()&ps.dbp_mean.notna()]
        comparison={'period':f'{prev_start} — {prev_end}','active':int(previous_valid.respondent_id.nunique()),'daily':len(pdail),'sessions':len(previous_valid),'sbp':round(float(previous_valid.sbp_mean.mean()),1) if len(previous_valid) else None}
    return {
      'source_kind':state.source_kind if state else 'unknown',
      'empty':not len(valid),
      'kpis':{'respondents':active,'daily_records':daily_count,'sessions':n_sessions,'mean_sbp':sbp_mean,'mean_dbp':dbp_mean,'dates':dates_count},
      'comparison':comparison,'trend':trend,'session_box':boxes,'heatmap':heat,'scatter':scatter,'categories':categories,
      'small_multiples':small_multiples, 'participants':records(participants,display_cols),
      'daily_rows':records(day_data.sort_values(['date','respondent_id'],ascending=[False,True]),
              ['respondent_id','date','sleep_hours','stress','activity_minutes','heavy_minutes','sitting','salty_food','fruit','vegetable','caffeine','smoked','medication','sbp_mean','dbp_mean']),
      'session_rows':records(valid.sort_values(['date','respondent_id'],ascending=[False,True]),
              ['respondent_id','date','session','measured_at','sbp1','dbp1','sbp2','dbp2','sbp_mean','dbp_mean','valid_sbp_count','valid_dbp_count']),
      'quality':quality,
      'definitions':{'respondents':'ID unik dengan ≥1 sesi valid pada filter.',
            'daily_records':'Jumlah kombinasi ID dan tanggal pada filter, tidak sama dengan jumlah responden.',
            'sessions':'Sesi Pagi/Malam dengan paling sedikit satu SBP dan satu DBP valid.',
            'mean_sbp':'Rata-rata SBP per sesi valid (mmHg), bukan diagnosis.',
            'sleep':'HH:MM pada CSV sintetis diperlakukan sebagai durasi jam:menit untuk demo.'}
    }
