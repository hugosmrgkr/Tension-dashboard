from datetime import date
from sqlalchemy import Date, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base

class DimPartisipan(Base):
    __tablename__ = "dim_partisipan"
    id: Mapped[int] = mapped_column(primary_key=True)
    id_partisipan: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    usia: Mapped[int] = mapped_column(Integer)
    jenis_kelamin: Mapped[str] = mapped_column(String(32))
    bmi: Mapped[float] = mapped_column(Float)
    aktivitas_fisik_hari_per_minggu: Mapped[int] = mapped_column(Integer)
    pola_makan: Mapped[str] = mapped_column(String(50))
    jam_tidur: Mapped[float] = mapped_column(Float)
    tingkat_stres: Mapped[int] = mapped_column(Integer)
    merokok: Mapped[str] = mapped_column(String(12))

class DimTanggal(Base):
    __tablename__ = "dim_tanggal"
    id: Mapped[int] = mapped_column(primary_key=True)
    tanggal: Mapped[date] = mapped_column(Date, unique=True, index=True)
    tahun: Mapped[int] = mapped_column(Integer)
    bulan: Mapped[int] = mapped_column(Integer)
    hari: Mapped[int] = mapped_column(Integer)

class DimKecamatan(Base):
    __tablename__ = "dim_kecamatan"
    id: Mapped[int] = mapped_column(primary_key=True)
    kecamatan: Mapped[str] = mapped_column(String(80), unique=True, index=True)

class FaktaPengukuran(Base):
    __tablename__ = "fact_pengukuran"
    __table_args__ = (UniqueConstraint("partisipan_id", "tanggal_id", name="uq_partisipan_tanggal"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    partisipan_id: Mapped[int] = mapped_column(ForeignKey("dim_partisipan.id"), index=True)
    tanggal_id: Mapped[int] = mapped_column(ForeignKey("dim_tanggal.id"), index=True)
    kecamatan_id: Mapped[int] = mapped_column(ForeignKey("dim_kecamatan.id"), index=True)
    sistolik: Mapped[int] = mapped_column(Integer)
    diastolik: Mapped[int] = mapped_column(Integer)
    status_hipertensi: Mapped[str] = mapped_column(String(40))
    partisipan: Mapped[DimPartisipan] = relationship()
    tanggal_dim: Mapped[DimTanggal] = relationship()
    kecamatan_dim: Mapped[DimKecamatan] = relationship()

class DatasetState(Base):
    __tablename__ = "dataset_state"
    id: Mapped[int] = mapped_column(primary_key=True)
    source_name: Mapped[str] = mapped_column(String(240), default="Dataset demo (sintetis)")
    source_kind: Mapped[str] = mapped_column(String(20), default="demo")
