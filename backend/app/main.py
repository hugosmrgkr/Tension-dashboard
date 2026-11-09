"""Toba Health Insight — survey-driven, non-clinical analytics API (checkpoint M6–M8)."""
from contextlib import asynccontextmanager
from io import BytesIO, StringIO
import json
import os
from pathlib import Path
import pandas as pd
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from .db import Base, engine, SessionLocal, get_db
from .models import Participant, CalendarDate, SessionType, BPSession, DailyBehavior, SourceState
from .pipeline import seed_if_empty, prepare, load_warehouse, DataQualityError
from .analytics_v2 import analytics, frames

@asynccontextmanager
async def lifespan(app:FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_if_empty(db)
    yield

app=FastAPI(title='Toba Health Insight API',version='2.0.0',lifespan=lifespan,
            docs_url='/api/docs',redoc_url='/api/redoc',openapi_url='/api/openapi.json')
app.add_middleware(CORSMiddleware,allow_origins=['http://localhost:5173','http://127.0.0.1:5173','http://localhost:8080'],allow_methods=['GET','POST'],allow_headers=['*'])

@app.get('/health')
@app.get('/api/health')
def health():return {'status':'ok','version':'2.0.0'}

@app.get('/api/meta')
def metadata(db:Session=Depends(get_db)):
    st=db.get(SourceState,1)
    p,s,d=frames(db)
    return {'source':st.source_name if st else 'Tidak diketahui','source_kind':st.source_kind if st else 'unknown',
      'participants':int(len(p)),'daily_records':int(len(d)),'session_records':int(len(s)),
      'min_date':str(d.date.min()) if len(d) else None,'max_date':str(d.date.max()) if len(d) else None,
      'gender':sorted(p.gender.dropna().unique().tolist()),'province':sorted(p.province.dropna().unique().tolist()),
      'city':sorted(p.city.dropna().unique().tolist()), 'occupation':sorted(p.occupation.dropna().unique().tolist()),
      'respondent_ids':sorted(p.respondent_id.dropna().unique().tolist()) if st and st.source_kind=='synthetic' else [],
      'sessions':['Pagi','Malam'],'age_groups':['15–29','30–44','45–59','60+'],
      'data_warning':'DATA SINTETIS / SIMULASI. Tidak mewakili masyarakat atau hasil penelitian.' if st and st.source_kind=='synthetic' else 'Data penelitian memerlukan persetujuan dan audit kualitas.'}

def query_args(start_date=None,end_date=None,province=None,city=None,gender=None,occupation=None,age_group=None,session=None,respondent_id=None):
    q=locals()
    for k in ('start_date','end_date'):
        if q[k]:
            try:pd.Timestamp(q[k])
            except Exception:raise HTTPException(422,f'Format {k} tidak sah')
    if q['start_date'] and q['end_date'] and q['start_date']>q['end_date']:
        raise HTTPException(422,'Tanggal awal lebih besar dari tanggal akhir')
    return q

@app.get('/api/analytics')
def get_analytics(q:dict=Depends(query_args),db:Session=Depends(get_db)):
    st=db.get(SourceState,1)
    if not st or st.source_kind!='synthetic':
        raise HTTPException(403,'Dashboard tanpa autentikasi hanya boleh menampilkan dataset sintetis. Data aktual perlu login dan perlindungan akses.')
    return analytics(db,q)

@app.get('/api/quality')
def get_quality(db:Session=Depends(get_db)):
    state=db.get(SourceState,1)
    return {'source_kind':state.source_kind if state else 'unknown','quality':json.loads(state.quality_json or '{}') if state else {}}

@app.get('/api/model/baseline')
def baseline_metadata(db:Session=Depends(get_db)):
    st=db.get(SourceState,1)
    file=Path(os.getenv('MODEL_DIR','/app/models'))/'baseline_metrics.json'
    if not file.exists():return {'available':False,'message':'Notebook eksperimen baseline belum dijalankan.'}
    result=json.loads(file.read_text(encoding='utf-8'))
    # Do not serve synthetic-derived model results as if they evaluated a different dataset.
    result['available']=(st is not None and st.source_kind=='synthetic')
    if not result['available']:result['message']='Model eksperimen sintetis dinonaktifkan pada dataset bukan sintetis.'
    return result

@app.get('/api/model/predict-baseline')
def predict_baseline(respondent_id:str=Query(...,min_length=1,max_length=40),db:Session=Depends(get_db)):
    st=db.get(SourceState,1)
    if not st or st.source_kind!='synthetic':raise HTTPException(409,'Baseline demo hanya tersedia pada dataset sintetis.')
    p,s,d=frames(db)
    bp=s[(s.respondent_id==respondent_id)&s.sbp_mean.notna()]
    if bp.empty:raise HTTPException(404,'ID responden tidak tersedia atau tidak punya sesi valid')
    day=bp.groupby('date',as_index=False).agg(sbp=('sbp_mean','mean'),dbp=('dbp_mean','mean')).sort_values('date')
    if len(day)<7 or (day.date.iloc[-1]-day.date.iloc[-7]).days!=6:
        raise HTTPException(422,'Dibutuhkan 7 hari kalender berturut-turut untuk baseline.')
    prev=day.tail(7)
    return {'respondent_id':respondent_id,'last_date':str(day.date.iloc[-1]),
            'prediction_mmHg':round(float(prev.sbp.mean()),2),'baseline':'Rata-rata SBP 7 hari terakhir',
            'target':'Estimasi rata-rata sistolik tujuh hari berikutnya',
            'is_synthetic':True,'is_diagnosis':False,'status':'DEMO EKSPERIMEN — BUKAN DIAGNOSIS'}

# Read-only by default; importing health records requires opt-in and explicit shared secret.
def admin_guard(token):
    configured=os.environ.get('IMPORT_TOKEN','').strip()
    if os.environ.get('ENABLE_IMPORT','false').lower()!='true' or not configured or token!=configured:
        raise HTTPException(403,'Impor dinonaktifkan atau token pengelola tidak sesuai. Gunakan demo lokal.')

async def read_csv_or_xlsx(file:UploadFile):
    if not file.filename or not file.filename.lower().endswith(('.csv','.xlsx')):
        raise HTTPException(422,'Hanya CSV/XLSX dengan skema formulir didukung')
    body=await file.read(5_000_001)
    if len(body)>5_000_000:raise HTTPException(413,'Batas file 5 MB')
    try:
        if file.filename.lower().endswith('.xlsx'):return pd.read_excel(BytesIO(body),dtype=str,keep_default_na=False)
        return pd.read_csv(BytesIO(body),dtype=str,keep_default_na=False,encoding='utf-8-sig')
    except Exception as e:raise HTTPException(422,'Gagal membaca berkas: '+str(e)) from e

@app.post('/api/data/import-pair')
async def import_pair(profile_file:UploadFile=File(...),daily_file:UploadFile=File(...),
       x_import_token:str|None=Header(None),db:Session=Depends(get_db)):
    admin_guard(x_import_token)
    try:
        p,d,s,quality=prepare(await read_csv_or_xlsx(profile_file),await read_csv_or_xlsx(daily_file),synthetic=False)
        # Only allow import of data with pseudonymous IDs. No real-world names are stored.
        if any(not row['respondent_id'] for row in p):raise DataQualityError('ID tidak sah')
        load_warehouse(db,p,d,s,quality,source_name='Dua formulir yang diunggah',kind='uploaded')
        return {'ok':True,'quality':quality}
    except DataQualityError as e:
        db.rollback();raise HTTPException(422,str(e)) from e

@app.get('/api/data/export/{kind}')
def export(kind:str,q:dict=Depends(query_args),db:Session=Depends(get_db)):
    if kind not in ('sessions','daily','participants'):raise HTTPException(404,'Pilihan ekspor tidak tersedia')
    st=db.get(SourceState,1)
    if not st or st.source_kind!='synthetic':raise HTTPException(403,'Ekspor data aktual memerlukan autentikasi yang belum tersedia.')
    result=analytics(db,q)
    rows=result['session_rows'] if kind=='sessions' else result['daily_rows'] if kind=='daily' else result['participants']
    df=pd.DataFrame(rows)
    content=df.to_csv(index=False).encode('utf-8-sig')
    return StreamingResponse(BytesIO(content),media_type='text/csv',headers={'Content-Disposition':f'attachment; filename=toba_{kind}.csv'})
