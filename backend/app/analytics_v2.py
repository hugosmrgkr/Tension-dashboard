"""CP3 serving contract: analytics are read from the selected warehouse snapshot."""
import json
import pandas as pd
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from .models import Participant, CalendarDate, SessionType, BPSession, DailyBehavior, SourceState

AGE_GROUPS = ['<15', '15\u201329', '30\u201344', '45\u201359', '60+', 'Tidak diketahui']
EXPORT_FIELDS = {
    'participants': ['respondent_id','age','gender','province','city','occupation','education','height_cm','weight_kg','bmi','active_days_week','days'],
    'daily': ['respondent_id','date','sleep_hours','stress','activity_type','activity_minutes','heavy_minutes','sitting','salty_food','fruit','vegetable','caffeine','smoked','smoke_count','medication','sbp_mean','dbp_mean'],
    'sessions': ['respondent_id','date','session','measured_at','sbp1','dbp1','sbp2','dbp2','sbp_mean','dbp_mean','valid_sbp_count','valid_dbp_count','is_valid'],
}


def age_band(value):
    if pd.isna(value): return 'Tidak diketahui'
    if value < 15: return '<15'
    if value < 30: return AGE_GROUPS[1]
    if value < 45: return AGE_GROUPS[2]
    if value < 60: return AGE_GROUPS[3]
    return '60+'


def source_summary(db):
    state = db.get(SourceState, 1)
    counts = {key: db.scalar(select(func.count()).select_from(model)) for key,model in
              [('participants',Participant),('daily_records',DailyBehavior),('session_records',BPSession)]}
    empty = not any(counts.values())
    kind = state.source_kind if state else 'empty' if empty else 'unknown'
    restricted = kind not in ('synthetic','empty') and (state is not None or not empty)
    message = ('Warehouse belum berisi data. Pengelola dapat memvalidasi dua formulir melalui ETL manual; aplikasi tidak mengisi data otomatis.' if empty else
               'Data non-sintetis memerlukan persetujuan dan kontrol akses sebelum ditampilkan.' if restricted else
               'DATA SINTETIS / SIMULASI. Data responden asli masih dalam proses pengumpulan.')
    return state, dict(**counts,source_kind=kind,warehouse_empty=empty,access_restricted=restricted,message=message)


def metadata_payload(db):
    state, result = source_summary(db)
    result.update(source=state.source_name if state else 'Belum ada sumber data',
                  min_date=None,max_date=None,gender=[],province=[],city=[],occupation=[],respondent_ids=[],sessions=[],age_groups=[],
                  etl_audit_version=None,data_version=None)
    if result['access_restricted']:
        for key in ('participants','daily_records','session_records'): result[key]=None
        return result
    profiles = pd.read_sql(select(*[c for c in Participant.__table__.columns if c.name!='conditions_json']),db.connection())
    for key in ('gender','province','city','occupation'):
        result[key] = sorted(profiles[key].dropna().unique().tolist())
    result['respondent_ids'] = sorted(profiles.respondent_id.dropna().unique().tolist())
    result['cities_by_province'] = {str(province):sorted(group.city.dropna().unique().tolist())
                                     for province,group in profiles.dropna(subset=['province']).groupby('province')}
    result['education'] = sorted(profiles.education.dropna().unique().tolist())
    result['age_groups'] = [label for label in AGE_GROUPS if label in set(profiles.age.map(age_band))]
    result['sessions'] = list(db.scalars(select(SessionType.name).join(BPSession,BPSession.session_id==SessionType.id).distinct().order_by(SessionType.name)))
    low, high = db.execute(select(func.min(CalendarDate.date),func.max(CalendarDate.date)).join(DailyBehavior,DailyBehavior.date_id==CalendarDate.id)).one()
    result.update(min_date=str(low) if low else None,max_date=str(high) if high else None)
    quality=json.loads(state.quality_json or '{}') if state else {}
    result.update(etl_audit_version=quality.get('audit_version'),data_version=quality.get('prepared_content_sha256'))
    return result


def frames(db:Session):
    connection=db.connection()
    profiles=pd.read_sql(select(Participant),connection).drop(columns=['conditions_json'])
    dates=pd.read_sql(select(CalendarDate),connection)
    sessions=pd.read_sql(select(SessionType),connection)
    bp=pd.read_sql(select(BPSession),connection)
    daily=pd.read_sql(select(DailyBehavior),connection)
    prof=profiles.rename(columns={'id':'participant_id'})
    cal=dates[['id','date']].rename(columns={'id':'date_id'})
    se=sessions[['id','name']].rename(columns={'id':'session_id','name':'session'})
    session_frame=bp.merge(prof,on='participant_id',how='left',suffixes=('','_profile')).merge(cal,on='date_id',how='left').merge(se,on='session_id',how='left')
    daily_frame=daily.merge(prof,on='participant_id',how='left',suffixes=('','_profile')).merge(cal,on='date_id',how='left')
    return prof,session_frame,daily_frame


def filter_frames(profiles,bp,daily,query):
    for key in ('gender','province','city','occupation','education','respondent_id'):
        if query.get(key):
            profiles=profiles[profiles[key]==query[key]]
            bp=bp[bp[key]==query[key]]; daily=daily[daily[key]==query[key]]
    if query.get('age_group'):
        profiles=profiles[profiles.age.map(age_band)==query['age_group']]
        bp=bp[bp.age.map(age_band)==query['age_group']];daily=daily[daily.age.map(age_band)==query['age_group']]
    for key in ('start_date','end_date'):
        if query.get(key):
            bound=pd.Timestamp(query[key])
            if key=='start_date':
                bp=bp[pd.to_datetime(bp.date)>=bound];daily=daily[pd.to_datetime(daily.date)>=bound]
            else:
                bp=bp[pd.to_datetime(bp.date)<=bound];daily=daily[pd.to_datetime(daily.date)<=bound]
    if query.get('session'):
        bp=bp[bp.session==query['session']]
        daily=daily.merge(bp[['respondent_id','date']].drop_duplicates(),on=['respondent_id','date'],how='inner',validate='one_to_one')
    if any(query.get(k) for k in ('start_date','end_date','session')):
        profiles=profiles[profiles.respondent_id.isin(set(daily.respondent_id)|set(bp.respondent_id))]
    return profiles,bp,daily


def records(frame,fields=None,limit=None):
    if fields: frame=frame.reindex(columns=fields)
    frame=(frame.head(limit) if limit is not None else frame).copy()
    for column in frame.columns:
        if pd.api.types.is_datetime64_any_dtype(frame[column]): frame[column]=frame[column].dt.strftime('%Y-%m-%d')
        elif frame[column].dtype=='object': frame[column]=frame[column].map(lambda value:value.isoformat() if hasattr(value,'isoformat') else value)
    return json.loads(frame.to_json(orient='records',date_format='iso'))


def dataframe_to_json(frame):
    return records(frame)


def analytics(db:Session,query=None):
    query=query or {}
    original=frames(db)
    warehouse_empty=not any(len(frame) for frame in original)
    p,s,d=filter_frames(*original,query)
    s=s.copy();s['is_valid']=s.sbp_mean.notna() & s.dbp_mean.notna()
    valid=s[s.is_valid].copy()
    state=db.get(SourceState,1)
    quality=json.loads(state.quality_json or '{}') if state else {}
    daily_sbp=valid.groupby(['respondent_id','date'],as_index=False).agg(sbp_mean=('sbp_mean','mean'),dbp_mean=('dbp_mean','mean'))
    day_data=d.merge(daily_sbp,on=['respondent_id','date'],how='left',validate='one_to_one')
    n=len(valid)
    scoped=dict(daily_records=len(d),session_records=len(s),valid_sessions=n,incomplete_sessions=len(s)-n,
                **{'missing_'+field:int(d[field].isna().sum()) for field in ['sleep_hours','sitting','stress','activity_minutes','smoke_count']})
    reason=('warehouse_empty' if warehouse_empty else 'filters_empty' if not len(s) and not len(d) else 'no_valid_sessions' if not n else None)
    messages={
        'warehouse_empty':'Warehouse belum berisi data. Tidak ada angka atau grafik contoh yang ditampilkan. Jalankan ETL manual setelah validasi dan persetujuan.',
        'filters_empty':'Tidak ada catatan pada pilihan filter ini. Ubah atau reset filter untuk melihat data yang tersedia.',
        'no_valid_sessions':'Belum ada sesi dengan sistolik dan diastolik valid pada pilihan ini. Pembacaan kosong tetap ditampilkan di tabel, bukan diganti nol.',
    }
    trend=[];boxes=[];scatter=[];small=[];session_stats=[]
    categories={key:[] for key in ['salty_food','fruit','vegetable','caffeine','sitting','smoked','medication','activity_type','occupation']}
    if n:
        trend=records(valid.groupby(['date','session'],as_index=False).agg(sbp=('sbp_mean','mean'),dbp=('dbp_mean','mean'),n=('sbp_mean','size')).sort_values(['date','session']))
        boxes=records(valid[['session','sbp_mean','dbp_mean','age','respondent_id']].assign(age_group=valid.age.map(age_band)))
        scatter=records(day_data[['respondent_id','date','sleep_hours','stress','activity_minutes','heavy_minutes','sbp_mean','dbp_mean','age','gender','salty_food','fruit','vegetable','caffeine','smoked','smoke_count','medication','sitting','occupation']].assign(age_group=day_data.age.map(age_band)))
        for key in categories:
            groups=day_data.dropna(subset=[key,'sbp_mean']).groupby(key,as_index=False).agg(sbp=('sbp_mean','mean'),n=('sbp_mean','size'),respondents=('respondent_id','nunique'))
            categories[key]=records(groups.rename(columns={key:'category'}).round({'sbp':1}))
        small=records(valid.assign(age_group=valid.age.map(age_band)).groupby(['date','age_group'],as_index=False).agg(sbp=('sbp_mean','mean'),n=('sbp_mean','size')))
        session_stats=records(valid.groupby('session',as_index=False).agg(sbp=('sbp_mean','mean'),dbp=('dbp_mean','mean'),n=('sbp_mean','size')))
    profile_days=d.groupby('respondent_id',as_index=False).agg(days=('date','nunique'))
    participants=p.merge(profile_days,on='respondent_id',how='left',validate='one_to_one').fillna({'days':0})
    demographics={}
    for key in ['gender','education','occupation','province','city','age_group']:
        values=p.age.map(age_band) if key=='age_group' else p[key].fillna('Tidak diketahui')
        demographics[key]=records(values.value_counts().rename_axis('category').reset_index(name='n'))
    correlations=[]
    for key in ['sleep_hours','stress','activity_minutes','smoke_count']:
        pairs=day_data.dropna(subset=[key,'sbp_mean'])
        coefficient=(float(pairs[key].corr(pairs.sbp_mean))
                     if len(pairs)>=3 and pairs[key].nunique()>1 and pairs.sbp_mean.nunique()>1 else None)
        correlations.append(dict(field=key,n=len(pairs),respondents=int(pairs.respondent_id.nunique()),r=coefficient))
    comparison=None
    if query.get('start_date') and query.get('end_date'):
        first=pd.Timestamp(query['start_date']);last=pd.Timestamp(query['end_date']);span=(last-first).days+1
        start=(first-pd.Timedelta(days=span)).date();end=(first-pd.Timedelta(days=1)).date()
        _,old_s,old_d=filter_frames(*original,{**query,'start_date':str(start),'end_date':str(end)})
        old_valid=old_s.dropna(subset=['sbp_mean','dbp_mean'])
        comparison=dict(period=f'{start} - {end}',has_data=bool(len(old_valid) or len(old_d)),
                        active=int(old_valid.respondent_id.nunique()),daily=len(old_d),sessions=len(old_valid),
                        sbp=round(float(old_valid.sbp_mean.mean()),1) if len(old_valid) else None)
    return dict(source_kind=state.source_kind if state else 'empty' if warehouse_empty else 'unknown',
                data_version=quality.get('prepared_content_sha256'),empty=not n,empty_reason=reason,message=messages.get(reason),
                filters={k:v for k,v in query.items() if v is not None},
                kpis=dict(respondents=int(valid.respondent_id.nunique()),daily_records=len(d),sessions=n,
                          mean_sbp=round(float(valid.sbp_mean.mean()),1) if n else None,
                          mean_dbp=round(float(valid.dbp_mean.mean()),1) if n else None,dates=int(d.date.nunique())),
                comparison=comparison,trend=trend,session_box=boxes,heatmap=trend,scatter=scatter,categories=categories,
                demographics=demographics,correlations=correlations,
                small_multiples=small,session_stats=session_stats,
                participants=records(participants,EXPORT_FIELDS['participants']),
                daily_rows=records(day_data.sort_values(['date','respondent_id'],ascending=[False,True]),EXPORT_FIELDS['daily']),
                session_rows=records(s.sort_values(['date','respondent_id','session'],ascending=[False,True,True]),EXPORT_FIELDS['sessions']),
                quality=quality,filtered_quality=scoped,
                definitions=dict(respondents='ID unik dengan sedikitnya satu sesi valid pada filter.',
                    daily_records='Catatan ID-tanggal diterima; tidak digandakan untuk dua sesi.',
                    sessions='Sesi dengan sedikitnya satu SBP dan satu DBP valid.',
                    session_rows='Semua sesi pada filter, termasuk pembacaan tidak lengkap.',
                    mean_sbp='Rata-rata SBP sesi valid, mmHg.',
                    quality='Snapshot laporan batch ETL seluruh sumber; bukan statistik filter.',
                    filtered_quality='Missing dan validitas dihitung ulang dari baris PostgreSQL pada filter.'))
