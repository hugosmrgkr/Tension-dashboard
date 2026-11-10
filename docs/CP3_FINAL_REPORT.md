# CP3 Final Report - Minggu 8

> **CATATAN SINKRONISASI (10 Nov 2026, CP3-K01):** Laporan ini bersifat historis per tanggal penulisannya. Definisi teknis, hasil tes, dan run ID artefak ML **terbaru dan otoritatif** ada di [`P0_P1_FINAL_AUDIT.md`](P0_P1_FINAL_AUDIT.md). Secara khusus: run artefak ML pada dokumen ini (`242a4f84499a00fc1028`) **sudah digantikan** oleh run `5d3bed0d6591cd2bc09d` yang diverifikasi ulang pada audit P0/P1 dan dikonfirmasi ulang pada [`reports/p0_p1_final_verification.md`](../reports/p0_p1_final_verification.md). Skor metrik (MAE/RMSE/R²) tidak berubah antara kedua run tersebut — hanya provenance/fingerprint yang berbeda. Gunakan dokumen ini untuk riwayat tahapan CP3, bukan untuk angka run ID atau jumlah tes terbaru.

**SELESAI SECARA TEKNIS PADA DATA SINTETIS / SIMULASI.** Tahap 3-4 telah diimplementasikan dan diuji; target belum disetujui final oleh dosen. Tidak menyatakan data primer cukup, validitas klinis, diagnosis hipertensi, deployment publik atau CP4/CP5 selesai.

## 1. Ringkasan seluruh CP3

| Tahap | Hasil | Bukti |
|---|---|---|
| 1 - Integrasi CP2 | API/warehouse dinamis, filter/ekspor, missing, empty state, ETL manual, tanpa upload/auto-seed | `CP3_STAGE1.md` |
| 2 - Dashboard v1 | Delapan halaman navy responsif, KPI/demografi/gaya hidup/tren/storytelling, 34 panel termasuk pengulangan konteks, drill-down/cross-filter dan sample context | `CP3_STAGE2.md` |
| 3 - Baseline | Target sama; audit dan perbaikan split ID/waktu/test overlap; naive + Linear Regression dijalankan ulang; metrik/prediksi/residual/manifest nyata | `CP3_BASELINE_REPORT.md`, notebook 03, `reports/cp3_baseline/` |
| 4 - Demo/progres | Stack demo Docker terpisah, integrasi lengkap, tes/backend/frontend/browser, bukti serta dokumen demo/checklist/rencana | `CP3_PROGRESS_REPORT.md`, `CP3_DEMO_SCRIPT.md`, `CP3_CHECKLIST.md`, `CP3_NEXT_STEPS.md` |

Acuan: `Deskripsi_Proyek_DA_DS.pdf` hal. 4-6 (spesifikasi dan timeline), panduan utama hal. 10-12/16/20, serta laporan CP2 dan CP3 1-2. CP3/M8 menuntut dashboard v1 dengan warehouse, laporan baseline dan rencana eksperimen. Syarat final tiga algoritma/tuning/jenis advance lengkap/public deployment tidak dipaksakan ke M8. Persetujuan topik/target dan kecukupan primer tetap keputusan dosen; dokumen kerja bukan bukti pengesahan.

## 2. Verifikasi baseline dan hasil aktual

Target usulan `future_7d_mean_sbp` tidak diganti. Origin akhir hari t; histori t-6..t dan target rerata SBP harian t+1..t+7, masing-masing tujuh hari kalender lengkap. SBP harian merata-ratakan sesi SBP tersedia; fitur perilaku hanya histori. Usia/BMI statis diasumsikan diketahui sebelum origin pada fixture, bukan bukti timestamp aktual. Imputer median dan scaler fit train saja.

Skema lama ID-only dihitung ulang untuk menunjukkan hasil awal secara jujur: kalender train/test sama dan target test berurutan overlap. Utama sekarang: holdout ID seed 42 + cutoff **2026-09-18**, train label selesai paling lambat cutoff; test origin pada/setelah cutoff; target test per ID tidak overlap. **60 train pada 12 ID / 7 test pada 7 ID**. Dataset lengkap menghasilkan 323 window; bukan 323 individu.

| Metode | MAE (mmHg) | RMSE (mmHg) | R2 |
|---|---:|---:|---:|
| Naive 7-day mean | 1.933673 | 2.234723 | 0.850309 |
| Linear Regression | 2.575492 | 3.113985 | 0.709343 |

Pada split kecil ini naive lebih rendah MAE daripada Linear Regression. Tidak ada klaim perbedaan signifikan atau generalisasi pasien. R2 bukan accuracy persen. Audit: nol overlap ID, nol pengukuran ID-tanggal dibagi antarsubset, nol overlap target test; seluruh label train tersedia saat origin test. Training windows masih berkorelasi (overlap di dalam train) dan test hanya 7 origin. Hasil subject-only 204/119 dan purged rolling 42 test disimpan sebagai sensitivitas, bukan skor utama atau sampel independen.

Run artefak: **`242a4f84499a00fc1028`**. `baseline_manifest.json` memeriksa metrics/model melalui hash. Metrik dihitung dari prediksi presisi penuh dan diverifikasi ulang; joblib direload dan prediksi dicocokkan. Error per origin/ID dan dugaan penyebab yang belum terbukti tersedia di CSV/laporan/PNG. Endpoint naive berbagi fungsi agregasi dengan eksperimen; tersedia `asof_date` untuk memeriksa origin tanpa memakai data setelahnya. UI menjelaskan split, sampel, target belum disetujui, run ID dan rentang ramalan. Artefak hilang/rusak ditolak tanpa angka pengganti.

Notebook `03_verifikasi_baseline_cp3.ipynb` benar-benar dieksekusi: **6 sel kode sukses, 3 PNG tertanam**. Notebook 02 dan pipeline CP2 tidak diubah. Notebook 01 dipertahankan sebagai catatan awal; untuk verifikasi final gunakan 03.

## 3. Integrasi dan pengujian

| Pemeriksaan | Hasil |
|---|---|
| backend_sqlite | 59 lulus, 1 dilewati, 0 gagal |
| backend_postgresql_linux | 59 lulus, 1 dilewati, 0 gagal |
| frontend_components | 9 lulus, 0 dilewati, 0 gagal |
| Browser Microsoft Edge pada Docker demo | 7 skenario lulus; 8 halaman desktop 1440x1000/mobile 390x844, grafik asli, metrik/hasil baseline, interaksi, filter/CSV dan empty/error |
| Production build host + Docker frontend/backend | Lulus; aset JS sekitar 4.91 MB; peringatan bundle Plotly tetap ada |
| ETL -> PostgreSQL demo | 19 profil, 30 tanggal, 2 sesi, 570 harian, 1.140 sesi; nol orphan; hari aktif mingguan 0 missing |
| Konsistensi API/SQL/CSV | KPI SBP 118,9 / DBP 72,6 mmHg; filter ID/Pagi-Malam/tanggal dan ekspor cocok; tidur NA 6, duduk 3, jumlah merokok 550 |
| Warehouse -> fitur/model | Semua 323 window PostgreSQL cocok dengan CSV offline; 7 prediksi LR cocok dengan artefak (selisih maksimum 0.0) |
| Endpoint naive vs eksperimen | Semua 7 origin holdout cocok dengan nilai naive eksperimen setelah pembulatan output |
| Aktif dan berkas terlindungi | Fingerprint aktif sebelum/sesudah sama; semua 10 berkas terlindungi/ketiadaan `.env` cocok |

Kontrak API v1 usang dilewati secara eksplisit, tidak dihitung sebagai lulus. Tes backend memakai SQLite in-memory atau PostgreSQL khusus tes, bukan database aktif/demo. PostgreSQL khusus tes dihentikan setelah suite; database demo tetap berjalan untuk presentasi. Empty/error browser disimulasikan di jaringan browser, tidak dengan mengosongkan/mengganggu DB aktif. Build dan tes komponen juga dijalankan di host; browser final mengakses Nginx produksi di 8081, bukan sekadar mock React.

Bukti: [verification.json](../reports/cp3_final/verification.json), XML backend/React, [browser-results.json](../reports/cp3_final/browser-results.json), [HTTP verification](../reports/cp3_final/http-verification.json), [warehouse audit](../reports/cp3_final/demo_warehouse.json), [ML equivalence](../reports/cp3_final/warehouse-ml-equivalence.json). [Screenshot nyata](../reports/cp3_final/screenshots/) berjumlah 18: desktop/mobile 1-8, empty dan mobile viewport. Nomor mengikuti urutan sidebar.

Peringatan: chunk Plotly sekitar 4,91 MB / 1,49 MB gzip; Starlette/httpx deprecation; n test kecil dan asumsi profil statis. Bukan audit keamanan/aksesibilitas penuh, uji pengguna formal, atau bukti deploy publik.

## 4. File yang dibuat/diubah pada finalisasi Tahap 3-4

| Kelompok | File |
|---|---|
| Baseline/API | Diubah `backend/app/baseline.py`, blok baseline `backend/app/main.py`; baru `backend/tests/test_cp3_baseline.py`, `backend/requirements-cp3.txt` |
| Artefak | Diperbarui `models/baseline_metrics.json`, `models/linear_regression_synthetic.joblib`; baru `models/baseline_manifest.json` |
| Reproduksi | Baru notebook 03; `etl/verify_baseline.py`, `execute_cp3_notebook.py`, `verify_cp3_demo.py`, `verify_cp3_warehouse.py`, `build_cp3_final_report.py` |
| UI/tes browser | Perubahan kecil `frontend/src/pages/Pages.jsx` untuk konteks split/run/sampel/rentang prediksi; `frontend/playwright.config.js` dan `tests/browser/dashboard.spec.js` mendukung target Docker/bukti final dan tes artefak |
| Demo Docker | Baru `compose.cp3-demo.yaml`, `scripts/start_cp3_demo.ps1`; tidak mengubah compose/volume aktif |
| Dokumentasi/bukti | README/checkpoint diperbarui; 6 laporan CP3 baseline/progress/demo/checklist/next/final; `reports/cp3_baseline/*`, `reports/cp3_final/*` |

Perubahan CP2 dan Tahap 1-2 yang sebelumnya sudah ada pada working tree dipertahankan; seluruh `git diff` bukan hanya pekerjaan finalisasi ini. Tidak ada commit/push otomatis.

## 5. Checklist kesiapan dan keputusan yang terbuka

Checklist lengkap: [CP3_CHECKLIST.md](CP3_CHECKLIST.md). **SELESAI:** reproducible baseline, audit leakage, dashboard/warehouse terintegrasi, tes, demo lokal terisolasi dan materi presentasi. **SEBAGIAN/BELUM:** persetujuan dosen, profil pengguna final, protokol tidur/validitas sesi, kecukupan/izin data primer, timestamp ketersediaan aktual, tiga algoritma/tuning, jenis advance final kelima, model/input final, deployment publik dan user study.

Tidak mengganti target diam-diam. Konfirmasi: bobot hari/sesi, cukup satu sesi/bacaan atau harus keduanya, minimum histori/target, waktu prediksi akhir hari, standar ID, kriteria usia/inklusi, makna tidur, consent, dan apakah person-day memenuhi minimum baris primer dengan jumlah ID terbatas. Jangan memakai hasil simulasi sebagai hasil aktual. [CP3_NEXT_STEPS.md](CP3_NEXT_STEPS.md) berisi rencana, bukan implementasi CP4/CP5.

## 6. Menjalankan demo mandiri dengan Docker

Prasyarat: Docker Desktop aktif, port 8081 dan 8001 tersedia, repo dengan dua fixture dan artefak yang sesuai manifest. Tidak memerlukan perubahan `.env`.

```powershell
# Dari root project; satu stack demo terpisah, bukan compose.yaml aktif.
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start_cp3_demo.ps1
# Frontend: http://127.0.0.1:8081
# Swagger:  http://127.0.0.1:8001/api/docs
```

Script build/start `db/backend/frontend` di project **toba-cp3-demo**. ETL default dry-run; hanya saat DB demo kosong script memvalidasi lalu memuat fixture dengan commit **ke toba_cp3_demo di network demo**. DB berisi data dipertahankan; tidak direset/diganti otomatis. Jika artefak/source tidak cocok, script berhenti untuk pemeriksaan. Jangan arahkan ETL tersebut ke warehouse aktif atau menambahkan hash overwrite hanya agar demo lolos.

Database demo memakai RAM/tmpfs dan tidak berbagi volume aktif. Stopping/recreating db demo membuat data demo hilang, sehingga hindari saat presentasi; start script dapat memuat ulang hanya target demo kosong. Stack demo dibiarkan hidup setelah pengujian. Port lokal saja, bukan deployment publik. Jangan menjalankan `down -v`, reset atau drop DB/volume aktif.

Verifikasi ulang tanpa perubahan DB:

```powershell
python -m etl.verify_cp3_demo
docker compose -f compose.cp3-demo.yaml -p toba-cp3-demo run --rm etl python -m etl.verify_warehouse
docker compose -f compose.cp3-demo.yaml -p toba-cp3-demo run --rm etl python -m etl.verify_cp3_warehouse
```

Baseline offline (menulis model/laporan sintetis secara eksplisit, tanpa DB): buat/aktifkan venv project, `pip install -r backend/requirements-cp3.txt`, lalu `python -m etl.execute_cp3_notebook` atau `python -m etl.verify_baseline`. Baca [baseline report](CP3_BASELINE_REPORT.md) untuk versi dan audit. Run ID dapat berbeda lintas versi Python/lingkungan; prediksi diuji dengan toleransi numerik, bukan mengharuskan byte joblib identik.

Tes: `python -m pytest backend/tests -q -p no:cacheprovider`; frontend `npm ci`, `npm test`, `npm run build`. Browser Docker: set `$env:CP3_BROWSER_BASE_URL='http://127.0.0.1:8081'` dan `$env:CP3_REPORT_DIR='../reports/cp3_final'`, lalu `npm run test:browser` dari frontend (Edge tersedia di Windows). Tidak memuat ulang data aktif untuk memenuhi tes.

Demo aktif lama pada 8080 tidak di-restart atau di-load ulang; hash natural tetap `2c72512aed5d6c4f1e124f1be7ec47a03d0635fe2a6579fe6c3a7edd9c14c267` dan 19 profil hari aktif mingguan masih kosong. Folder model bersama diperbarui sesuai permintaan dan dapat terbaca service lama melalui bind mount; gunakan 8081 untuk pasangan kode terbaru yang diuji lengkap. Penerapan dataset aktif tetap membutuhkan keputusan terpisah.

Naskah demo 5-10 menit: [CP3_DEMO_SCRIPT.md](CP3_DEMO_SCRIPT.md). Pekerjaan berhenti pada finalisasi CP3 teknis ini.
