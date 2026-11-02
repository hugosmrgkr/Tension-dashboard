"""Toba Health Insight API. Demo classification is not a trained ML model."""
from contextlib import asynccontextmanager
from io import BytesIO
import os
import pandas as pd
from fastapi import FastAPI, Depends, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from .db import Base, engine, get_db, SessionLocal
from .models import DatasetState
from .data_utils import buat_data_hipertensi_demo, klasifikasi_tekanan, KELOMPOK_USIA
from .service import validate_frame, replace_data, seed_if_empty, get_frame, filtered, analytics, records, DataValidationError, COLUMNS

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_if_empty(db)
    yield

app = FastAPI(
    title="Toba Health Insight API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8080"], allow_methods=["GET", "POST", "PUT", "DELETE"], allow_headers=["*"])

class FilterParams(BaseModel):
    awal: str | None = None
    akhir: str | None = None
    kecamatan: str | None = None
    jenis_kelamin: str | None = None
    kelompok_usia: str | None = None
    id_partisipan: str | None = None

class Prediction(BaseModel):
    usia: int = Field(35, ge=15, le=64)
    bmi: float = Field(24, ge=10, le=70)
    sistolik: int = Field(128, ge=50, le=260)
    diastolik: int = Field(82, ge=30, le=180)

class Measurement(BaseModel):
    id_partisipan: str = Field(min_length=1, max_length=40)
    tanggal: str
    usia: int = Field(ge=15, le=64)
    jenis_kelamin: str
    kecamatan: str
    bmi: float = Field(ge=10, le=70)
    aktivitas_fisik_hari_per_minggu: int = Field(ge=0, le=7)
    pola_makan: str
    jam_tidur: float = Field(ge=0, le=24)
    tingkat_stres: int = Field(ge=0, le=10)
    merokok: str
    sistolik: int = Field(ge=50, le=260)
    diastolik: int = Field(ge=30, le=180)

# Demo cards from original dashboard, never reported as real model evaluation.
MODEL_DEMO = {
 "is_placeholder": True, "akurasi": 85.3,
 "confusion_matrix": [[112,18],[12,58]],
 "models": [
    {"model":"Logistic Regression", "accuracy":.78,"f1":.74,"auc":.82},
    {"model":"Random Forest", "accuracy":.86,"f1":.84,"auc":.90},
    {"model":"SVM", "accuracy":.81,"f1":.78,"auc":.86},
    {"model":"Naive Bayes", "accuracy":.72,"f1":.68,"auc":.76},
 ], "message": "Ilustrasi dari Streamlit asli — bukan hasil pelatihan model."}

def filtered_data(db, q:FilterParams):
    try:
        return filtered(get_frame(db), **q.model_dump())
    except (TypeError, ValueError) as e:
        raise HTTPException(422, str(e)) from e

@app.get("/health")
def health():
    return {"status":"ok"}

@app.get("/api/meta")
def meta(db: Session=Depends(get_db)):
    df = get_frame(db)
    state = db.get(DatasetState, 1)
    return {"source": state.source_name if state else "Tidak diketahui", "source_kind":state.source_kind if state else "unknown",
        "total_rows":len(df), "min_date": df.tanggal.min().strftime("%Y-%m-%d") if len(df) else None,
        "max_date":df.tanggal.max().strftime("%Y-%m-%d") if len(df) else None,
        "kecamatan":sorted(df.kecamatan.dropna().unique().tolist()), "jenis_kelamin":sorted(df.jenis_kelamin.dropna().unique().tolist()),
        "kelompok_usia":KELOMPOK_USIA, "participants":sorted(df.id_partisipan.dropna().unique().tolist())}

@app.get("/api/analytics")
def get_analytics(q:FilterParams=Depends(), db:Session=Depends(get_db)):
    return analytics(filtered_data(db,q))