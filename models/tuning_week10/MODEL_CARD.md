# Model card - eksperimen tuning Minggu 10

Run `e34327cd28c78f592900`; algoritma Linear Regression; target `future_7d_mean_sbp`; horizon 7 hari.

DATA SINTETIS / SIMULASI. 19 ID; 60 window train / 7 origin test historis.

Fitur: past_7d_sbp, past_7d_dbp, past_7d_sbp_std, age, bmi, past_7d_activity, past_7d_sleep, past_7d_stress.

Konfigurasi: `{}`.

| Model | Tahap | RMSE val | MAE val | RMSE historis | MAE historis | R2 historis |
|---|---|---:|---:|---:|---:|---:|
| Naive 7-day mean | reference | 2.377 | 1.908 | 2.235 | 1.934 | 0.850 |
| Linear Regression | original | 2.759 | 2.180 | 3.114 | 2.575 | 0.709 |
| Linear Regression | selected_configuration | 2.759 | 2.180 | 3.114 | 2.575 | 0.709 |
| Random Forest | original | 4.750 | 3.178 | 3.441 | 2.959 | 0.645 |
| Random Forest | selected_configuration | 4.325 | 2.912 | 3.236 | 2.682 | 0.686 |
| Hist Gradient Boosting | original | 4.600 | 3.353 | 4.832 | 3.693 | 0.300 |
| Hist Gradient Boosting | selected_configuration | 4.510 | 3.318 | 4.651 | 3.631 | 0.352 |

DATA SINTETIS / SIMULASI. Inner GroupKFold memisahkan ID, tetapi kalender fit/validasi dapat beririsan dan target window training berkorelasi. Ini bukan validasi forecasting kronologis penuh. Test CP3 sudah pernah diperiksa; evaluasi ulang bersifat historis, bukan holdout baru. Sampel kecil; bukan validasi klinis atau hasil data aktual. Persetujuan target diasumsikan untuk tugas ini; bukti akademik belum direkam dalam artefak aktif.

Tidak dipromosikan ke API/dashboard. Bukan diagnosis atau keputusan medis. Rincian protokol dan reproduksi: docs/WEEK10_TUNING_REPORT.md.

## Analisis error Minggu 10

DATA SINTETIS / SIMULASI; evaluasi test historis, bukan holdout baru.

Model Linear Regression: MAE 2.575, RMSE 3.114 mmHg; R2 0.709; bias (prediksi - aktual) -1.697 mmHg.

4 prediksi terlalu rendah, 3 terlalu tinggi, 0 sama dalam toleransi numerik 1e-9 mmHg (bukan batas klinis). Error absolut terbesar 5.136 mmHg.

Dibanding naif pada pasangan yang sama: 3 lebih kecil, 4 lebih besar, 0 sama. Perbandingan pasangan ini deskriptif, bukan uji signifikansi.

Hanya 7 origin dari 7 ID, satu origin per ID. Error per responden hanya deskriptif; tidak membuktikan kestabilan individu, perbedaan kelompok, atau sebab error. Tidak ada interval ketidakpastian tervalidasi atau klaim diagnosis.

Model terlatih dipilih dari validasi; hasil test tidak mengubah pemilihan. Baseline naif tetap pembanding dan unggul pada eksperimen ini. Laporan: docs/WEEK10_EVALUATION_REPORT.md; tabel/grafik: reports/week10_evaluation/.
