# Notebook Data Science — menunggu dataset penelitian

Tambahkan notebook EDA, preprocessing, baseline, perbandingan >= 3 algoritma, tuning, evaluasi ROC-AUC/F1/recall, error analysis, serta model card. Jangan melatih pada data sintetis demo untuk melaporkan hasil penelitian.

**Minggu 10:** `05_tuning_model_minggu10.ipynb` menjalankan grid terbatas Random Forest
dan HistGradientBoosting, dengan LR/naif pembanding. Hasil sintetis ditulis terpisah
ke `models/tuning_week10/` dan `reports/week10_tuning/`; laporan metode ada di
`docs/WEEK10_TUNING_REPORT.md`. Untuk target regresi gunakan MAE/RMSE/R2;
ROC-AUC/F1/recall pada daftar umum di atas hanya relevan untuk tugas klasifikasi.
Inner CV memisahkan ID tetapi tidak waktu; test historis bukan holdout baru.

**Evaluasi Minggu 10:** `06_evaluasi_error_minggu10.ipynb` membaca prediksi tuning
terverifikasi tanpa training ulang. Output: tabel metrik/bias, error per ID, error
terbesar dan grafik di `reports/week10_evaluation/`; laporan di
`docs/WEEK10_EVALUATION_REPORT.md`. Model card tuning diperbarui, sedangkan model
serving tetap sama. Satu origin per ID tidak cukup untuk menilai kestabilan individu.

**P2-01:** `04_perbandingan_model_regresi.ipynb` membandingkan baseline naif, Linear Regression, Random Forest dan HistGradientBoosting pada target `future_7d_mean_sbp` (DATA SINTETIS; target belum disetujui dosen). Notebook 01-03 tidak diubah. Artefak ditulis ke `models/experiments/` dan `reports/p2_model_comparison/`.
