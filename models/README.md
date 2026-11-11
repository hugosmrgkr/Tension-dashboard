# Baseline model checkpoint M6–M8

- `baseline_metrics.json`: metrik **hasil eksperimen benar-benar dihitung** dari dua CSV sintetis.
- `linear_regression_synthetic.joblib`: model pembanding awal pada data simulasi. Jangan deploy sebagai model diagnosis. FastAPI endpoint demo menampilkan baseline naif sebagai contoh yang mudah dijelaskan.
- Model baseline naif: rata-rata sistolik 7 hari sebelumnya → perkiraan rata-rata sistolik 7 hari berikutnya.
- Model pembanding: Linear Regression; hold-out ID responden (`GroupShuffleSplit`) sekaligus pemisahan waktu dengan purge label. Target uji tujuh hari tidak tumpang tindih; preprocessing hanya fit pada train.
- Hanya baris dengan tujuh hari histori dan tujuh hari target lengkap yang dipakai. Fitur tidak menggunakan data masa depan.
- Eksperimen final minimal tiga model dan tuning akan menjadi pekerjaan berikutnya, setelah data aktual cukup dan target disetujui dosen.
- `baseline_metrics.json` tidak boleh dibaca sebagai bukti evaluasi pada pasien atau masyarakat nyata.

Audit final P0/P1: manifest v3 menggunakan hash teks UTF-8 dengan normalisasi LF/CRLF (`utf8-lf-v1`); hash biner joblib tetap byte-exact. `.gitattributes` mengunci LF untuk JSON dan menonaktifkan konversi biner. Nilai metrik yang berubah atau model rusak tetap ditolak. ETL, API dan baseline memakai gate pasangan pembacaan yang sama; lihat `docs/P0_P1_FINAL_AUDIT.md` dan `backend/app/bp_policy.py`. Target `future_7d_mean_sbp` tetap usulan, belum disetujui dosen.

## P2-01: `models/experiments/`
- `comparison_metrics.json` / `comparison_manifest.json`: hasil perbandingan 3 algoritma + baseline naif, berhash (`utf8-lf-v1`).
- `linear_regression_synthetic.joblib`: model terpilih berdasarkan RMSE validasi leave-ID-out; dilayani oleh `/api/model/predict` (P2-02).
- `MODEL_CARD.md`: dibuat otomatis oleh `etl/run_model_comparison.py`; jangan edit manual. **DATA SINTETIS, target belum disetujui, bukan diagnosis.**
- Berkas CP3 di folder ini (`baseline_*.json`, `linear_regression_synthetic.joblib`) tidak diubah.
