"""Komponen UI dan halaman dashboard Toba Health Insight.

Berisi: CSS tema, ikon SVG, ilustrasi sidebar, serta fungsi render tiap halaman.
app.py hanya mengurus konfigurasi, sidebar, header, dan routing halaman.
"""
from __future__ import annotations

from io import BytesIO

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from data_utils import (
    KELOMPOK_USIA,
    STATUS_URUT,
    ringkas_per_partisipan,
    tambah_kelompok_usia,
)

# ==================================================
# Palet warna (disamakan dengan desain)
# ==================================================
BIRU = "#2f6fe0"
ORANYE = "#f59e0b"
HIJAU = "#22b36b"
KUNING = "#fbbf3a"
MERAH = "#ef5b5b"
MERAH_TUA = "#d6232f"
NAVY = "#15264b"
ABU_TEKS = "#5b6b88"
WARNA_STATUS = [HIJAU, KUNING, MERAH, MERAH_TUA]

BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]

# Angka contoh untuk bagian model (belum ada model terlatih).
# Ganti dengan hasil evaluasi model sebenarnya jika sudah tersedia.
MODEL_DEMO = {
    "akurasi": 85.3,
    "konfusi": [[112, 18], [12, 58]],  # baris = prediksi, kolom = aktual
    "performa": {
        "Logistic<br>Regression": 0.78,
        "Random<br>Forest": 0.86,
        "SVM": 0.81,
        "Naive<br>Bayes": 0.72,
    },
}

KOLOM_MINIMUM = [
    "tanggal", "kecamatan", "jenis_kelamin", "usia", "bmi",
    "aktivitas_fisik_hari_per_minggu", "pola_makan", "jam_tidur",
    "merokok", "sistolik", "diastolik", "status_hipertensi",
]

INFO_HALAMAN = {
    "Dashboard": (
        "Dashboard",
        "Ringkasan data tekanan darah dan kejadian hipertensi pada masyarakat usia produktif<br>di Kabupaten Toba",
    ),
    "Data Partisipan": ("Data Partisipan", "Seluruh data pengukuran tekanan darah partisipan."),
    "Analisis Faktor Risiko": (
        "Analisis Faktor Risiko",
        "Eksplorasi deskriptif faktor risiko. Hubungan statistik bukan bukti sebab-akibat.",
    ),
    "Tren Tekanan Darah": ("Tren Tekanan Darah", "Pergerakan harian rata-rata dan rentang tekanan darah."),
    "Prediksi Hipertensi": ("Prediksi Hipertensi", "Alur input dan keluaran klasifikasi untuk dataset final."),
    "Evaluasi Model": ("Evaluasi Model", "Perbandingan performa model klasifikasi."),
    "Laporan & Ringkasan": ("Laporan & Ringkasan", "Ringkasan data yang sedang dianalisis."),
    "Kelola Data": ("Kelola Data", "Sumber data, penyuntingan, dan ekspor."),
}


# ==================================================
# Utilitas dasar
# ==================================================
def h(teks: str) -> str:
    """Rapatkan HTML jadi satu baris supaya tidak dibaca sebagai blok kode markdown."""
    return "".join(baris.strip() for baris in teks.splitlines())


def fmt(x: float, desimal: int = 1) -> str:
    """Format angka gaya Indonesia (koma desimal)."""
    return f"{x:.{desimal}f}".replace(".", ",")


def tgl_id(t, tahun: bool = True) -> str:
    return f"{t.day:02d} {BULAN[t.month - 1]}" + (f" {t.year}" if tahun else "")


_IKON = {
    "users": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    "user": '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
    "heart-pulse": '<path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/><path d="M3.22 12H9.5l.5-1 2 4.5 2-7 1.5 3.5h5.27"/>',
    "activity": '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>',
    "alert": '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
    "alert-circle": '<circle cx="12" cy="12" r="10"/><path d="M12 8v4"/><path d="M12 16h.01"/>',
    "calendar": '<rect width="18" height="18" x="3" y="4" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
    "pin": '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>',
    "filter": '<polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>',
    "gauge": '<path d="m12 14 4-4"/><path d="M3.34 19a10 10 0 1 1 17.32 0"/>',
    "zap": '<path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/>',
    "moon": '<path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>',
    "refresh": '<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/>',
    "chevron": '<path d="m6 9 6 6 6-6"/>',
    "bars": '<line x1="12" x2="12" y1="20" y2="10"/><line x1="18" x2="18" y1="20" y2="4"/><line x1="6" x2="6" y1="20" y2="16"/>',
    "target": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
    "table-user": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="10" r="3"/><path d="M7 20.66V19a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v1.66"/>',
    "database": '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14a9 3 0 0 0 18 0V5"/><path d="M3 12a9 3 0 0 0 18 0"/>',
    "arrow": '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
}


def ikon(nama: str, ukuran: int = 18, warna: str = "currentColor", tebal: float = 2) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{ukuran}" height="{ukuran}" '
        f'viewBox="0 0 24 24" fill="none" stroke="{warna}" stroke-width="{tebal}" '
        f'stroke-linecap="round" stroke-linejoin="round" style="flex:none">{_IKON[nama]}</svg>'
    )


SVG_LOGO = (
    '<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="1.7" '
    'stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z" fill="#2f6fe0" stroke="#7fb0ff"/>'
    '<path d="M3.22 12H9.5l.5-1 2 4.5 2-7 1.5 3.5h5.27"/></svg>'
)

SVG_ALAM = (
    '<svg viewBox="0 0 252 170" width="252" height="170" xmlns="http://www.w3.org/2000/svg" style="display:block">'
    '<defs>'
    '<linearGradient id="langit" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0b2250" stop-opacity="0"/><stop offset="1" stop-color="#27609f"/></linearGradient>'
    '<linearGradient id="danau" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1c4b86"/><stop offset="1" stop-color="#0c2656"/></linearGradient>'
    '</defs>'
    '<rect width="252" height="170" fill="url(#langit)"/>'
    '<path d="M0 100 L34 66 L58 84 L102 38 L138 80 L176 52 L214 84 L252 62 L252 170 L0 170Z" fill="#2a5d9b" opacity=".75"/>'
    '<path d="M0 118 L48 82 L86 108 L132 72 L186 112 L226 92 L252 104 L252 170 L0 170Z" fill="#1a447e"/>'
    '<path d="M0 132 L40 112 L80 128 L128 106 L170 130 L210 118 L252 130 L252 170 L0 170Z" fill="#12356a"/>'
    '<rect y="132" width="252" height="38" fill="url(#danau)"/>'
    '<g stroke="#5b95d6" stroke-width="1.2" opacity=".45" stroke-linecap="round">'
    '<path d="M18 142h54M96 148h72M190 141h46M44 156h60M140 160h80"/></g>'
    '<g fill="#08183a"><path d="M148 140h40l-6 7h-28z"/><path d="M160 140l8-10h12l5 10z"/><rect x="167" y="124" width="1.6" height="8"/></g>'
    '</svg>'
)


def html_brand() -> str:
    return h(f"""
    <div class="brand">
      <div class="brand-logo">{SVG_LOGO}</div>
      <div>
        <div class="brand-name">Toba Health Insight</div>
        <div class="brand-tag">Sehat Hari Ini, Masa Depan Lebih Baik</div>
      </div>
    </div>
    """)


def html_sidebar_bawah() -> str:
    return h(f"""
    <div class="side-bottom">
      <div class="side-note">
        <div class="side-note-ico">{ikon("user", 14, "#ffffff")}</div>
        <div>Analisis Faktor Risiko dan Prediksi Hipertensi pada Masyarakat Usia Produktif di Kabupaten Toba</div>
      </div>
      {SVG_ALAM}
    </div>
    """)


def judul_kartu(teks: str, nama_ikon: str | None = None) -> str:
    ico = ikon(nama_ikon, 16, BIRU) if nama_ikon else ""
    return f'<div class="ct">{ico}<span>{teks}</span></div>'


# ==================================================
# CSS tema
# ==================================================
GAYA_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

.stApp, .stApp p, .stApp label, .stApp div, .stApp button, .stApp input, .stApp textarea, .stApp table {
    font-family: 'Inter', 'Segoe UI', Roboto, sans-serif;
}
.stApp { background: #eef3fa; }
header[data-testid="stHeader"] { display: none; }
#MainMenu, footer { visibility: hidden; }
.block-container { max-width: 1640px; padding: 1.1rem 1.5rem .8rem; }
.stApp [data-testid="stVerticalBlock"] { gap: .8rem; min-width: 0; }
.stApp [data-testid="stHorizontalBlock"] { min-width: 0; }
.stApp [data-testid="stColumn"] { min-width: 0; overflow: hidden; }

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] {
    width: 252px !important; min-width: 252px !important; max-width: 252px !important;
    background: linear-gradient(180deg, #0f2a5e 0%, #0b2250 55%, #081b40 100%);
    border-right: 0;
}
section[data-testid="stSidebar"] > div { width: 252px !important; }
[data-testid="stSidebarHeader"], [data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapsedControl"] { display: none !important; }
[data-testid="stSidebarUserContent"] { padding: 1.2rem .85rem 0 !important; }
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: .25rem; }

.brand { display: flex; align-items: center; gap: .65rem; padding: .1rem .35rem 1.2rem; }
.brand-logo { flex: none; display: flex; }
.brand-name { color: #fff; font-weight: 800; font-size: .98rem; line-height: 1.15; }
.brand-tag { color: #9db6e0; font-size: .6rem; line-height: 1.3; margin-top: 3px; }

[class*="st-key-navoff_"] button, [class*="st-key-navon_"] button {
    width: 100%; justify-content: flex-start; gap: .8rem; min-height: 40px;
    padding: .35rem .85rem; border: 0; border-radius: 8px; box-shadow: none;
    background: transparent; font-size: .84rem; font-weight: 500;
}
[class*="st-key-navoff_"] button, [class*="st-key-navoff_"] button * { color: #d5e1f8 !important; }
[class*="st-key-navoff_"] button:hover { background: rgba(255,255,255,.08); }
[class*="st-key-navon_"] button { background: #2f6fe0; font-weight: 600; }
[class*="st-key-navon_"] button, [class*="st-key-navon_"] button * { color: #fff !important; }
[class*="st-key-nav"] button p { font-size: .84rem; }

.side-bottom { position: relative; width: 100%; margin-top: 2.2rem; pointer-events: none; }
.side-note { display: flex; gap: .55rem; align-items: flex-start; padding: 0 1rem .8rem;
    color: #c4d4f0; font-size: .62rem; line-height: 1.45; }
.side-note-ico { flex: none; width: 24px; height: 24px; border-radius: 50%; background: #2f6fe0;
    display: flex; align-items: center; justify-content: center; }
.side-bottom svg { display: block; width: 100%; max-width: 252px; height: auto; }

/* ---------- Header ---------- */
.page-title { font-size: 1.75rem; font-weight: 800; color: #15264b; line-height: 1.15; }
.page-desc { font-size: .8rem; color: #5b6b88; margin-top: .3rem; line-height: 1.45; }
.chip-user { display: flex; align-items: center; justify-content: center; gap: .5rem; height: 40px;
    background: #fff; border: 1px solid #dde5f2; border-radius: 10px; font-size: .84rem; font-weight: 600; color: #15264b; }
.avatar { width: 26px; height: 26px; border-radius: 50%; background: #15264b; display: flex;
    align-items: center; justify-content: center; }
.pill-date { display: flex; align-items: center; gap: .5rem; width: fit-content; margin-left: auto;
    background: #fff; border: 1px solid #dde5f2; border-radius: 10px; padding: .5rem .85rem;
    font-size: .78rem; font-weight: 500; color: #33425f; margin-top: .55rem; }

/* ---------- Kartu ---------- */
[class*="st-key-card"] { background: #fff; border: 1px solid #e4ebf6; border-radius: 14px;
    padding: .85rem 1rem .75rem; box-shadow: 0 2px 10px rgba(30,64,120,.06);
    min-width: 0; overflow: hidden; }
[class*="st-key-card"] [data-testid="stPlotlyChart"],
[class*="st-key-card"] .js-plotly-plot { max-width: 100%; overflow: hidden; }
.ct { display: flex; align-items: center; gap: .5rem; font-weight: 700; font-size: .9rem; color: #15264b; margin: 0 0 .25rem; }

.kpi { display: flex; align-items: center; gap: .9rem; border-radius: 14px; padding: .95rem 1.1rem;
    min-height: 104px; border: 1px solid; box-shadow: 0 2px 10px rgba(30,64,120,.05); }
.kpi-ico { width: 46px; height: 46px; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex: none; }
.kpi-label { font-size: .78rem; font-weight: 600; color: #33425f; }
.kpi-value { font-size: 1.95rem; font-weight: 800; color: #15264b; line-height: 1.15; }
.kpi-value small { font-size: .75rem; font-weight: 500; color: #5b6b88; margin-left: .3rem; }
.kpi-pct { font-size: .75rem; font-weight: 500; color: #e03b3b; margin-left: .25rem; }
.kpi-sub { font-size: .7rem; color: #6a7a95; margin-top: 2px; }
.kpi-biru { background: #e6f0ff; border-color: #cfe0fb; } .kpi-biru .kpi-ico { background: #cfe0fb; }
.kpi-hijau { background: #e4f6ed; border-color: #c8ebd9; } .kpi-hijau .kpi-ico { background: #c4ead6; }
.kpi-merah { background: #fde8e8; border-color: #f8cccc; } .kpi-merah .kpi-ico { background: #f8c4c4; }
.kpi-ungu { background: #ece9fb; border-color: #d9d3f6; } .kpi-ungu .kpi-ico { background: #d8d1f6; }

/* ---------- Input ---------- */
.stApp label p { font-size: .74rem; font-weight: 600; color: #33425f; }
.stApp div[data-baseweb="select"] > div, .stApp div[data-baseweb="input"] > div,
.stApp [data-testid="stDateInput"] div[data-baseweb="input"] {
    min-height: 34px; width: 100%; max-width: 100%; border-radius: 8px; font-size: .8rem;
    background: #fff; border-color: #dde5f2; }
.stApp input, .stApp textarea { max-width: 100%; box-sizing: border-box; }
.stApp [data-testid="stSelectbox"] { margin-bottom: 0; }
[class*="st-key-card_filter"] [data-testid="stVerticalBlock"] { gap: .55rem; }

/* ---------- Panel kanan ---------- */
.stat { display: flex; justify-content: space-between; align-items: center; padding: .5rem 0;
    border-bottom: 1px solid #eef2f8; font-size: .76rem; color: #33425f; }
.stat:last-child { border-bottom: 0; }
.stat span { display: flex; align-items: center; gap: .5rem; color: #5b6b88; }
.stat b { color: #15264b; font-weight: 700; }
.risk { background: #fdeaea; border: 1px solid #f8d0d0; border-radius: 14px; padding: .85rem 1rem; }
.risk-title { display: flex; align-items: center; gap: .45rem; font-weight: 700; font-size: .8rem; color: #c62828; margin-bottom: .45rem; }
.risk-row { display: flex; justify-content: space-between; font-size: .74rem; color: #c0392b; padding: .22rem 0; }
.risk-row b { color: #d32f2f; font-weight: 700; }

/* ---------- Donut legend ---------- */
.leg-row { display: flex; align-items: center; gap: .6rem; padding: .62rem 0; font-size: .8rem; color: #33425f; }
.leg-dot { width: 12px; height: 12px; border-radius: 3px; flex: none; }
.leg-name { flex: 1; font-weight: 500; }
.leg-val { font-weight: 700; color: #15264b; font-size: .78rem; }
.leg-val span { font-weight: 500; color: #5b6b88; }

/* ---------- Matriks konfusi ---------- */
.kf-title { text-align: center; font-weight: 700; font-size: .78rem; color: #15264b; margin: .2rem 0 .4rem; }
.kf { border-collapse: separate; border-spacing: 3px; width: 100%; font-size: .66rem; text-align: center; }
.kf th { font-weight: 600; color: #33425f; padding: .25rem .2rem; }
.kf td { background: #eef3fb; border-radius: 5px; font-weight: 700; font-size: .9rem; color: #15264b; padding: .85rem .2rem; }
.kf td.panas { background: #fde4e4; color: #d32f2f; }
.kf td.aman { background: #e8f4ee; }
.kf .vert { writing-mode: vertical-rl; transform: rotate(180deg); font-size: .62rem; }

/* ---------- Tabel contoh ---------- */
.tbl { width: 100%; table-layout: fixed; border-collapse: collapse; font-size: .68rem; }
.tbl th { text-align: left; color: #5b6b88; font-weight: 600; padding: .4rem .25rem; border-bottom: 1px solid #e4ebf6; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.tbl td { padding: .45rem .25rem; border-bottom: 1px solid #eef2f8; color: #2a3856; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.st-n { color: #16a265; font-weight: 600; } .st-p { color: #d98e04; font-weight: 600; } .st-h { color: #e03b3b; font-weight: 600; }
[class*="st-key-lihat_semua"] { display: flex; justify-content: flex-end; }
[class*="st-key-lihat_semua"] button { background: transparent; border: 0; box-shadow: none; padding: 0;
    min-height: 0; color: #2f6fe0; font-weight: 600; }
[class*="st-key-lihat_semua"] button * { color: #2f6fe0 !important; font-size: .76rem; }

/* ---------- Footer ---------- */
.foot { display: flex; justify-content: space-between; align-items: center; font-size: .68rem; color: #6a7a95; padding: .2rem .2rem 0; }
.foot span { display: flex; align-items: center; gap: .4rem; }
@media (max-width: 1100px) {
    .block-container { padding-left: .85rem; padding-right: .85rem; }
    .page-title { font-size: 1.45rem; }
    .kpi { padding: .75rem; gap: .55rem; }
    .kpi-value { font-size: 1.5rem; }
}
@media (max-width: 800px) {
    section[data-testid="stSidebar"] { width: 220px !important; min-width: 220px !important; }
    section[data-testid="stSidebar"] > div { width: 220px !important; }
    .side-bottom { margin-top: 1rem; }
    .foot { flex-direction: column; align-items: flex-start; gap: .4rem; }
}
"""


# ==================================================
# Grafik
# ==================================================
def _dasar(fig: go.Figure, tinggi: int, kiri=8, kanan=8, atas=8, bawah=8) -> go.Figure:
    fig.update_layout(
        height=tinggi,
        margin=dict(l=kiri, r=kanan, t=atas, b=bawah),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", size=11, color=ABU_TEKS),
        hoverlabel=dict(bgcolor="#15264b", font=dict(color="white", size=12)),
    )
    fig.update_xaxes(showline=True, linecolor="#dfe6f1", gridcolor="#edf1f7", zeroline=False)
    fig.update_yaxes(showline=False, gridcolor="#edf1f7", zeroline=False)
    return fig


def tampil(fig: go.Figure, key: str) -> None:
    st.plotly_chart(
        fig, use_container_width=True, key=key,
        config={"displayModeBar": False, "responsive": True},
    )


def fig_tren(df: pd.DataFrame, pilih: str) -> go.Figure:
    d = df if pilih == "Semua Partisipan" else df[df["id_partisipan"] == pilih]
    t = d.groupby("tanggal")[["sistolik", "diastolik"]].mean().reset_index()
    fig = go.Figure()
    for nama, warna in [("sistolik", BIRU), ("diastolik", ORANYE)]:
        fig.add_trace(go.Scatter(
            x=t["tanggal"], y=t[nama], mode="lines+markers", name=nama.capitalize(),
            line=dict(color=warna, width=2), marker=dict(size=5, color=warna),
            hovertemplate="%{x|%d %b}: %{y:.0f} mmHg<extra>" + nama.capitalize() + "</extra>",
        ))
    idx = [i for i in range(len(t)) if i == 0 or (i + 1) % 5 == 0]
    lo = min(90, int(t[["sistolik", "diastolik"]].min().min()) - 5)
    hi = max(150, int(t[["sistolik", "diastolik"]].max().max()) + 5)
    _dasar(fig, 225, kiri=4, atas=26, bawah=4)
    fig.update_layout(
        legend=dict(orientation="h", x=0.0, y=1.2, font=dict(size=10)),
        yaxis=dict(range=[lo, hi], tick0=90, dtick=20, title=dict(text="Tekanan Darah (mmHg)", font=dict(size=10))),
        xaxis=dict(
            tickvals=[t["tanggal"].iloc[i] for i in idx],
            ticktext=[f"{t['tanggal'].iloc[i].day} {BULAN[t['tanggal'].iloc[i].month - 1]}" for i in idx],
            tickfont=dict(size=10),
        ),
    )
    return fig


def fig_donut_status(p: pd.DataFrame) -> go.Figure:
    dist = p["status_hipertensi"].value_counts().reindex(STATUS_URUT, fill_value=0)
    fig = go.Figure(go.Pie(
        labels=dist.index, values=dist.values, hole=0.66, sort=False, direction="clockwise",
        marker=dict(colors=WARNA_STATUS, line=dict(color="white", width=2)),
        textinfo="none", hovertemplate="%{label}: %{value} partisipan<extra></extra>",
    ))
    _dasar(fig, 215, 4, 4, 4, 4)
    fig.update_layout(
        showlegend=False,
        annotations=[dict(
            text=f"<span style='font-size:22px;color:{NAVY}'><b>{len(p)}</b></span><br>Partisipan",
            showarrow=False, font=dict(size=11, color=ABU_TEKS),
        )],
    )
    return fig


def html_legenda_status(p: pd.DataFrame) -> str:
    dist = p["status_hipertensi"].value_counts().reindex(STATUS_URUT, fill_value=0)
    total = max(len(p), 1)
    baris = "".join(
        f'<div class="leg-row"><div class="leg-dot" style="background:{w}"></div>'
        f'<div class="leg-name">{n}</div>'
        f'<div class="leg-val">{v / total * 100:.0f}% <span>({v})</span></div></div>'
        for n, v, w in zip(dist.index, dist.values, WARNA_STATUS)
    )
    return h(f'<div style="padding-top:.5rem">{baris}</div>')


def fig_usia(p: pd.DataFrame) -> go.Figure:
    peta = {
        "Normal": "Normal", "Pra-hipertensi": "Pra-hipertensi",
        "Hipertensi Tahap 1": "Hipertensi", "Hipertensi Tahap 2": "Hipertensi",
    }
    q = p.assign(grup=p["status_hipertensi"].map(peta))
    tab = (
        q.groupby(["kelompok_usia", "grup"], observed=False).size().unstack(fill_value=0)
        .reindex(index=KELOMPOK_USIA, columns=["Normal", "Pra-hipertensi", "Hipertensi"], fill_value=0)
    )
    fig = go.Figure()
    for kolom, warna in zip(tab.columns, [HIJAU, KUNING, MERAH]):
        fig.add_trace(go.Bar(x=tab.index, y=tab[kolom], name=kolom, marker_color=warna))
    _dasar(fig, 250, kiri=4, atas=28, bawah=4)
    fig.update_layout(
        barmode="group", bargap=0.28, bargroupgap=0.06,
        legend=dict(orientation="h", x=0.0, y=1.16, font=dict(size=10)),
        xaxis=dict(title=dict(text="Kelompok Usia", font=dict(size=10))),
        yaxis=dict(title=dict(text="Jumlah Partisipan", font=dict(size=10)), dtick=1 if tab.values.max() <= 6 else None),
    )
    return fig


def fig_korelasi(p: pd.DataFrame) -> go.Figure:
    f = {
        "BMI": p["bmi"],
        "Aktivitas Fisik": p["aktivitas_fisik_hari_per_minggu"],
        "Pola Makan Tinggi Garam": (p["pola_makan"] == "Tinggi Garam").astype(int),
        "Durasi Tidur": p["jam_tidur"],
    }
    if "tingkat_stres" in p.columns:
        f["Tingkat Stres"] = p["tingkat_stres"]
    f["Merokok"] = (p["merokok"] == "Ya").astype(int)
    z = np.nan_to_num(
        [[pd.Series(v).corr(p["sistolik"]), pd.Series(v).corr(p["diastolik"])] for v in f.values()]
    )
    fig = go.Figure(go.Heatmap(
        z=z, x=["Sistolik", "Diastolik"], y=list(f.keys()), zmin=-1, zmax=1,
        colorscale=[[0, "#5b8def"], [0.5, "#ffffff"], [1, "#f26b6b"]],
        text=np.round(z, 2), texttemplate="%{text:.2f}", textfont=dict(size=11, color="#1f2a44"),
        xgap=2, ygap=2,
        colorbar=dict(thickness=10, len=0.95, tickvals=[-1, -0.5, 0, 0.5, 1],
                      ticktext=["-1.0", "-0.5", "0.0", "0.5", "1.0"], tickfont=dict(size=9), outlinewidth=0),
        hovertemplate="%{y} vs %{x}: %{z:.2f}<extra></extra>",
    ))
    _dasar(fig, 250, kiri=4, kanan=4, atas=6, bawah=4)
    fig.update_xaxes(showline=False, showgrid=False)
    fig.update_yaxes(autorange="reversed", showgrid=False, automargin=True, tickfont=dict(size=10))
    return fig


def fig_akurasi() -> go.Figure:
    a = MODEL_DEMO["akurasi"]
    fig = go.Figure(go.Pie(
        values=[a, 100 - a], hole=0.74, sort=False, direction="clockwise",
        marker=dict(colors=[HIJAU, "#e1f1e8"], line=dict(width=0)),
        textinfo="none", hoverinfo="skip",
    ))
    _dasar(fig, 175, 4, 4, 4, 4)
    fig.update_layout(
        showlegend=False,
        annotations=[dict(
            text=f"Akurasi Model<br><span style='font-size:20px;color:{NAVY}'><b>{a:.1f}%</b></span>",
            showarrow=False, font=dict(size=10, color=ABU_TEKS),
        )],
    )
    return fig


def fig_performa() -> go.Figure:
    nama = list(MODEL_DEMO["performa"].keys())
    nilai = list(MODEL_DEMO["performa"].values())
    terbaik = int(np.argmax(nilai))
    warna = [HIJAU if i == terbaik else "#b3c8ee" for i in range(len(nilai))]
    fig = go.Figure(go.Bar(
        x=nama, y=nilai, marker_color=warna, text=[f"{v:.2f}" for v in nilai],
        textposition="outside", textfont=dict(size=10, color=NAVY), cliponaxis=False, width=0.5,
        hovertemplate="%{y:.2f}<extra></extra>",
    ))
    _dasar(fig, 195, kiri=4, atas=26, bawah=4)
    fig.update_layout(
        yaxis=dict(range=[0, 1.05], title=dict(text="Akurasi", font=dict(size=10))),
        xaxis=dict(tickfont=dict(size=9)),
    )
    return fig


# ==================================================
# Dashboard utama
# ==================================================
def _filter_panel(data: pd.DataFrame) -> pd.DataFrame:
    tgl = pd.to_datetime(data["tanggal"])
    awal, akhir = tgl.min().date(), tgl.max().date()
    with st.container(key="card_filter"):
        st.markdown(judul_kartu("Filter Data", "filter"), unsafe_allow_html=True)
        rentang = st.date_input(
            "Tanggal", value=(awal, akhir), min_value=awal, max_value=akhir,
            format="DD/MM/YYYY", key=f"f_tgl_{awal}_{akhir}",
        )
        kec = st.selectbox("Kecamatan", ["Semua Kecamatan"] + sorted(data["kecamatan"].dropna().unique()), key="f_kec")
        jk = st.selectbox("Jenis Kelamin", ["Semua"] + sorted(data["jenis_kelamin"].dropna().unique()), key="f_jk")
        kel = st.selectbox("Kelompok Usia", ["Semua"] + KELOMPOK_USIA, key="f_usia")
        cari = st.text_input("ID Partisipan", placeholder="Cari ID partisipan...", key="f_id")

    hasil = tambah_kelompok_usia(data)
    if isinstance(rentang, (tuple, list)) and len(rentang) == 2:
        hasil = hasil[hasil["tanggal"].between(pd.Timestamp(rentang[0]), pd.Timestamp(rentang[1]))]
    if kec != "Semua Kecamatan":
        hasil = hasil[hasil["kecamatan"] == kec]
    if jk != "Semua":
        hasil = hasil[hasil["jenis_kelamin"] == jk]
    if kel != "Semua":
        hasil = hasil[hasil["kelompok_usia"] == kel]
    if cari.strip() and "id_partisipan" in hasil.columns:
        hasil = hasil[hasil["id_partisipan"].astype(str).str.contains(cari.strip(), case=False, regex=False)]
    return hasil


def _panel_ringkasan(p: pd.DataFrame) -> None:
    if p.empty:
        return
    aktif = p["aktivitas_fisik_hari_per_minggu"].mean()
    baris = [
        ("user", "Rata-rata Usia", f"{fmt(p['usia'].mean())} tahun"),
        ("gauge", "Rata-rata BMI", f"{fmt(p['bmi'].mean())} kg/m²"),
        ("zap", "Rata-rata Aktivitas Fisik", f"{fmt(aktif)} hari/minggu"),
        ("moon", "Rata-rata Durasi Tidur", f"{fmt(p['jam_tidur'].mean())} jam"),
    ]
    isi = "".join(
        f'<div class="stat"><span>{ikon(i, 15, ABU_TEKS)}{n}</span><b>{v}</b></div>' for i, n, v in baris
    )
    with st.container(key="card_ringkasan"):
        st.markdown(judul_kartu("Ringkasan Statistik", "alert-circle"), unsafe_allow_html=True)
        st.markdown(h(isi), unsafe_allow_html=True)

    faktor = {
        "Pola makan tinggi garam": (p["pola_makan"] == "Tinggi Garam").mean(),
        "Kurang aktivitas fisik": (p["aktivitas_fisik_hari_per_minggu"] < 3).mean(),
        "Merokok": (p["merokok"] == "Ya").mean(),
        "BMI berlebih": (p["bmi"] >= 25).mean(),
    }
    if "tingkat_stres" in p.columns:
        faktor["Stres tinggi"] = (p["tingkat_stres"] >= 7).mean()
    urut = sorted(faktor.items(), key=lambda kv: kv[1], reverse=True)[:5]
    daftar = "".join(
        f'<div class="risk-row"><span>{i}. {n}</span><b>({v * 100:.0f}%)</b></div>'
        for i, (n, v) in enumerate(urut, 1)
    )
    st.markdown(
        h(f'<div class="risk"><div class="risk-title">{ikon("alert", 16, "#d32f2f")}Faktor Risiko Utama</div>{daftar}</div>'),
        unsafe_allow_html=True,
    )


def _kpi(kelas: str, nama_ikon: str, warna: str, label: str, nilai: str, sub: str) -> str:
    return h(f"""
    <div class="kpi kpi-{kelas}">
      <div class="kpi-ico">{ikon(nama_ikon, 22, warna)}</div>
      <div><div class="kpi-label">{label}</div><div class="kpi-value">{nilai}</div><div class="kpi-sub">{sub}</div></div>
    </div>
    """)


def _tabel_contoh(p: pd.DataFrame) -> str:
    def chip(s: str) -> str:
        if s == "Normal":
            return '<span class="st-n">Normal</span>'
        if s == "Pra-hipertensi":
            return '<span class="st-p">Pra-hipertensi</span>'
        return '<span class="st-h">Hipertensi</span>'

    baris = "".join(
        f"<tr><td>{r.id_partisipan}</td><td>{int(r.usia)}</td><td>{r.jenis_kelamin}</td>"
        f"<td>{r.kecamatan}</td><td>{chip(r.status_hipertensi)}</td></tr>"
        for r in p.head(5).itertuples()
    )
    return h(
        '<table class="tbl"><thead><tr><th>ID Partisipan</th><th>Usia</th><th>Jenis Kelamin</th>'
        f"<th>Kecamatan</th><th>Status</th></tr></thead><tbody>{baris}</tbody></table>"
    )


def _html_konfusi() -> str:
    (tn, fp), (fn, tp) = MODEL_DEMO["konfusi"]
    return h(f"""
    <div class="kf-title">Matriks Konfusi</div>
    <table class="kf">
      <tr><th></th><th></th><th colspan="2">Aktual</th></tr>
      <tr><th></th><th></th><th>Tidak<br>Hipertensi</th><th>Hipertensi</th></tr>
      <tr><th rowspan="2" class="vert">Prediksi</th><th>Tidak<br>Hipertensi</th><td class="aman">{tn}</td><td>{fp}</td></tr>
      <tr><th>Hipertensi</th><td>{fn}</td><td class="panas">{tp}</td></tr>
    </table>
    """)


def render_dashboard(data: pd.DataFrame) -> None:
    utama, kanan = st.columns([3.55, 1], gap="medium")

    with kanan:
        f = _filter_panel(data)
        p = ringkas_per_partisipan(f) if not f.empty else f
        _panel_ringkasan(p)

    with utama:
        if f.empty:
            st.warning("Tidak ada data yang cocok dengan filter. Ubah filter di panel kanan.")
            return

        n_p = len(p)
        # Kasus = partisipan di atas rentang Normal (Pra-hipertensi + Hipertensi), sesuai desain (8 = 32%)
        kasus = int((p["status_hipertensi"] != "Normal").sum())
        hari = f["tanggal"].nunique()

        k = st.columns(4, gap="small")
        k[0].markdown(_kpi("biru", "users", BIRU, "Jumlah Partisipan", f"{n_p}", "Usia produktif (15–64 tahun)"), unsafe_allow_html=True)
        k[1].markdown(_kpi("hijau", "heart-pulse", HIJAU, "Total Pengukuran", f"{len(f):,}".replace(",", "."), f"Data selama {hari} hari"), unsafe_allow_html=True)
        k[2].markdown(_kpi("merah", "alert", "#e03b3b", "Kasus Hipertensi", f'{kasus}<span class="kpi-pct">({kasus / n_p * 100:.0f}%)</span>', "Dari total partisipan"), unsafe_allow_html=True)
        k[3].markdown(_kpi("ungu", "activity", "#6d4fd6", "Rata-rata Tekanan Darah", f'{f["sistolik"].mean():.0f}/{f["diastolik"].mean():.0f}<small>mmHg</small>', "Sistolik / Diastolik"), unsafe_allow_html=True)

        # --- Baris 1: tren + donut ---
        c1, c2 = st.columns([1.75, 1.05], gap="small")
        with c1:
            with st.container(key="card_tren"):
                st.markdown(judul_kartu("Tren Tekanan Darah Rata-rata"), unsafe_allow_html=True)
                opsi = ["Semua Partisipan"] + sorted(f["id_partisipan"].unique())
                pilih = st.selectbox("Partisipan", opsi, key="tren_pilih")
                tampil(fig_tren(f, pilih), "g_tren")
        with c2:
            with st.container(key="card_donut"):
                st.markdown(judul_kartu("Distribusi Tekanan Darah"), unsafe_allow_html=True)
                tampil(fig_donut_status(p), "g_donut")
                st.markdown(html_legenda_status(p), unsafe_allow_html=True)

        # --- Baris 2: usia + korelasi ---
        c3, c4 = st.columns([1, 1.15], gap="small")
        with c3:
            with st.container(key="card_usia"):
                st.markdown(judul_kartu("Distribusi Tekanan Darah Berdasarkan Usia"), unsafe_allow_html=True)
                tampil(fig_usia(p), "g_usia")
        with c4:
            with st.container(key="card_korelasi"):
                st.markdown(judul_kartu("Hubungan Faktor Risiko dengan Tekanan Darah"), unsafe_allow_html=True)
                tampil(fig_korelasi(p), "g_korelasi")

        # --- Baris 3: prediksi + performa + tabel ---
        c5, c6, c7 = st.columns([1.25, 0.95, 1.1], gap="small")
        with c5:
            with st.container(key="card_prediksi"):
                st.markdown(judul_kartu("Prediksi Hipertensi (Klasifikasi)", "target"), unsafe_allow_html=True)
                tampil(fig_akurasi(), "g_akurasi")
                st.markdown(_html_konfusi(), unsafe_allow_html=True)
        with c6:
            with st.container(key="card_performa"):
                st.markdown(judul_kartu("Performa Model", "bars"), unsafe_allow_html=True)
                tampil(fig_performa(), "g_performa")
        with c7:
            with st.container(key="card_tabel"):
                st.markdown(judul_kartu("Data Partisipan (Contoh)", "table-user"), unsafe_allow_html=True)
                st.markdown(_tabel_contoh(p), unsafe_allow_html=True)
                if st.button("Lihat semua data  →", key="lihat_semua"):
                    st.session_state["page"] = "Data Partisipan"
                    st.rerun()


# ==================================================
# Header & footer
# ==================================================
def render_header(halaman: str, data: pd.DataFrame) -> None:
    judul, desk = INFO_HALAMAN.get(halaman, (halaman, ""))
    tgl = pd.to_datetime(data["tanggal"])
    kiri, kanan = st.columns([2.3, 1.7], vertical_alignment="top")
    with kiri:
        st.markdown(h(f'<div class="page-title">{judul}</div><div class="page-desc">{desk}</div>'), unsafe_allow_html=True)
    with kanan:
        a, b = st.columns([1.3, 0.8], gap="small")
        with a:
            st.selectbox("Wilayah", ["Kabupaten Toba"], label_visibility="collapsed", key="wilayah")
        b.markdown(
            h(f'<div class="chip-user"><div class="avatar">{ikon("user", 14, "#ffffff")}</div>User{ikon("chevron", 14, ABU_TEKS)}</div>'),
            unsafe_allow_html=True,
        )
        st.markdown(
            h(f'<div class="pill-date">{ikon("calendar", 15, ABU_TEKS)}{tgl_id(tgl.min())} - {tgl_id(tgl.max())}</div>'),
            unsafe_allow_html=True,
        )


def render_footer(data: pd.DataFrame) -> None:
    akhir = pd.to_datetime(data["tanggal"]).max()
    st.markdown(
        h(f"""
        <div class="foot">
          <span>© 2025 Toba Health Insight &nbsp;|&nbsp; Analisis Faktor Risiko dan Prediksi Hipertensi</span>
          <span>{ikon("refresh", 13, ABU_TEKS)}Data diperbarui pada {akhir.day} {BULAN[akhir.month - 1]} {akhir.year}, 10.24</span>
        </div>
        """),
        unsafe_allow_html=True,
    )


# ==================================================
# Halaman lain (memakai tema yang sama)
# ==================================================
def _gaya_plot(fig: go.Figure, tinggi: int = 340) -> go.Figure:
    fig.update_layout(
        height=tinggi, margin=dict(l=10, r=10, t=44, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", size=11, color=ABU_TEKS),
        legend=dict(orientation="h", y=-0.2), title=dict(font=dict(size=14, color=NAVY)),
    )
    fig.update_xaxes(gridcolor="#edf1f7", linecolor="#dfe6f1")
    fig.update_yaxes(gridcolor="#edf1f7", zeroline=False)
    return fig


def _grafik(fig: go.Figure, tinggi: int, key: str) -> None:
    tampil(_gaya_plot(fig, tinggi), key)


def render_data_partisipan(data: pd.DataFrame) -> None:
    with st.container(key="card_dp"):
        st.markdown(judul_kartu("Data Pengukuran Partisipan", "table-user"), unsafe_allow_html=True)
        st.dataframe(data, use_container_width=True, hide_index=True)


def render_faktor(data: pd.DataFrame) -> None:
    p = ringkas_per_partisipan(data)
    warna = dict(zip(STATUS_URUT, WARNA_STATUS))
    c1, c2 = st.columns(2)
    with c1, st.container(key="card_f1"):
        _grafik(px.box(p, x="status_hipertensi", y="bmi", color="status_hipertensi", color_discrete_map=warna,
                       category_orders={"status_hipertensi": STATUS_URUT}, title="BMI menurut Status Hipertensi"), 360, "f_bmi")
    with c2, st.container(key="card_f2"):
        akt = data.groupby("aktivitas_fisik_hari_per_minggu", as_index=False)["sistolik"].mean()
        fig = px.line(akt, x="aktivitas_fisik_hari_per_minggu", y="sistolik", markers=True,
                      title="Aktivitas Fisik dan Rata-rata Sistolik")
        fig.update_traces(line_color=BIRU)
        _grafik(fig, 360, "f_akt")
    c3, c4, c5 = st.columns(3)
    with c3, st.container(key="card_f3"):
        fig = px.bar(data.groupby("pola_makan", as_index=False)["sistolik"].mean(), x="pola_makan", y="sistolik", title="Pola Makan")
        fig.update_traces(marker_color=BIRU)
        _grafik(fig, 310, "f_pola")
    with c4, st.container(key="card_f4"):
        _grafik(px.box(p, x="merokok", y="sistolik", color="merokok", title="Kebiasaan Merokok"), 310, "f_rokok")
    with c5, st.container(key="card_f5"):
        _grafik(px.scatter(p, x="jam_tidur", y="diastolik", color="status_hipertensi", color_discrete_map=warna,
                           title="Tidur dan Diastolik"), 310, "f_tidur")


def render_tren(data: pd.DataFrame) -> None:
    daily = data.groupby("tanggal")[["sistolik", "diastolik"]].agg(["mean", "min", "max"]).reset_index()
    daily.columns = ["tanggal", "sistolik_mean", "sistolik_min", "sistolik_max",
                     "diastolik_mean", "diastolik_min", "diastolik_max"]
    fig = go.Figure()
    for nama, warna in [("sistolik", BIRU), ("diastolik", ORANYE)]:
        fig.add_trace(go.Scatter(x=daily.tanggal, y=daily[f"{nama}_max"], mode="lines",
                                 line=dict(width=0), showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=daily.tanggal, y=daily[f"{nama}_min"], mode="lines", fill="tonexty",
                                 fillcolor=f"{warna}22", line=dict(width=0), name=f"{nama.title()} (rentang)"))
        fig.add_trace(go.Scatter(x=daily.tanggal, y=daily[f"{nama}_mean"], mode="lines+markers",
                                 line=dict(color=warna, width=2.5), name=f"{nama.title()} rata-rata"))
    fig.update_layout(title="Pergerakan rata-rata dan rentang pengukuran", yaxis_title="mmHg")
    with st.container(key="card_tr1"):
        _grafik(fig, 430, "t_harian")
    with st.container(key="card_tr2"):
        st.dataframe(daily, use_container_width=True, hide_index=True)


def render_prediksi(data: pd.DataFrame) -> None:
    st.info("Model ML belum diaktifkan. Halaman ini menyiapkan alur input dan keluaran klasifikasi untuk dataset final.")
    kiri, kanan = st.columns([1, 1.35], gap="medium")
    with kiri, st.container(key="card_pr1"):
        st.markdown(judul_kartu("Input Klasifikasi", "target"), unsafe_allow_html=True)
        st.number_input("Usia", 15, 64, 35)
        st.number_input("BMI", 15.0, 45.0, 24.0)
        sis = st.number_input("Sistolik", 80, 220, 128)
        dia = st.number_input("Diastolik", 40, 140, 82)
        if st.button("Jalankan klasifikasi demo", type="primary", use_container_width=True):
            if sis >= 140 or dia >= 90:
                st.warning("Indikasi hipertensi berdasarkan ambang demo.")
            elif sis >= 130 or dia >= 80:
                st.info("Indikasi pra-hipertensi berdasarkan ambang demo.")
            else:
                st.success("Rentang normal berdasarkan ambang demo.")
    with kanan, st.container(key="card_pr2"):
        st.markdown(judul_kartu("Catatan penggunaan"), unsafe_allow_html=True)
        st.caption("Output di atas bukan diagnosis medis. Model terlatih, validasi, metrik, dan threshold "
                   "perlu ditetapkan setelah dataset penelitian tersedia.")
        p = ringkas_per_partisipan(data)
        st.dataframe(p[["id_partisipan", "usia", "bmi", "sistolik", "diastolik", "status_hipertensi"]]
                     .round({"sistolik": 0, "diastolik": 0}).head(8),
                     use_container_width=True, hide_index=True)


def render_evaluasi() -> None:
    st.info("Placeholder UI — metrik di bawah adalah contoh tampilan, bukan hasil penelitian atau model nyata.")
    model = pd.DataFrame({
        "Model": ["Logistic Regression", "Random Forest", "SVM", "Naive Bayes"],
        "Akurasi": [.78, .86, .81, .72], "F1-score": [.74, .84, .78, .68], "AUC": [.82, .90, .86, .76],
    })
    c1, c2 = st.columns([1.3, 1], gap="medium")
    with c1, st.container(key="card_ev1"):
        fig = px.bar(model, x="Model", y="Akurasi", range_y=[0, 1], title="Perbandingan Akurasi (contoh)")
        fig.update_traces(marker_color=HIJAU)
        _grafik(fig, 360, "e_akurasi")
    with c2, st.container(key="card_ev2"):
        st.dataframe(model.style.format({"Akurasi": "{:.0%}", "F1-score": "{:.0%}", "AUC": "{:.0%}"}),
                     use_container_width=True, hide_index=True)


def render_laporan(data: pd.DataFrame) -> None:
    p = ringkas_per_partisipan(data)
    st.markdown(judul_kartu("Ringkasan Data", "bars"), unsafe_allow_html=True)
    a, b, c = st.columns(3)
    a.metric("Partisipan", f"{len(p):,}")
    b.metric("Total pengukuran", f"{len(data):,}")
    c.metric("Rata-rata tekanan darah", f"{data['sistolik'].mean():.0f}/{data['diastolik'].mean():.0f} mmHg")
    st.caption("Dashboard ini memakai data sintetis untuk merancang UI. Interpretasi klinis dan model "
               "prediksi ditambahkan setelah dataset final tersedia. Gunakan halaman Kelola Data untuk ekspor.")


def _ekspor_excel(df: pd.DataFrame) -> bytes:
    out = BytesIO()
    with pd.ExcelWriter(out, engine="xlsxwriter") as w:
        df.to_excel(w, index=False, sheet_name="Data Partisipan")
    return out.getvalue()


def render_kelola(data: pd.DataFrame) -> None:
    with st.container(key="card_sumber"):
        st.markdown(judul_kartu("Sumber Data", "database"), unsafe_allow_html=True)
        pakai_upload = st.session_state.get("data_upload") is not None
        st.caption(f"Sumber aktif: **{st.session_state.get('nama_upload', 'Dataset demo (sintetis)') if pakai_upload else 'Dataset demo (sintetis)'}**")
        up = st.file_uploader("Unggah CSV atau Excel", type=["csv", "xlsx"], key="uploader")
        if st.button("Gunakan dataset demo", use_container_width=True, disabled=not pakai_upload):
            st.session_state.pop("data_upload", None)
            st.session_state.pop("nama_upload", None)
            st.rerun()
        if up is not None and st.session_state.get("nama_upload") != up.name:
            try:
                raw = pd.read_excel(up) if up.name.lower().endswith(".xlsx") else pd.read_csv(up)
                kurang = sorted(set(KOLOM_MINIMUM) - set(raw.columns))
                if kurang:
                    st.error(f"Berkas belum memiliki kolom minimum: {', '.join(kurang)}")
                else:
                    st.session_state["data_upload"] = raw
                    st.session_state["nama_upload"] = up.name
                    st.rerun()
            except Exception as exc:  # noqa: BLE001
                st.error(f"Gagal membaca berkas: {exc}")

    with st.container(key="card_kelola"):
        st.markdown(judul_kartu("Sunting & Ekspor Data", "table-user"), unsafe_allow_html=True)
        st.caption("Data demo bersifat sintetis. Berkas sumber tidak ditimpa otomatis.")
        edit = st.data_editor(data, num_rows="dynamic", use_container_width=True, height=380)
        st.download_button("Ekspor CSV", edit.to_csv(index=False).encode("utf-8-sig"),
                           "data_hipertensi.csv", "text/csv", use_container_width=True)
        st.download_button("Ekspor Excel", _ekspor_excel(edit), "data_hipertensi.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True)
        st.download_button("Laporan ringkas", f"Jumlah baris: {len(edit)}\nKolom: {len(edit.columns)}".encode(),
                           "laporan_ringkas.txt", "text/plain", use_container_width=True)