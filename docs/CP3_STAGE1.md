# CP3 Tahap 1 - Integrasi CP2 ke Dashboard

Status: **implementasi dan verifikasi terisolasi selesai; belum diterapkan pada service dan warehouse aktif**. Seluruh hasil di bawah adalah **DATA SINTETIS / SIMULASI**. Data responden asli masih dikumpulkan. Pekerjaan berhenti pada Tahap 1.

## Hasil dan alur data

`dua CSV -> survey_schema / pipeline.prepare CP2 -> validasi dan audit -> CLI apply_validated -> PostgreSQL v2 -> FastAPI -> React / Plotly / CSV export`.

Server tidak membaca CSV untuk melayani dashboard dan tidak memanggil auto-seed saat startup. Startup hanya membuat tabel yang belum ada. Impor pasangan melalui website dihapus. Tombol **Muat ulang data** hanya mengulang GET ke API; tidak menjalankan ETL.

| Komponen | Status | Perubahan / batasan | Referensi |
|---|---|---|---|
| Dashboard | Siap pada warehouse CP2 | KPI, tren, boxplot dan heatmap berasal dari PostgreSQL. Pembanding periode hanya muncul bila ada data pembanding. | `backend/app/analytics_v2.py`, `frontend/src/pages/Pages.jsx` |
| Data Partisipan | Siap | ID cocok secara tepat, profil mengikuti filter tanggal/sesi, hari aktif mingguan CP2 tersedia setelah ETL baru diterapkan. Tabel memakai pagination. | `analytics_v2.py`, `Pages.jsx`, `components/Common.jsx` |
| Analisis Faktor Risiko | Siap | Variabel harian dihitung sekali per ID-tanggal; kelompok usia berasal dari definisi backend. Missing tidak diubah menjadi nol. | `analytics_v2.py`, `pages/Pages.jsx`, `components/Visuals.jsx` |
| Tren Tekanan Darah | Siap | Pagi dan malam terpisah. Semua pembacaan tersedia melalui pagination, termasuk sesi tidak lengkap; grafik hanya memakai sesi valid. | `analytics_v2.py`, `Pages.jsx` |
| Prediksi Hipertensi | Baseline lama dipertahankan | Riwayat responden tetap dari DB. Algoritma, target, notebook, dan artefak ML tidak diubah. Filter analitik tidak melatih ulang model. | `backend/app/main.py`, `frontend/src/App.jsx` |
| Evaluasi Model | Artefak eksperimen dipertahankan | Metrik berasal dari JSON hasil eksperimen, bukan dihitung ulang dari filter PostgreSQL. Pemberitahuan eksplisit ditampilkan. Bukan evaluasi tiga algoritma/data aktual. | `models/baseline_metrics.json`, `App.jsx` |
| Laporan & Ringkasan | Siap | Statistik sesi pagi/malam menggunakan seluruh sesi terfilter, bukan rata-rata tidak berbobot dari rerata per tanggal. Missing dihitung untuk filter aktif. | `analytics_v2.py`, `Pages.jsx` |
| Kelola Data | Siap, baca dan ekspor | Jumlah seluruh warehouse dibedakan dari kualitas filter aktif dan snapshot audit batch. CSV mempertahankan filter dan header saat hasil kosong. Tidak ada upload. | `main.py`, `Pages.jsx` |
| ETL manual | Siap, belum dijalankan pada DB aktif | Warehouse berisi data membutuhkan hash isi saat ini. Perubahan jenis sumber memerlukan konfirmasi CLI terpisah. Load tetap transaksional melalui loader CP2. | `backend/app/etl_control.py`, `etl/import_data.py` |
| Database kosong / koneksi gagal | Siap | Pesan informatif, tanpa KPI atau grafik contoh. Gangguan SQL menghasilkan HTTP 503, tanpa fallback CSV. | `main.py`, `App.jsx` |
| Docker | Build dan koneksi terisolasi lulus | Image baru diuji tanpa mengganti service aktif. `npm ci` memakai lockfile lintas Windows/Linux. | `frontend/Dockerfile`, `frontend/package-lock.json` |
| Dataset aktual | Kontrak disiapkan | Dua formulir memakai parser, dimensi, fakta, dan API yang sama. Sumber privat terpisah dari sample/Git. Akses publik tetap dibatasi sampai kontrol akses tersedia; definisi tidur aktual masih memerlukan konfirmasi. | `etl/import_data.py`, `etl_control.py`, `main.py` |

Filter ID, tanggal, provinsi, kota, jenis kelamin, usia, sesi, dan pekerjaan diterapkan pada KPI, grafik, tabel, statistik kualitas pilihan dan ekspor yang sesuai. Opsi filter dibaca dari warehouse. Baseline merupakan eksperimen terpisah; filter global disembunyikan di dua halaman baseline agar tidak memberikan kesan metriknya berubah mengikuti filter.

Grain tetap: profil = satu ID; perilaku = satu ID-tanggal; sesi = satu ID-tanggal-Pagi/Malam. Sesi valid berarti memiliki sedikitnya satu SBP dan satu DBP yang diterima parser CP2. Pembacaan lain yang kosong tetap `NULL`. Batas lama 5.000 baris di serialisasi dan 200 baris pada tabel dihapus; tabel menampilkan 25 baris per halaman.

## Hasil pengujian

| Pemeriksaan | Hasil |
|---|---|
| Backend, ETL, API v2 dan CP3 - Windows / SQLite in-memory | 46 lulus, 1 modul kontrak API v1 dilewati eksplisit |
| Suite yang sama - PostgreSQL 16 sementara | 46 lulus, 1 modul v1 dilewati |
| Suite yang sama - Python 3.12 Linux Docker, repo read-only | 46 lulus, 1 modul v1 dilewati |
| React component tests | 6 lulus: kosong, angka API berbeda dari fixture, filter/ekspor, 8 halaman, error independen, pagination dan missing |
| Vite production build | Lulus |
| Docker backend dan frontend build | Keduanya lulus |
| HTTP Nginx -> FastAPI -> PostgreSQL sementara | Health, HTML/aset, KPI vs SQL, filter gabungan Pagi/Malam, ekspor, empty result, ketiadaan endpoint impor, baseline artefak lulus |
| ETL fixture terbaru pada PostgreSQL sementara | 19 profil; 570 harian; 1.140 sesi valid = 570 Pagi + 570 Malam; 30 tanggal; 0 orphan |
| Missing yang dipertahankan | Tidur 6; duduk 3; jumlah merokok 550; hari aktif mingguan profil kosong 0 setelah CP2 baru |
| Konsistensi rata-rata seluruh sesi valid | SBP 118,9 / DBP 72,6 mmHg, cocok dengan SQL setelah pembulatan 1 desimal |
| CSV export | 19 profil / 570 harian / 1.140 sesi, missing tetap sel kosong |

Kasus backend mencakup perubahan jumlah data langsung di DB (20 profil / 571 harian / 1.141 sesi), kecocokan ID tepat (`SIM001` tidak mengambil `SIM0010`), filter tidak valid, sesi tidak lengkap, larangan data aktual pada API publik, serta penolakan load tanpa hash atau dengan hash salah. Kontrak v1 yang sudah dihentikan tidak dihitung sebagai tes lulus.

Bukti: [verification.json](../reports/cp3_stage1/verification.json), [isolated_warehouse.json](../reports/cp3_stage1/isolated_warehouse.json), dan [dry_run/quality.json](../reports/cp3_stage1/dry_run/quality.json). Prepared hash CP2 dan hash isi natural warehouse adalah dua audit berbeda; hanya `natural_content_sha256` dari warehouse target yang dipakai sebagai prasyarat penggantian data.

Tes komponen mengganti renderer Plotly yang membutuhkan browser dengan probe; komponen dashboard, filter, transformasi grafik dan pemanggilan API tetap asli. Build produksi memakai Plotly asli. Belum dilakukan pemeriksaan visual manual/browser end-to-end. Build memberi peringatan bundle Plotly sekitar 4,89 MB / 1,48 MB gzip. Suite backend memberi peringatan deprecation Starlette/httpx; tidak menyebabkan kegagalan. Optimasi bundle dan migrasi dependency tidak dikerjakan pada Tahap 1.

## Cara menjalankan ulang pemeriksaan

Jalankan dari root project memakai lingkungan Python project yang sudah berisi `backend/requirements-dev.txt`:

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests -q -p no:cacheprovider
.\.venv\Scripts\python.exe -m etl.import_data --synthetic --dry-run --summary
Push-Location frontend
npm ci --no-audit --no-fund
npm test
npm run build
Pop-Location
```

Suite default memakai SQLite in-memory, bukan database aktif. Untuk pengujian PostgreSQL, gunakan pola container sementara pada README dan `CP2_TEST_DATABASE_URL=postgresql+psycopg://postgres@127.0.0.1:<PORT_TEST>/toba_cp2_test`; nama variabel CP2 dipertahankan karena fixture bersama. Fixture menolak nama DB/host PostgreSQL selain target tes tersebut. Jangan mengarahkan suite ke database aktif karena fixture membuat dan menghapus tabel milik database tes.

## Panduan ETL manual

### 1. Validasi sumber tanpa mengubah database

```powershell
.\.venv\Scripts\python.exe -m etl.import_data --source-kind synthetic --dry-run --summary --report-dir reports/cp3_stage1/dry_run
```

Dua sumber default adalah `data/sample/Data_Responden_Sintetis.csv` dan `data/sample/Data_Harian_Sintetis.csv`. Dry-run tidak membuka koneksi database. Mode tanpa `--commit` selalu dry-run. Periksa audit kelengkapan, karantina, konsistensi dan sumber sebelum menyetujui load. File mentah tidak ditimpa.

Untuk data aktual, gunakan file privat di luar `data/sample` dan Git, dengan header/skema CP2:

```powershell
python -m etl.import_data --profile 'D:\DATA_PRIVAT\profil.csv' --daily 'D:\DATA_PRIVAT\harian.csv' --source-kind actual --dry-run --summary
```

Contoh path harus diganti lokasi yang benar. Ini hanya validasi, bukan persetujuan untuk mengganti sumber aktif. ETL menolak file `data/sample` yang diklasifikasikan sebagai aktual. Nilai tidur aktual tidak diasumsikan sebagai durasi HH:MM sintetis. Jangan menghapus missing atau menjadikannya nol untuk memperoleh grafik lengkap.

### 2. Periksa target dan minta persetujuan pemuatan

Pilih `DATABASE_URL` secara eksplisit pada sesi shell, tanpa mengedit `.env`. Jangan mengandalkan default SQLite. Jangan menaruh password di Git, laporan, atau tangkapan layar.

```powershell
$env:DATABASE_URL = Read-Host 'DATABASE_URL target yang telah diperiksa'
python -m etl.verify_warehouse --output reports/cp3_stage1/target_before.json
```

`verify_warehouse` hanya SELECT/introspeksi dan memakai transaksi READ ONLY pada PostgreSQL. Periksa nama target, jenis sumber, jumlah data, orphan, dan `natural_content_sha256`. Backup serta tinjau sumber dan target sebelum meminta persetujuan pemuatan. **Pekerjaan CP3 ini tidak menjalankan langkah penggantian pada warehouse aktif.**

### 3. Terapkan hanya setelah disetujui

Perintah berikut mengganti isi **tabel warehouse v2**, bukan merge. Karena itu jangan menjalankannya tanpa persetujuan target/dataset yang spesifik. Tidak ada penghapusan database, volume, atau tabel legacy. Untuk target yang sudah berisi data, gunakan hash dari pemeriksaan tepat sebelum load:

```powershell
# HANYA SETELAH DISETUJUI; ganti placeholder dengan hash natural target.
python -m etl.import_data --source-kind synthetic --commit --summary --expected-current-hash '<HASH_NATURAL_TARGET_YANG_DISETUJUI>'
python -m etl.verify_warehouse --output reports/cp3_stage1/target_after.json
```

Target kosong boleh diisi dengan `--commit` tanpa hash, tetapi pemilihan target dan persetujuan tetap tanggung jawab pengelola. Target berisi data tanpa hash, hash tidak cocok, atau perubahan jenis sumber tanpa `--allow-source-change` ditolak sebelum penggantian. PostgreSQL memakai advisory transaction lock untuk menserialkan pemanggilan CLI ini. `--allow-source-change` bukan persetujuan otomatis dan tidak menggabungkan sintetis dengan aktual.

Untuk dataset aktual setelah persetujuan, tambahkan path `--profile`, `--daily`, `--source-kind actual`, hash target, serta `--allow-source-change` bila jenis sumber berubah. Dashboard publik akan menolak akses aktual sampai autentikasi/kontrol akses dikerjakan; jangan mematikan guard untuk memaksa tampil. API dan komponen analitiknya tetap memakai kontrak yang sama.

### 4. Jika PostgreSQL hanya tersedia di jaringan Docker

Compose tidak mempublikasikan port PostgreSQL. Gunakan image tooling pada jaringan Docker target, bukan mengubah `.env` atau membuka port DB aktif. Bangun tooling terpisah dan pilih jaringan yang benar dari inspeksi container DB:

```powershell
docker build -f backend/Dockerfile.cp2 -t toba-cp2-check ./backend
$cp3Root = (Get-Location).Path
$cp3Network = Read-Host 'Nama network Docker target yang sudah diperiksa'
$env:DATABASE_URL = Read-Host 'DATABASE_URL dari dalam network target'
docker run --rm --network $cp3Network --env DATABASE_URL -v "${cp3Root}:/workspace:ro" toba-cp2-check python -m etl.verify_warehouse
docker run --rm --network $cp3Network --env DATABASE_URL -v "${cp3Root}:/workspace:ro" toba-cp2-check python -m etl.import_data --synthetic --dry-run --summary
```

Untuk commit yang telah disetujui, gunakan pemanggilan tooling yang sama dengan argumen langkah 3. Mount sumber tetap read-only. Data aktual memerlukan mount privat read-only yang terpisah. Perintah pada bagian ini tidak dijalankan terhadap service aktif dalam pekerjaan ini.

### 5. Membaca hasil pada dashboard

Setelah kode baru diterapkan dan ETL telah disetujui/dijalankan, klik **Muat ulang data**. UI mengambil `/api/meta` dan `/api/analytics` lagi. Tidak perlu menulis ulang struktur dashboard ketika dua sumber aktual memakai kontrak CP2.

Build image pengujian `toba-cp3-stage1-backend` dan `toba-cp3-stage1-frontend` sudah berhasil. Service Compose aktif belum dibangun ulang/restart selama pekerjaan ini. Penerapan kode lewat Compose merupakan langkah operasional terpisah; tidak memuat ulang data secara otomatis. Jangan memakai `down -v`, reset, atau drop database.

## Kondisi warehouse aktif dan batas pekerjaan

Warehouse aktif tetap berisi 19 profil / 570 harian / 1.140 sesi dari hasil ETL lama, dengan 19 profil `active_days_week` kosong. Hash natural aktif sebelum/sesudah diperiksa dan sama; lihat `verification.json`. Hasil ETL terbaru pada database sementara memperbaiki kelengkapan kolom ini menjadi nol missing. Halaman Kelola Data akan menjelaskan bila snapshot audit CP2 belum dimuat.

Tidak ada `.env`, notebook CP2, kode/artefak baseline ML, atau CSV sumber yang diubah pada Tahap 1. Tidak ada load/restart service aktif, reset/hapus DB/volume, commit atau push. Container/jaringan sementara milik pengujian dihentikan setelah verifikasi; image ber-tag pengujian dapat dipakai ulang. Autentikasi, training tiga algoritma, tuning, notebook/model baru, upload website dan CP3 tahap berikutnya tidak dikerjakan.

## File yang berubah pada Tahap 1

| Kelompok | File |
|---|---|
| Serving/API | `backend/app/main.py`, `backend/app/analytics_v2.py` |
| Kontrol ETL | **baru** `backend/app/etl_control.py`; `etl/import_data.py` |
| Backend tests | **baru** `backend/tests/test_cp3_stage1.py`; `backend/tests/test_api_v2.py`, `backend/tests/test_api.py` (penandaan kontrak v1 usang) |
| React | `frontend/src/App.jsx`, `frontend/src/pages/Pages.jsx`, `frontend/src/components/Common.jsx`, `frontend/src/components/FilterBar.jsx`, `frontend/src/styles.css` |
| Build/tests frontend | `frontend/package.json`, **baru** `frontend/package-lock.json`, **baru** `frontend/tests/dashboard.test.mjs`, `frontend/Dockerfile` |
| Dokumentasi/bukti | `README.md`, **baru** `docs/CP3_STAGE1.md`, **baru** `reports/cp3_stage1/verification.json`, `isolated_warehouse.json`, `dry_run/*` |

Perubahan CP2 yang sudah ada sebelumnya pada working tree dipertahankan. Daftar `git status` juga mencakup pekerjaan CP2 tersebut; jangan menganggap seluruh diff Git sebagai perubahan baru Tahap 1. Komponen lama `pages/Dashboard.jsx`, `pages/OtherPages.jsx`, `components/Charts.jsx`, `Filters.jsx`, `DataTable.jsx` tidak dirender oleh `App.jsx`; alur aktif menggunakan `pages/Pages.jsx`, `components/Common.jsx`, `FilterBar.jsx`, dan `Visuals.jsx`.
