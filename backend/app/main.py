"""Toba Health Insight API. Demo classification is not a trained ML model."""
from contextlib import asynccontextmanager
from io import BytesIO
from pathlib import Path
from typing import Literal
import pandas as pd
from fastapi import FastAPI, Depends, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, PlainTextResponse, JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .db import Base, engine, get_db, SessionLocal
from .models import DatasetState, FaktaPengukuran
from .data_utils import buat_data_hipertensi_demo, klasifikasi_tekanan, KELOMPOK_USIA
from .service import replace_data, seed_if_empty, get_frame, filtered, analytics, records, save_measurement, DataValidationError, COLUMNS

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


@app.exception_handler(DataValidationError)
async def validation_error_handler(request, exc):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request, exc):
    return JSONResponse(status_code=409, content={"detail": "Data bertentangan dengan data tersimpan. Muat ulang data dan coba lagi."})

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
def measurements(
    q: FilterParams = Depends(),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=1000),
):
    df = filtered_data(db, q)
    start = (page - 1) * page_size
    return {"rows": records(df.iloc[start:start + page_size], ["id", *COLUMNS]),
            "total": len(df), "page": page, "page_size": page_size}


@app.get("/api/model/demo")
def model_demo():
    return MODEL_DEMO


@app.post("/api/predict/demo")
def predict_demo(values: Prediction):
    return {
        "status": klasifikasi_tekanan(values.sistolik, values.diastolik),
        "is_ml": False,
        "message": "Klasifikasi demo berdasarkan sistolik dan diastolik; usia dan BMI tidak digunakan dalam aturan ini. Bukan prediksi model ML atau diagnosis.",
    }


@app.post("/api/measurements")
def create_measurement(values: Measurement, db: Session = Depends(get_db)):
    return save_measurement(db, values.model_dump())


def require_measurement(db: Session, measurement_id: int):
    measurement = db.get(FaktaPengukuran, measurement_id)
    if measurement is None:
        raise HTTPException(404, "Pengukuran tidak ditemukan")
    return measurement


@app.put("/api/measurements/{measurement_id}")
def update_measurement(measurement_id: int, values: Measurement, db: Session = Depends(get_db)):
    return save_measurement(db, values.model_dump(), require_measurement(db, measurement_id))


@app.delete("/api/measurements/{measurement_id}")
def delete_measurement(measurement_id: int, db: Session = Depends(get_db)):
    db.delete(require_measurement(db, measurement_id))
    db.commit()
    return {"deleted": measurement_id}


@app.post("/api/data/reset")
def reset_data(db: Session = Depends(get_db)):
    rows = replace_data(db, buat_data_hipertensi_demo(), "Dataset demo (sintetis)", "demo")
    return {"rows": rows, "source": "Dataset demo (sintetis)", "source_kind": "demo"}


@app.post("/api/data/upload")
def upload_data(file: UploadFile = File(...), db: Session = Depends(get_db)):
    name = Path((file.filename or "").replace("\\", "/")).name
    suffix = Path(name).suffix.lower()
    if suffix not in {".csv", ".xlsx"}:
        raise HTTPException(422, "Pilih berkas CSV atau XLSX")
    # Bound API uploads too when running without Nginx.
    max_size = 15 * 1024 * 1024
    content = file.file.read(max_size + 1)
    if len(content) > max_size:
        raise HTTPException(413, "Ukuran berkas maksimal 15 MB")
    try:
        raw = (pd.read_csv(BytesIO(content), encoding="utf-8-sig") if suffix == ".csv"
               else pd.read_excel(BytesIO(content), engine="openpyxl"))
    except Exception as exc:
        raise HTTPException(422, "Berkas tidak dapat dibaca sebagai CSV/XLSX yang valid") from exc
    rows = replace_data(db, raw, name, "uploaded")
    return {"rows": rows, "source": name, "source_kind": "uploaded"}


@app.get("/api/data/export")
def export_data(
    q: FilterParams = Depends(),
    db: Session = Depends(get_db),
    format: Literal["csv", "xlsx", "txt"] = "csv",
):
    df = filtered_data(db, q)
    if format == "txt":
        summary = analytics(df)
        state = db.get(DatasetState, 1)
        lines = ["Toba Health Insight — Ringkasan Data",
                 f"Sumber: {state.source_name if state else 'Tidak diketahui'}",
                 "Filter: " + str(q.model_dump(exclude_none=True)),
                 f"Total pengukuran: {len(df)}",
                 f"Total partisipan: {summary.get('total_participants', 0)}"]
        if not summary["empty"]:
            lines.extend([
                f"Rata-rata tekanan darah: {summary['mean_sistolik']}/{summary['mean_diastolik']} mmHg",
                f"Di atas rentang normal: {summary['non_normal']} ({summary['non_normal_percent']}%)",
                "Distribusi berdasarkan rata-rata per partisipan:",
                *[f"- {row['status']}: {row['count']} ({row['percent']}%)" for row in summary["distribution"]],
            ])
        lines.append("Ringkasan deskriptif dataset aktif; bukan diagnosis atau evaluasi model ML.")
        return PlainTextResponse("\n".join(lines) + "\n", headers={
            "Content-Disposition": 'attachment; filename="laporan_ringkas.txt"'})

    exported = df[COLUMNS].copy()
    if not exported.empty:
        exported["tanggal"] = pd.to_datetime(exported["tanggal"]).dt.strftime("%Y-%m-%d")
    if format == "csv":
        content = exported.to_csv(index=False).encode("utf-8-sig")
        media_type = "text/csv; charset=utf-8"
    else:
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter", engine_kwargs={
            "options": {"strings_to_formulas": False, "strings_to_urls": False}
        }) as writer:
            exported.to_excel(writer, index=False, sheet_name="Pengukuran")
        content = buffer.getvalue()
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return StreamingResponse(BytesIO(content), media_type=media_type, headers={
        "Content-Disposition": f'attachment; filename="data_hipertensi.{format}"'})
