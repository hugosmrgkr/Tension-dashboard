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

app = FastAPI(title="Toba Health Insight API", version="1.0.0", lifespan=lifespan)
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

@app.get("/api/measurements")
def measurements(q:FilterParams=Depends(), page:int=Query(1,ge=1), page_size:int=Query(30,ge=1,le=1000), db:Session=Depends(get_db)):
    df=filtered_data(db,q); start=(page-1)*page_size
    return {"total":len(df), "page":page, "page_size":page_size, "rows":records(df.iloc[start:start+page_size])}

@app.get("/api/model/demo")
def demo_model():
    return MODEL_DEMO

@app.post("/api/predict/demo")
def predict_demo(payload:Prediction):
    status=klasifikasi_tekanan(payload.sistolik,payload.diastolik)
    return {"status":status, "is_ml":False, "probability":None,
        "message":"Klasifikasi aturan ambang dari Streamlit asli, bukan model ML/diagnosis medis."}

@app.post("/api/data/upload")
async def upload(file: UploadFile=File(...), db:Session=Depends(get_db)):
    filename=(file.filename or "upload").replace("\\", "/").split("/")[-1]
    if not filename.lower().endswith((".csv",".xlsx")):
        raise HTTPException(422,"Hanya CSV dan XLSX yang didukung")
    content=await file.read(15_000_001)
    if len(content)>15_000_000:
        raise HTTPException(413,"Ukuran file maksimal 15 MB")
    try:
        raw=(pd.read_excel(BytesIO(content)) if filename.lower().endswith(".xlsx") else pd.read_csv(BytesIO(content), encoding="utf-8-sig"))
        count=replace_data(db,raw,filename,"uploaded")
    except (ValueError, TypeError, DataValidationError) as e:
        db.rollback(); raise HTTPException(422,str(e)) from e
    except Exception as e:
        db.rollback(); raise HTTPException(422,"Berkas gagal dibaca/diimpor: " + str(e)) from e
    return {"ok":True,"rows":count,"source":filename}

@app.post("/api/data/reset")
def reset(db:Session=Depends(get_db)):
    count=replace_data(db,buat_data_hipertensi_demo(),"Dataset demo (sintetis)","demo")
    return {"ok":True, "rows":count}

@app.get("/api/data/export")
def export(format:str=Query("csv",pattern="^(csv|xlsx|txt)$"), q:FilterParams=Depends(), db:Session=Depends(get_db)):
    df=filtered_data(db,q).drop(columns=["id"],errors="ignore")
    if format=="txt":
        return PlainTextResponse(f"TOBA HEALTH INSIGHT — RINGKASAN\nJumlah baris: {len(df)}\nJumlah kolom: {len(df.columns)}\nSumber: dashboard\n", headers={"Content-Disposition":"attachment; filename=laporan_ringkas.txt"})
    buff=BytesIO()
    if format=="csv":
        payload=df.to_csv(index=False).encode("utf-8-sig")
        return StreamingResponse(BytesIO(payload),media_type="text/csv", headers={"Content-Disposition":"attachment; filename=data_hipertensi.csv"})
    with pd.ExcelWriter(buff,engine="xlsxwriter") as writer:
        df.to_excel(writer,index=False,sheet_name="Data Partisipan")
    buff.seek(0)
    return StreamingResponse(buff,media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",headers={"Content-Disposition":"attachment; filename=data_hipertensi.xlsx"})

def edit_row(db:Session, payload:Measurement, target_id:int|None):
    current=get_frame(db)
    row=payload.model_dump()
    if target_id is None:
        if "id" in current: row["id"]=int(current.id.max()+1) if len(current) else 1
    else:
        if target_id not in set(current.id.tolist()):
            raise HTTPException(404,"Data pengukuran tidak ditemukan")
        old = current.loc[current.id == target_id].iloc[0]
        row["id"]=target_id
        current=current[current.id!=target_id]
        # Dimension attributes are properties of a participant, not a daily fact.
        # Propagate user edits to the rest of that participant's measurements.
        if row["id_partisipan"] == old["id_partisipan"]:
            fixed = ["usia", "jenis_kelamin", "bmi", "aktivitas_fisik_hari_per_minggu",
                     "pola_makan", "jam_tidur", "tingkat_stres", "merokok"]
            for col in fixed:
                current.loc[current.id_partisipan == row["id_partisipan"], col] = row[col]
    combined=pd.concat([current,pd.DataFrame([row])],ignore_index=True).drop(columns=["id","status_hipertensi"],errors="ignore")
    state=db.get(DatasetState,1)
    try:
        count=replace_data(db,combined,state.source_name if state else "Data edit",state.source_kind if state else "edited")
    except DataValidationError as e:
        db.rollback(); raise HTTPException(422,str(e)) from e
    return {"ok":True,"rows":count}

@app.post("/api/measurements")
def add_measurement(payload:Measurement,db:Session=Depends(get_db)):
    return edit_row(db,payload,None)

@app.put("/api/measurements/{row_id}")
def update_measurement(row_id:int,payload:Measurement,db:Session=Depends(get_db)):
    return edit_row(db,payload,row_id)

@app.delete("/api/measurements/{row_id}")
def delete_measurement(row_id:int,db:Session=Depends(get_db)):
    current=get_frame(db)
    if row_id not in set(current.id.tolist()):
        raise HTTPException(404,"Data pengukuran tidak ditemukan")
    if len(current)<=1:
        raise HTTPException(422,"Dataset tidak boleh kosong")
    state=db.get(DatasetState,1)
    count=replace_data(db,current[current.id!=row_id].drop(columns=["id","status_hipertensi"],errors="ignore"),state.source_name,state.source_kind)
    return {"ok":True,"rows":count}
