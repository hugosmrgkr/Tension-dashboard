# Minggu 10 - Eksperimen tuning sintetis

Run: `e34327cd28c78f592900`. Target: `future_7d_mean_sbp`.

## Tujuan dan batas pekerjaan
Mencari konfigurasi Random Forest dan HistGradientBoosting melalui training/validasi,
dengan Linear Regression dan baseline rerata SBP tujuh hari sebagai pembanding.
Persetujuan target diasumsikan sesuai instruksi pengguna, bukan bukti persetujuan
akademik yang diverifikasi. Tidak mengganti target atau flag artefak serving lama.

## Protokol yang dikunci sebelum test
- Dataset: dua CSV `data/sample/`, 19 ID, 570 ID-tanggal, 1.140 sesi sintetis.
- Fitur dan target memakai pipeline CP3: histori t-6..t, target t+1..t+7.
- Split CP3 tetap: 60 train dari 12 ID;
  7 test historis dari 7 ID; cutoff 2026-09-18.
- Tuning: 8 konfigurasi RF dan 8 HGB; 1 konfigurasi LR pembanding; 4 fold GroupKFold.
  Total 68 fit validasi. Grid kecil ditetapkan dalam kode; konfigurasi P2 asli termasuk.
- Semua kandidat memakai fold yang sama, seed 42, imputer/scaler hanya di-fit pada
  bagian fit fold. Tidak mengimputasi target. Nilai fitur dihitung hanya sampai origin.
- Pilihan: pooled out-of-fold RMSE terendah, lalu MAE, lalu kunci kandidat deterministik.
  Peringkat global ini hanya antara model terlatih; baseline naif selalu dilaporkan.
- `grouped_search` hanya menerima frame train. Pemilihan dikunci sebelum test dihitung.
- Audit split luar memeriksa ID terpisah, tidak ada ID-tanggal bersama, label train
  tersedia sebelum origin test, target test tidak overlap, preprocessing training-only.

## Keterbatasan validasi waktu
Origin train hanya 7-11 September, sedangkan labelnya baru selesai 14-18 September.
Tidak ada pasangan fold train/validasi di kalender ini yang bisa memenuhi label-fit
selesai sebelum origin-validasi. Inner CV mengukur generalisasi ke ID lain dalam
kalender training, bukan strict future forecasting. Fold metadata mencatat kondisi ini.
Grid dipilih setelah tim pernah melihat hasil P2, sehingga ada risiko adaptasi terhadap
dataset lama; tidak disebut sebagai nested/unbiased evaluation. Test lama sudah pernah
diperiksa dan metrik di bawah berlabel historis, bukan holdout baru.

## Hasil sebenarnya
RMSE/MAE dalam mmHg; R2 tanpa satuan. Lebih kecil lebih baik untuk RMSE/MAE.

| Model | Tahap | RMSE validasi | MAE validasi | RMSE test historis | MAE test historis | R2 test historis |
|---|---|---:|---:|---:|---:|---:|
| Naive 7-day mean | reference | 2.377 | 1.908 | 2.235 | 1.934 | 0.850 |
| Linear Regression | original | 2.759 | 2.180 | 3.114 | 2.575 | 0.709 |
| Linear Regression | selected_configuration | 2.759 | 2.180 | 3.114 | 2.575 | 0.709 |
| Random Forest | original | 4.750 | 3.178 | 3.441 | 2.959 | 0.645 |
| Random Forest | selected_configuration | 4.325 | 2.912 | 3.236 | 2.682 | 0.686 |
| Hist Gradient Boosting | original | 4.600 | 3.353 | 4.832 | 3.693 | 0.300 |
| Hist Gradient Boosting | selected_configuration | 4.510 | 3.318 | 4.651 | 3.631 | 0.352 |

Model terpilih di antara model terlatih: **Linear Regression**.
Konfigurasi: `{}`.
Mengalahkan naif pada validasi: **tidak**.
RF dan HGB dapat membaik terhadap konfigurasi aslinya tanpa mengalahkan LR atau naif.
Jika pemenang global tetap LR, model terlatih terbaik tidak berubah pada grid ini.
Skor test historis tidak digunakan untuk mengubah pemilihan atau mencari ulang grid.

## Artefak dan reproduksi
- Kode: `backend/app/model_tuning.py`, `etl/run_week10_tuning.py`.
- Notebook: `notebooks/05_tuning_model_minggu10.ipynb`.
- Artefak terpisah: `models/tuning_week10/selected_model.joblib`, metrik, manifest,
  dan model card. Hash teks dinormalisasi LF/CRLF; hash joblib memakai byte persis.
- Bukti: `reports/week10_tuning/validation_trials.csv`, `validation_predictions.csv`,
  `comparison.csv`, `historical_test_predictions.csv`, dan `figures/`.
- Jalankan dari root: `python -m etl.run_week10_tuning` menggunakan environment proyek.
- Notebook juga menjalankan eksperimen dan menampilkan tabel/gambar; menjalankan ulang
  menulis ulang hanya output eksperimen tuning yang disebut di atas.
- Hash semua file model aktif diperiksa sebelum/sesudah eksperimen. Tidak ada promosi
  ke dashboard/API, perubahan database, ETL aktif, `.env`, atau artefak CP3/P2.

## Verifikasi pengerjaan
Regression tests: `python -m pytest backend/tests/test_week10_tuning.py backend/tests/test_p2_model_comparison.py -q -p no:cacheprovider`.
Bukti hasil pengujian dan pemeriksaan ulang tersimpan di
`reports/week10_tuning/verification.json`: jumlah tes lulus/gagal, kesamaan hasil
dua eksekusi, paritas prediksi model tersimpan dengan CSV, kesamaan konfigurasi
original dengan skor P2, dan hash artefak aktif yang dilindungi.
Notebook telah dieksekusi tanpa output error; grafik diperiksa secara visual.
Frontend/browser dan integrasi PostgreSQL tidak diuji ulang pada langkah tuning
offline ini karena tidak ada perubahan pada serving, UI, atau database.

## Penggunaan dan langkah berikutnya
DATA SINTETIS / SIMULASI. Inner GroupKFold memisahkan ID, tetapi kalender fit/validasi dapat beririsan dan target window training berkorelasi. Ini bukan validasi forecasting kronologis penuh. Test CP3 sudah pernah diperiksa; evaluasi ulang bersifat historis, bukan holdout baru. Sampel kecil; bukan validasi klinis atau hasil data aktual. Persetujuan target diasumsikan untuk tugas ini; bukti akademik belum direkam dalam artefak aktif.

Data aktual harus divalidasi terpisah. Perlu kalender lebih panjang untuk validasi
waktu dengan purge dan evaluasi prospektif baru; jangan memaksa split dari sampel kecil.
Integrasi model tuning ke serving membutuhkan pekerjaan kompatibilitas terpisah.
Eksperimen ini menyelesaikan langkah tuning teknis, bukan seluruh cakupan Minggu 10.
