"""Database ETL and dashboard calculations kept consistent with the Streamlit source."""
from datetime import date
import io
import numpy as np
import pandas as pd
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from .data_utils import buat_data_hipertensi_demo, klasifikasi_tekanan, ringkas_per_partisipan, tambah_kelompok_usia, STATUS_URUT, KELOMPOK_USIA
from .models import DatasetState, DimPartisipan, DimTanggal, DimKecamatan, FaktaPengukuran

COLUMNS = ["id_partisipan", "tanggal", "usia", "jenis_kelamin", "kecamatan", "bmi", "aktivitas_fisik_hari_per_minggu", "pola_makan", "jam_tidur", "tingkat_stres", "merokok", "sistolik", "diastolik", "status_hipertensi"]
# The legacy CSV minimum did not require these two fields, but the dashboard uses them.
REQUIRED = ["tanggal", "kecamatan", "jenis_kelamin", "usia", "bmi", "aktivitas_fisik_hari_per_minggu", "pola_makan", "jam_tidur", "merokok", "sistolik", "diastolik"]
DEFAULTS = {"tingkat_stres": 5}
P_STATE = ["Normal", "Pra-hipertensi", "Hipertensi Tahap 1", "Hipertensi Tahap 2"]
COLORS = ["#22b36b", "#fbbf3a", "#ef5b5b", "#d6232f"]

class DataValidationError(ValueError):
    pass

def validate_frame(raw: pd.DataFrame) -> pd.DataFrame:
    """Validate structured data, reject duplicates and inconsistent respondent dimensions.

    Status is deliberately recalculated from the original threshold logic; user-provided
    labels are not used. This is a dashboard categorization, not a clinical diagnosis.
    """
    df = raw.copy()
    missing = [col for col in REQUIRED if col not in df.columns]
    if missing:
        raise DataValidationError("Kolom wajib belum tersedia: " + ", ".join(missing))
    if df.empty or len(df) > 250_000:
        raise DataValidationError("Dataset harus berisi 1–250.000 baris")
    for col, default in DEFAULTS.items():
        if col not in df:
            df[col] = default
    if "id_partisipan" not in df:
        # Matches original fallback of generating a unique ID per measurement.
        df["id_partisipan"] = [f"P{i:06d}" for i in range(1, len(df) + 1)]
    for col in ("tanggal",):
        df[col] = pd.to_datetime(df[col], errors="coerce").dt.date
    numeric = ("usia", "bmi", "aktivitas_fisik_hari_per_minggu", "jam_tidur", "tingkat_stres", "sistolik", "diastolik")
    for col in numeric:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in ("id_partisipan", "jenis_kelamin", "kecamatan", "pola_makan", "merokok"):
        df[col] = df[col].astype("string").str.strip()
        df.loc[df[col].isin(["", "nan", "None"]), col] = pd.NA
    if df[["id_partisipan", "tanggal", *numeric, "jenis_kelamin", "kecamatan", "pola_makan", "merokok"]].isna().any().any():
        raise DataValidationError("Ada nilai wajib kosong atau tipe data tidak valid")
    for col, low, high in [("usia", 15, 64), ("bmi", 10, 70), ("aktivitas_fisik_hari_per_minggu", 0, 7), ("jam_tidur", 0, 24), ("tingkat_stres", 0, 10), ("sistolik", 50, 260), ("diastolik", 30, 180)]:
        if ((df[col] < low) | (df[col] > high)).any():
            raise DataValidationError(f"{col} harus dalam rentang {low}–{high}")
    for col in ("usia", "aktivitas_fisik_hari_per_minggu", "tingkat_stres", "sistolik", "diastolik"):
        if (df[col] % 1 != 0).any():
            raise DataValidationError(f"{col} harus bilangan bulat")
        df[col] = df[col].astype(int)
    if df.duplicated(subset=["id_partisipan", "tanggal"]).any():
        raise DataValidationError("Terdapat ID partisipan dan tanggal yang sama (duplikat)")
    for col in ("usia", "jenis_kelamin", "bmi", "aktivitas_fisik_hari_per_minggu", "pola_makan", "jam_tidur", "tingkat_stres", "merokok"):
        if (df.groupby("id_partisipan")[col].nunique() > 1).any():
            raise DataValidationError(f"Nilai {col} harus konsisten untuk setiap id_partisipan")
    for col in ("id_partisipan", "jenis_kelamin", "kecamatan", "pola_makan", "merokok"):
        if df[col].str.len().max() > (40 if col == "id_partisipan" else 80):
            raise DataValidationError(f"Teks pada {col} terlalu panjang")
    df["status_hipertensi"] = [klasifikasi_tekanan(s, d) for s, d in zip(df.sistolik, df.diastolik)]
    return df[COLUMNS].reset_index(drop=True)

def replace_data(db: Session, raw: pd.DataFrame, name: str, kind: str) -> int:
    df = validate_frame(raw)
    # Dimension rows are independent of facts; delete in FK order.
    for model in (FaktaPengukuran, DimPartisipan, DimTanggal, DimKecamatan):
        db.execute(delete(model))
    participants = {}
    for item in df.drop_duplicates("id_partisipan").to_dict("records"):
        obj = DimPartisipan(**{key: item[key] for key in ["id_partisipan", "usia", "jenis_kelamin", "bmi", "aktivitas_fisik_hari_per_minggu", "pola_makan", "jam_tidur", "tingkat_stres", "merokok"]})
        db.add(obj)
        participants[item["id_partisipan"]] = obj
    dates = {}
    for day in df.tanggal.unique():
        d = day if isinstance(day, date) else pd.Timestamp(day).date()
        obj = DimTanggal(tanggal=d, tahun=d.year, bulan=d.month, hari=d.day)
        db.add(obj)
        dates[d] = obj
    locations = {}
    for name_loc in df.kecamatan.unique():
        obj = DimKecamatan(kecamatan=str(name_loc)); db.add(obj); locations[str(name_loc)] = obj
    db.flush()
    db.add_all([FaktaPengukuran(
        partisipan_id=participants[row.id_partisipan].id, tanggal_id=dates[row.tanggal].id,
        kecamatan_id=locations[row.kecamatan].id, sistolik=int(row.sistolik), diastolik=int(row.diastolik),
        status_hipertensi=row.status_hipertensi,
    ) for row in df.itertuples(index=False)])
    state = db.get(DatasetState, 1)
    if state is None:
        state = DatasetState(id=1); db.add(state)
    state.source_name = name[:240]
    state.source_kind = kind
    db.commit()
    return len(df)

def seed_if_empty(db: Session):
    if db.scalar(select(DatasetState.id).limit(1)) is None:
        replace_data(db, buat_data_hipertensi_demo(), "Dataset demo (sintetis)", "demo")

def get_frame(db: Session) -> pd.DataFrame:
    q = select(FaktaPengukuran.id, DimPartisipan.id_partisipan, DimTanggal.tanggal,
        DimPartisipan.usia, DimPartisipan.jenis_kelamin, DimKecamatan.kecamatan,
        DimPartisipan.bmi, DimPartisipan.aktivitas_fisik_hari_per_minggu,
        DimPartisipan.pola_makan, DimPartisipan.jam_tidur, DimPartisipan.tingkat_stres,
        DimPartisipan.merokok, FaktaPengukuran.sistolik, FaktaPengukuran.diastolik,
        FaktaPengukuran.status_hipertensi).join(DimPartisipan, FaktaPengukuran.partisipan_id == DimPartisipan.id).join(DimTanggal, FaktaPengukuran.tanggal_id == DimTanggal.id).join(DimKecamatan, FaktaPengukuran.kecamatan_id == DimKecamatan.id).order_by(DimTanggal.tanggal, DimPartisipan.id_partisipan)
    rows = db.execute(q).mappings().all()
    if not rows:
        return pd.DataFrame(columns=["id", *COLUMNS])
    df = pd.DataFrame([dict(row) for row in rows]); df["tanggal"] = pd.to_datetime(df["tanggal"])
    return df

def filtered(df, awal=None, akhir=None, kecamatan=None, jenis_kelamin=None, kelompok_usia=None, id_partisipan=None):
    d = df.copy()
    if d.empty:
        return d
    if awal:
        d = d[d["tanggal"] >= pd.Timestamp(awal)]
    if akhir:
        d = d[d["tanggal"] <= pd.Timestamp(akhir)]
    if kecamatan and kecamatan != "Semua Kecamatan":
        d = d[d.kecamatan == kecamatan]
    if jenis_kelamin and jenis_kelamin != "Semua":
        d = d[d.jenis_kelamin == jenis_kelamin]
    if kelompok_usia and kelompok_usia != "Semua":
        d = tambah_kelompok_usia(d)
        d = d[d.kelompok_usia.astype(str) == kelompok_usia]
    if id_partisipan:
        d = d[d.id_partisipan.str.contains(id_partisipan, case=False, regex=False, na=False)]
    return d.copy()

def safe_float(x, digits=3):
    return round(float(x), digits) if pd.notna(x) and np.isfinite(x) else None

def records(df, cols=None, limit=None):
    if cols is not None:
        df = df[cols]
    if limit is not None:
        df = df.head(limit)
    return [{k: (v.strftime('%Y-%m-%d') if isinstance(v, (date, pd.Timestamp)) else
                  (None if pd.isna(v) else (v.item() if hasattr(v, 'item') else v)))
             for k, v in row.items()} for row in df.to_dict('records')]

def analytics(df):
    if df.empty:
        return {"empty": True, "total_rows": 0, "participants": [], "trends": [], "distribution": [], "by_age": [], "correlations": [], "risk_factors": [], "risk_charts": {}}
    p = ringkas_per_partisipan(df)
    dist = p.status_hipertensi.value_counts().reindex(P_STATE, fill_value=0)
    data = df.groupby("tanggal")[["sistolik", "diastolik"]].agg(["mean", "min", "max"]).reset_index()
    data.columns = ["tanggal", "sistolik_mean", "sistolik_min", "sistolik_max", "diastolik_mean", "diastolik_min", "diastolik_max"]
    peta = {"Normal": "Normal", "Pra-hipertensi": "Pra-hipertensi", "Hipertensi Tahap 1": "Hipertensi", "Hipertensi Tahap 2": "Hipertensi"}
    by_age = p.assign(grup=p.status_hipertensi.map(peta)).groupby(["kelompok_usia", "grup"], observed=False).size().unstack(fill_value=0).reindex(index=KELOMPOK_USIA, columns=["Normal", "Pra-hipertensi", "Hipertensi"], fill_value=0)
    # Like original Streamlit: use participant-level means for correlations.
    vectors = {"BMI": p.bmi, "Aktivitas Fisik": p.aktivitas_fisik_hari_per_minggu,
      "Pola Makan Tinggi Garam": (p.pola_makan == "Tinggi Garam").astype(int),
      "Durasi Tidur": p.jam_tidur, "Tingkat Stres": p.tingkat_stres,
      "Merokok": (p.merokok == "Ya").astype(int)}
    corr = [{"feature": label, "sistolik": safe_float(pd.Series(values).corr(p.sistolik)) or 0, "diastolik": safe_float(pd.Series(values).corr(p.diastolik)) or 0} for label, values in vectors.items()] if len(p) > 1 else [{"feature": label, "sistolik": 0, "diastolik": 0} for label in vectors]
    risks = {"Pola makan tinggi garam": (p.pola_makan == "Tinggi Garam").mean(),
        "Kurang aktivitas fisik": (p.aktivitas_fisik_hari_per_minggu < 3).mean(),
        "Merokok": (p.merokok == "Ya").mean(), "BMI berlebih": (p.bmi >= 25).mean(),
        "Stres tinggi": (p.tingkat_stres >= 7).mean()}
    status_non_normal = int((p.status_hipertensi != "Normal").sum())
    risks_order = sorted(risks.items(), key=lambda kv: kv[1], reverse=True)
    faktor = {
        "bmi_box": records(p, ["id_partisipan", "status_hipertensi", "bmi"]),
        "aktivitas": records(df.groupby("aktivitas_fisik_hari_per_minggu", as_index=False).sistolik.mean()),
        "pola_makan": records(df.groupby("pola_makan", as_index=False).sistolik.mean()),
        "merokok_box": records(p, ["id_partisipan", "merokok", "sistolik"]),
        "tidur_scatter": records(p, ["id_partisipan", "jam_tidur", "diastolik", "status_hipertensi"]),
    }
    return {
        "empty": False, "total_rows": len(df), "total_participants": len(p), "days": int(df.tanggal.nunique()),
        "non_normal": status_non_normal, "non_normal_percent": safe_float(status_non_normal / len(p) * 100, 1),
        "mean_sistolik": safe_float(df.sistolik.mean(), 1), "mean_diastolik": safe_float(df.diastolik.mean(), 1),
        "mean_usia": safe_float(p.usia.mean(), 1), "mean_bmi": safe_float(p.bmi.mean(), 1),
        "mean_aktivitas": safe_float(p.aktivitas_fisik_hari_per_minggu.mean(), 1), "mean_tidur": safe_float(p.jam_tidur.mean(), 1),
        "distribution": [{"status": x, "count": int(dist[x]), "percent": safe_float(100 * dist[x] / len(p), 1), "color": COLORS[i]} for i,x in enumerate(P_STATE)],
        "by_age": [{"age": k, **{col:int(by_age.loc[k,col]) for col in by_age.columns}} for k in by_age.index],
        "correlations": corr,
        "risk_factors": [{"label": k, "percent": safe_float(v * 100, 1)} for k,v in risks_order],
        "trends": records(data), "participants": records(p.drop(columns=["kelompok_usia"]), limit=2000),
        "samples": records(p[["id_partisipan", "usia", "jenis_kelamin", "kecamatan", "status_hipertensi"]], limit=5),
        "risk_charts": faktor,
    }
