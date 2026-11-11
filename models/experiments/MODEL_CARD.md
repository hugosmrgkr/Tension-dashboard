# Model Card - Linear Regression (DATA SINTETIS / SIMULASI - EKSPERIMEN)

> **DATA SINTETIS / SIMULASI. Bukan diagnosis, bukan hasil penelitian aktual. Target `future_7d_mean_sbp` belum disetujui dosen (`target_approved=false`).**

Dibuat otomatis oleh `backend/app/model_comparison.py` (run `d43ac5c17c70cead67c7`). Jangan edit manual; jalankan ulang `python -m etl.run_model_comparison`.

## Tujuan dan target
Memperkirakan rerata SBP harian (mmHg) pada tujuh hari setelah origin (akhir hari t). Horizon dan target adalah usulan teknis yang menunggu keputusan dosen.

## Data
19 ID sintetis, 570 ID-tanggal, 1140 sesi; 323 complete windows. Fitur: `past_7d_sbp, past_7d_dbp, past_7d_sbp_std, age, bmi, past_7d_activity, past_7d_sleep, past_7d_stress`. Train 60 window, test utama 7 origin. Seed 42.

## Protokol evaluasi
- Split train/test identik baseline CP3: ID held-out + purge label kronologis (cutoff 2026-09-18) + target uji tidak overlap.
- Pemilihan model memakai validasi leave-ID-out (4 fold) di dalam train. Aturan: RMSE validasi leave-ID-out terkecil; tie dipecah dengan MAE lalu nama.
- Test dihitung sekali setelah pemilihan terkunci. Imputer median, scaler, dan regressor di-fit hanya pada data fit.
- Audit leakage baseline CP3 lulus untuk semua model (tidak ada ID atau kunci ID-tanggal yang dibagi, label train selesai sebelum origin test).

## Hasil (mmHg)
| Model | Jenis | RMSE validasi | MAE validasi | RMSE test | MAE test | R2 test |
|---|---|---:|---:|---:|---:|---:|
| Naive 7-day mean | baseline naif | 2.377 | 1.908 | 2.235 | 1.934 | 0.850 |
| Linear Regression | terlatih | 2.759 | 2.180 | 3.114 | 2.575 | 0.709 |
| Random Forest | terlatih | 4.750 | 3.178 | 3.441 | 2.959 | 0.645 |
| Hist Gradient Boosting | terlatih | 4.600 | 3.353 | 4.832 | 3.693 | 0.300 |

Model terpilih berdasarkan validasi: **Linear Regression** (peringkat: Linear Regression, Hist Gradient Boosting, Random Forest). Mengalahkan baseline naif pada validasi: **tidak**.

## Hiperparameter (tetap, tanpa tuning)
- **Linear Regression**: `{}`
- **Random Forest**: `{"max_depth": 5, "max_features": 0.6, "min_samples_leaf": 5, "n_estimators": 300, "n_jobs": 1, "random_state": 42}`
- **Hist Gradient Boosting**: `{"l2_regularization": 1.0, "learning_rate": 0.05, "max_depth": 3, "max_iter": 120, "min_samples_leaf": 5, "random_state": 42}`

## Peringatan otomatis
- Test hanya 7 origin: metrik test sangat tidak stabil.
- Train hanya 60 window: model non-linear mudah overfit.
- Tidak ada model terlatih yang mengalahkan baseline naif pada validasi.

## Keterbatasan
DATA SINTETIS. Train hanya 60 window dari 12 ID dan test utama hanya 7 origin dari 7 ID, sehingga selisih antar-model tidak stabil dan tidak membuktikan generalisasi. Window train saling berkorelasi. Target belum disetujui dosen. Bukan validasi klinis atau diagnosis.

## Penggunaan yang tidak diperbolehkan
Diagnosis atau klasifikasi hipertensi; keputusan medis; klaim performa pada responden aktual; menyebutnya model final penelitian sebelum target disetujui dosen dan data aktual divalidasi.
