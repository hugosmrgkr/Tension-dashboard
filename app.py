import pandas as pd
import streamlit as st

import dashboard_pages as dp
from data_utils import buat_data_hipertensi_demo, klasifikasi_tekanan

st.set_page_config(
    page_title="Toba Health Insight",
    page_icon="❤",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(f"<style>{dp.GAYA_CSS}</style>", unsafe_allow_html=True)

MENU = [
    ("Dashboard", "home"),
    ("Data Partisipan", "person"),
    ("Analisis Faktor Risiko", "bar_chart"),
    ("Tren Tekanan Darah", "show_chart"),
    ("Prediksi Hipertensi", "track_changes"),
    ("Evaluasi Model", "model_training"),
    ("Laporan & Ringkasan", "description"),
    ("Kelola Data", "database"),
]

if "page" not in st.session_state:
    st.session_state["page"] = "Dashboard"

with st.sidebar:
    st.markdown(dp.html_brand(), unsafe_allow_html=True)
    for i, (label, material) in enumerate(MENU):
        aktif = st.session_state["page"] == label
        if st.button(
            label,
            key=f"{'navon' if aktif else 'navoff'}_{i}",
            icon=f":material/{material}:",
            use_container_width=True,
        ):
            st.session_state["page"] = label
            st.rerun()
    st.markdown(dp.html_sidebar_bawah(), unsafe_allow_html=True)

page = st.session_state["page"]


def muat_data() -> pd.DataFrame:
    """Data unggahan (dari halaman Kelola Data) bila ada, selain itu data demo."""
    if st.session_state.get("data_upload") is not None:
        d = st.session_state["data_upload"].copy()
    else:
        if "hipertensi_demo" not in st.session_state:
            st.session_state["hipertensi_demo"] = buat_data_hipertensi_demo()
        d = st.session_state["hipertensi_demo"].copy()
    d["tanggal"] = pd.to_datetime(d["tanggal"], errors="coerce")
    d = d.dropna(subset=["tanggal", "sistolik", "diastolik"]).copy()
    if "status_hipertensi" not in d.columns:
        d["status_hipertensi"] = [klasifikasi_tekanan(s, k) for s, k in zip(d["sistolik"], d["diastolik"])]
    return d


data = muat_data()

dp.render_header(page, data)

if page == "Dashboard":
    dp.render_dashboard(data)
elif page == "Data Partisipan":
    dp.render_data_partisipan(data)
elif page == "Analisis Faktor Risiko":
    dp.render_faktor(data)
elif page == "Tren Tekanan Darah":
    dp.render_tren(data)
elif page == "Prediksi Hipertensi":
    dp.render_prediksi(data)
elif page == "Evaluasi Model":
    dp.render_evaluasi()
elif page == "Laporan & Ringkasan":
    dp.render_laporan(data)
else:
    dp.render_kelola(data)

dp.render_footer(data)