"""CP3 Stage 1: read-only FastAPI serving the explicitly loaded CP2 warehouse."""
from contextlib import asynccontextmanager
from datetime import date
from io import BytesIO
import json
import os
from pathlib import Path
from typing import Literal
import pandas as pd
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from .db import Base, engine, SessionLocal, get_db
from .models import SourceState
from . import security
from .analytics_v2 import analytics, frames, metadata_payload, source_summary, EXPORT_FIELDS, AGE_GROUPS


@asynccontextmanager
async def lifespan(app:FastAPI):
    security.validate_runtime_config()  # P2-06: gagal tertutup bila konfigurasi staging/production tidak aman
    # Create missing empty tables only. ETL/seed is never run by the web server.
    Base.metadata.create_all(bind=engine)
    yield


_secure=security.app_env() in security.SECURE_ENVS  # dokumentasi API dimatikan di staging/production
app=FastAPI(title='Toba Health Insight API',version='2.1.0',lifespan=lifespan,
            docs_url=None if _secure else '/api/docs',redoc_url=None if _secure else '/api/redoc',openapi_url=None if _secure else '/api/openapi.json')
app.add_middleware(CORSMiddleware,allow_origins=security.cors_origins(),allow_methods=['GET'],allow_headers=['Authorization','Content-Type'])
app.middleware('http')(security.security_middleware)


@app.exception_handler(SQLAlchemyError)
async def database_unavailable(request,exc):
    return JSONResponse(status_code=503,content={'detail':'Warehouse tidak dapat dibaca. Periksa koneksi PostgreSQL dan skema; tidak ada data contoh yang digunakan sebagai pengganti.'})


@app.get('/health')
@app.get('/api/health')
def health(db:Session=Depends(get_db)):
    db.execute(select(1))
    return {'status':'ok','version':'2.1.0','database':db.bind.dialect.name}


@app.get('/api/meta')
def metadata(db:Session=Depends(get_db)):
    return metadata_payload(db)


def query_args(start_date:date|None=None,end_date:date|None=None,province:str|None=None,education:str|None=None,
               city:str|None=None,gender:str|None=None,occupation:str|None=None,age_group:str|None=None,
               session:Literal['Pagi','Malam']|None=None,respondent_id:str|None=Query(None,max_length=40)):
    if start_date and end_date and start_date>end_date:
        raise HTTPException(422,'Tanggal awal lebih besar dari tanggal akhir')
    if age_group and age_group not in AGE_GROUPS:
        raise HTTPException(422,'Kelompok usia tidak tersedia dalam definisi filter')
    return dict(start_date=start_date.isoformat() if start_date else None,end_date=end_date.isoformat() if end_date else None,
                province=province,city=city,gender=gender,occupation=occupation,education=education,age_group=age_group,session=session,respondent_id=respondent_id)


def require_public_source(db):
    state,summary=source_summary(db)
    if summary['access_restricted']:
        raise HTTPException(403,summary['message'])
    return state


@app.get('/api/analytics')
def get_analytics(q:dict=Depends(query_args),db:Session=Depends(get_db)):
    require_public_source(db)
    return analytics(db,q)


@app.get('/api/quality')
def get_quality(db:Session=Depends(get_db)):
    state=require_public_source(db)
    return {'source_kind':state.source_kind if state else 'empty','quality':json.loads(state.quality_json or '{}') if state else {}}


@app.get('/api/model/baseline')
def baseline_metadata(db:Session=Depends(get_db)):
    from .baseline import load_experiment
    state=db.get(SourceState,1)
    if not state or state.source_kind!='synthetic':
        return dict(available=False,message='Baseline eksperimen hanya tersedia pada DATA SINTETIS / SIMULASI.')
    result=load_experiment(Path(os.getenv('MODEL_DIR','/app/models')))
    if result['available']:
        batch=json.loads(state.quality_json or '{}').get('prepared_content_sha256')
        result['warehouse_batch_match']=(batch==result['provenance']['prepared_content_sha256']) if batch else None
        result['warehouse_match_note']='Kecocokan berdasarkan fingerprint batch ETL, bukan evaluasi ulang model pada filter aktif.'
    return result

@app.get('/api/model/predict-baseline')
def predict_baseline(respondent_id:str=Query(...,min_length=1,max_length=40),asof_date:date|None=None,db:Session=Depends(get_db)):
    from .baseline import predict_naive,load_experiment
    state=db.get(SourceState,1)
    if not state or state.source_kind!='synthetic':raise HTTPException(409,'Baseline demo hanya tersedia pada dataset sintetis.')
    experiment=load_experiment(Path(os.getenv('MODEL_DIR','/app/models')))
    if not experiment['available']:raise HTTPException(409,experiment['message'])
    _,sessions,_=frames(db)
    try:result=predict_naive(sessions,respondent_id,asof_date)
    except LookupError as exc:raise HTTPException(404,str(exc))
    except ValueError as exc:raise HTTPException(422,str(exc))
    return {**result,'artifact_run_id':experiment['run_id'],'target_approved':False}

@app.get('/api/model/comparison')
def model_comparison(db:Session=Depends(get_db)):
    """P2-03: hasil perbandingan algoritma dari artefak terverifikasi (hanya DATA SINTETIS)."""
    from .model_comparison import load_comparison
    state=db.get(SourceState,1)
    if not state or state.source_kind!='synthetic':
        return dict(available=False,message='Perbandingan model hanya tersedia pada DATA SINTETIS / SIMULASI.')
    return load_comparison(Path(os.getenv('MODEL_DIR','/app/models'))/'experiments')


@app.get('/api/model/predict')
def predict_model(respondent_id:str=Query(...,min_length=1,max_length=40),asof_date:date|None=None,db:Session=Depends(get_db)):
    """P2-02: prediksi rerata SBP 7 hari ke depan memakai model terlatih terverifikasi. Bukan diagnosis."""
    from . import model_service as ms
    state=db.get(SourceState,1)
    if not state or state.source_kind!='synthetic':raise HTTPException(409,'Prediksi model hanya tersedia pada dataset sintetis.')
    try:model,info=ms.load_serving_model(Path(os.getenv('MODEL_DIR','/app/models'))/'experiments')
    except ms.ModelUnavailable as exc:raise HTTPException(409,str(exc))
    profiles,sessions,days=frames(db)
    try:return ms.predict(model,info,profiles,days,sessions,respondent_id,asof_date)
    except ms.UnknownRespondent as exc:raise HTTPException(404,str(exc))
    except ms.InsufficientHistory as exc:raise HTTPException(422,str(exc))
    except ms.ModelFailure as exc:raise HTTPException(503,str(exc))


@app.get('/api/data/export/{kind}')
def export(kind:Literal['sessions','daily','participants'],q:dict=Depends(query_args),db:Session=Depends(get_db)):
    require_public_source(db)
    result=analytics(db,q)
    rows=result['session_rows'] if kind=='sessions' else result['daily_rows'] if kind=='daily' else result['participants']
    df=pd.DataFrame(rows,columns=EXPORT_FIELDS[kind])
    # Spreadsheet formula injection protection; raw database values stay untouched.
    def safe_csv(value):
        if isinstance(value,str) and value.lstrip().startswith(('=','+','-','@')):return "'"+value
        if isinstance(value,str) and value.startswith(('\t','\r','\n')):return "'"+value
        return value
    for column in df.columns:df[column]=df[column].map(safe_csv)
    content=df.to_csv(index=False).encode('utf-8-sig')
    return StreamingResponse(BytesIO(content),media_type='text/csv',headers={'Content-Disposition':f'attachment; filename=toba_{kind}.csv'})
