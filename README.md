# Toba Health Insight - Dashboard v1 CP3

**React + Vite + Plotly · FastAPI · PostgreSQL · Docker Compose**

Prototipe interaktif untuk eksplorasi pola pengukuran tekanan darah **pagi dan malam** serta faktor gaya hidup. Dashboard memakai **dua formulir sintetis**, bukan data penelitian aktual dan bukan alat diagnosis.

> **STATUS: DATA SINTETIS / SIMULASI.** Hasil tidak boleh dipakai sebagai kesimpulan kesehatan masyarakat maupun klaim performa pada pasien nyata.

## Audit final P0/P1 setelah commit CP3

**Ringkasan + panduan instalasi (10 Nov 2026):** [docs/RINGKASAN_PERBAIKAN_P0_P1_DAN_INSTALASI.md](docs/RINGKASAN_PERBAIKAN_P0_P1_DAN_INSTALASI.md) — penjelasan status tiap item P0/P1, apa yang masih butuh keputusan dosen, dan cara instalasi Python/Node/PostgreSQL untuk jalur Docker maupun non-Docker.

Laporan paling baru: [docs/P0_P1_FINAL_AUDIT.md](docs/P0_P1_FINAL_AUDIT.md). Gate BP/API/model kini satu definisi; responden aktif dihitung dari ID-harian, dibedakan dari ID dengan BP valid. Pasangan silang, parsial atau tidak konsisten memakai `pending_review`, bukan klaim klinis. Duplikat konflik tidak memilih baris pertama.

Artefak memakai manifest v3 dengan hash teks UTF-8/LF dan hash binary joblib ketat; `.gitattributes` menjaga checkout. Jangan menyunting metrik/hash manual atau melewati validasi. Sintetis dan aktual tetap terpisah; actual/private/raw serta dotenv/kredensial dilindungi Git. Quality gate aktual yang belum lolos review akan menolak commit.

Laporan CP2/CP3 berikut adalah riwayat. Untuk definisi yang berubah, gunakan audit final dan dictionary terbaru. Uji kandidat checkout memakai repo/index temporary, bukan commit/push ke repo ini.

## CP3 final - demo tengah siap pada DATA SINTETIS

Laporan final: [CP3_FINAL_REPORT.md](docs/CP3_FINAL_REPORT.md). Baseline: [CP3_BASELINE_REPORT.md](docs/CP3_BASELINE_REPORT.md). Persiapan presentasi: [CP3_DEMO_SCRIPT.md](docs/CP3_DEMO_SCRIPT.md), [checklist](docs/CP3_CHECKLIST.md), [progres](docs/CP3_PROGRESS_REPORT.md), [rencana CP4-CP5](docs/CP3_NEXT_STEPS.md).

Dari root dengan Docker Desktop aktif, tanpa mengubah `.env` atau warehouse aktif:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start_cp3_demo.ps1
```

Buka **http://127.0.0.1:8081**; Swagger **http://127.0.0.1:8001/api/docs**. Stack `toba-cp3-demo` memiliki PostgreSQL RAM terpisah. Script hanya memuat fixture bila DB demo kosong; DB berisi data tidak diganti. Jangan hentikan db demo saat presentasi. Service/volume lama pada 8080 tidak dipakai untuk demo final.

Baseline terverifikasi: target usulan tetap `future_7d_mean_sbp`, **belum disetujui final dosen**. Split utama memisahkan ID dan waktu serta target test non-overlap: **60 train / 7 test**; test sintetis sangat kecil. Metrik diperoleh dari eksperimen aktual dan manifest, bukan angka UI. Skema lama 204/119 hanya sensitivitas. Notebook utama [03_verifikasi_baseline_cp3.ipynb](notebooks/03_verifikasi_baseline_cp3.ipynb); notebook 01 merupakan catatan awal.

```powershell
# Reproduksi offline: secara eksplisit memperbarui model/laporan sintetis; tidak membuka DB.
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-cp3.txt
.\.venv\Scripts\python.exe -m etl.execute_cp3_notebook
# Alternatif tanpa Jupyter: python -m etl.verify_baseline
.\.venv\Scripts\python.exe -m etl.verify_cp3_demo
.\.venv\Scripts\python.exe -m pytest backend/tests -q -p no:cacheprovider
Push-Location frontend
npm ci --no-audit --no-fund
npm test
npm run build
$env:CP3_BROWSER_BASE_URL='http://127.0.0.1:8081'
$env:CP3_REPORT_DIR='../reports/cp3_final'
npm run test:browser
Pop-Location
```

Bukti final: [verification.json](reports/cp3_final/verification.json), XML tes, [hasil browser](reports/cp3_final/browser-results.json), [screenshot nyata](reports/cp3_final/screenshots/), dan [hasil eksperimen](reports/cp3_baseline/experiment.json). Kelulusan teknis sintetis berbeda dari data primer/izin/persetujuan dosen, tuning/tiga algoritma dan deployment publik yang masih perlu pekerjaan berikutnya. Artefak `models/` diperbarui sesuai tugas Tahap 3; service lama yang bind-mount folder ini dapat membaca JSON kompatibel baru walau tidak di-restart.

## Riwayat CP3 Tahap 1-2

Bagian berikut mencatat hasil tahap sebelumnya; baseline dan bukti paling baru mengikuti finalisasi di atas.

## CP3 Tahap 2

Penyempurnaan delapan halaman, katalog visualisasi, drill-down/cross-filter, hasil browser desktop/mobile, serta matriks kesesuaian kedua PDF: [docs/CP3_STAGE2.md](docs/CP3_STAGE2.md). Bukti: [reports/cp3_stage2/verification.json](reports/cp3_stage2/verification.json). Kode baru belum mengganti service Compose aktif; tidak ada ETL commit atau perubahan baseline ML.

## CP3 Tahap 1

Implementasi, hasil pengujian, daftar file, batasan, dan panduan ETL: [docs/CP3_STAGE1.md](docs/CP3_STAGE1.md). Bukti mesin: [reports/cp3_stage1/verification.json](reports/cp3_stage1/verification.json).

**Status:** kode integrasi selesai dan diuji terisolasi. Service Docker aktif belum dibangun ulang dan warehouse aktif belum di-load ulang; penerapan ETL aktif menunggu persetujuan.

## Deployment lokal biasa (terpisah dari demo CP3 final)

```powershell
# dari folder project
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
# untuk volume lama, PERTAHANKAN password yang dipakai PostgreSQL lama
# untuk pemasangan baru, ubah password di .env sebelum pertama kali start

docker compose up --build -d
docker compose ps
```

- Frontend: **http://localhost:8080**
- Swagger FastAPI: **http://localhost:8080/api/docs**
- Health: **http://localhost:8080/health**
- Hentikan tanpa menghapus database: `docker compose down`

**Jika sudah pernah menjalankan versi Streamlit→React sebelumnya:** Compose v2 membuat tabel baru dengan suffix `_v2` dan tidak menghapus tabel lama. **Jangan gunakan `docker compose down -v`** karena menghapus data volume PostgreSQL. Jika perlu migrasi data lama, lakukan backup dan audit terlebih dahulu. Uji di lingkungan lokal, bukan di deployment publik.

### Teman satu kelompok

Clone repository, jalankan Docker Desktop, buat konfigurasi lokal dari `.env.example` hanya jika belum ada, lalu jalankan Compose. Warehouse baru tetap kosong sampai ETL manual dijalankan. Tidak ada auto-seed. Dua CSV sintetis menghasilkan 19 profil, 570 catatan harian, dan 1.140 sesi setelah validasi.

Panduan layar demi layar: [`docs/PANDUAN_PENGGUNA.md`](docs/PANDUAN_PENGGUNA.md).

## Cara membaca dashboard (8 halaman)

| Halaman | Apa yang dilihat | Penjelasan |
|---|---|---|
| Dashboard | 4 KPI dan 4 grafik utama | Responden, catatan ID×tanggal, sesi, dan rerata sistolik. Garis Pagi/Malam tidak menghitung jumlah orang dua kali. |
| Data Partisipan | Profil anonim | ID pseudonim, demografi, BMI turunan dan jumlah hari pencatatan. |
| Analisis Faktor Risiko | Grafik gaya hidup | Tidur, stres 1–5, aktivitas menit, makanan asin, buah, sayur, kafein, dan treemap aktivitas. Hanya asosiasi. |
| Tren Tekanan Darah | Tren sesi dan bacaan mentah | Dua pembacaan tetap tersedia. Pilih satu ID untuk menelusuri sesi internal. |
| Prediksi Hipertensi | Baseline regresi | Tombol memilih ID dan menghitung **rata-rata SBP 7 hari sebelumnya** sebagai estimasi rata-rata 7 hari berikutnya. Bukan diagnosis hipertensi. |
| Evaluasi Model | Metrik awal | MAE/RMSE/R² baseline naif vs Linear Regression, group split berdasarkan responden, aktual-vs-prediksi dan residual. **Hanya simulasi.** |
| Laporan & Ringkasan | 5 poin deskriptif | Semua pernyataan berasal dari agregat filter aktif, bukan temuan populasi. |
| Kelola Data | Audit dan unduh | Sumber PostgreSQL, kualitas filter aktif, snapshot audit batch, ekspor CSV terfilter dan petunjuk ETL manual. Tidak ada upload website. |

**Filter global:** ID responden, periode tanggal, provinsi, kabupaten/kota, jenis kelamin, kelompok usia, sesi, pekerjaan. KPI, tabel, visualisasi deskriptif dan ekspor mengikuti filter. Halaman baseline mempertahankan artefak eksperimen dan diberi pemberitahuan terpisah; filter tidak menghitung ulang model.

## Data dan desain warehouse

- Form Awal: 19 profil / 24 kolom; `respondent_id` unik.
- Form Harian: 570 ID×tanggal / 28 kolom, dua sesi per hari; 1.140 fakta sesi.
- 3 dimensi: `dim_participant_v2`, `dim_date_v2`, `dim_session_v2`.
- 2 fakta: `fact_bp_session_v2` (ID×tanggal×sesi) dan `fact_daily_behavior_v2` (ID×tanggal).
- Sumber utama `data/sample/Data_Responden_Sintetis.csv` + `data/sample/Data_Harian_Sintetis.csv`, tidak digabung secara destruktif. Workbook gabungan hanya referensi alternatif.
- CSV sintetis tidur `06:31` diinterpretasi **6 jam 31 menit** untuk demo. Data aktual tidak dikonversi sampai semantik pertanyaan dikonfirmasi.
- Nama asli/teks `Nama lengkap` tidak masuk database analitik/API. ID digunakan untuk relasi.

Data dictionary: `docs/DATA_DICTIONARY.md`; ERD: `docs/ERD.md`; pencapaian checkpoint: `docs/CHECKPOINT_M6_M8.md`.

## Baseline model yang dapat diulang

Metrik di `models/baseline_metrics.json` dihasilkan oleh kode `backend/app/baseline.py`. Menyertakan model pembanding `models/linear_regression_synthetic.joblib`. Notebook `notebooks/01_baseline_regresi.ipynb` adalah catatan awal. Hasil verifikasi final memakai `notebooks/03_verifikasi_baseline_cp3.ipynb` dan split ID/waktu yang lebih ketat.

```powershell
# jika ingin menjalankan ulang eksperimen di Python lokal
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements-dev.txt
$env:PYTHONPATH = (Resolve-Path backend).Path
python -c "from app.baseline import run_experiment; print(run_experiment('data/sample/Data_Responden_Sintetis.csv','data/sample/Data_Harian_Sintetis.csv','models')['scores'])"
```

Model hanya untuk M6–M8; pemilihan target final, pelatihan tiga algoritma, tuning, dan penilaian atas data aktual masih bergantung pada kelayakan data/persetujuan dosen.

## ETL dan test

```powershell
$env:PYTHONPATH = (Resolve-Path backend).Path
python etl/import_data.py --synthetic --dry-run  # hanya memeriksa, tidak mengubah DB
python -m pytest backend/tests/test_api_v2.py -q
```

## CP2 — Data Readiness (selesai teknis pada fixture sintetis)

Laporan utama: [docs/CP2_DATA_READINESS.md](docs/CP2_DATA_READINESS.md). Dictionary seluruh **52 kolom sumber**, audit sebelum–sesudah, lima temuan EDA, sepuluh gambar, dan bukti pemeriksaan warehouse berada di `docs/` serta `reports/cp2/`. Angka hasil ini hanya **SIMULASI**, bukan bukti kesiapan data penelitian aktual.

### Windows / VS Code

Jalankan dari root project pada lingkungan Python 3.12+; aktifkan `.venv` yang dipilih VS Code. Instal kebutuhan pengujian/Jupyter:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements-dev.txt
python -m etl.import_data --synthetic --dry-run --report-dir reports/cp2 --summary
python -m etl.data_readiness --synthetic
python -m etl.execute_eda
python -m pytest backend/tests/test_cp2.py backend/tests/test_api_v2.py -q -p no:cacheprovider
```

`data_readiness` menghitung ulang dokumentasi, JSON, tabel CSV, hash sumber, dan PNG EDA; tidak menghubungi database. Notebook `notebooks/02_eda_data_readiness.ipynb` juga dapat dibuka langsung di VS Code: **Select Kernel → .venv project → Run All**. Runner `execute_eda` memakai Python pemanggil dengan kernel sementara; tidak memasang kernel global. Notebook memproses sumber di memori dan tidak memuat model atau menimpa data mentah.

Output audit: `quality.json`, `completeness_before.csv`, `completeness_after.csv`, `issues.csv`, `source_manifest.json`. Output EDA: `eda_summary.json`, `descriptive_*.csv`, `correlation_daily.csv`, dan `figures/*.png`. Tidak ada salinan nama dari Form Awal. Karantina ditelusuri dengan nomor baris/alasan; file mentah tetap di lokasi asal.

`--dry-run` adalah default ETL. `--dry-run` dan `--commit` saling eksklusif. **`--commit` mengganti isi tabel v2 pada DATABASE_URL yang dipilih**; untuk verifikasi CP2 gunakan database sementara, bukan PostgreSQL aktif. Missing tidak diisi nol; label/satuan yang tidak sah dilaporkan; flag IQR tidak menghapus sesi.

### PostgreSQL terisolasi untuk tes integrasi

Contoh berikut membuat database terpisah di container sementara dengan port localhost acak dan storage RAM. Ia tidak memakai volume atau service `db` project. Test fixture menolak URL PostgreSQL selain `localhost`/`127.0.0.1` dengan nama database **toba_cp2_test**.

```powershell
$cp2Name = 'toba-cp2-test-' + [guid]::NewGuid().ToString('N').Substring(0,8)
docker run -d --rm --name $cp2Name --label toba.cp2.test=1 --publish 127.0.0.1::5432 --tmpfs /var/lib/postgresql/data -e POSTGRES_HOST_AUTH_METHOD=trust -e POSTGRES_DB=toba_cp2_test postgres:16-alpine
try {
    for ($attempt=0; $attempt -lt 30; $attempt++) {
        docker exec $cp2Name pg_isready -U postgres -d toba_cp2_test
        if ($LASTEXITCODE -eq 0) { break }
        Start-Sleep -Seconds 1
    }
    if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL tes belum siap' }
    $cp2Port = (docker port $cp2Name 5432/tcp).Split(':')[-1]
    $env:CP2_TEST_DATABASE_URL = "postgresql+psycopg://postgres@127.0.0.1:$cp2Port/toba_cp2_test"
    python -m pytest backend/tests/test_cp2.py backend/tests/test_api_v2.py -q -p no:cacheprovider
} finally {
    Remove-Item Env:CP2_TEST_DATABASE_URL -ErrorAction SilentlyContinue
    docker stop $cp2Name
}
```

Untuk mencoba CLI load pada **database sementara yang sama**, pilih `DATABASE_URL` test tersebut, lalu jalankan `python -m etl.import_data --synthetic --commit --summary` dan `python -m etl.verify_warehouse`. Jangan menyalin URL database aktif ke contoh commit. `verify_warehouse` sendiri hanya melakukan SELECT/introspeksi, memakai transaksi READ ONLY pada PostgreSQL, dan dapat menyimpan ringkasan dengan `--output path.json`.

### Tooling CP2 melalui Docker

Image tooling ini terpisah dari service aplikasi; tidak menjalankan `compose up`, reset, atau migrasi database aktif:

```powershell
docker build -f backend/Dockerfile.cp2 -t toba-cp2-check ./backend
$projectRoot = (Get-Location).Path
docker run --rm -v "${projectRoot}:/workspace:ro" toba-cp2-check
docker run --rm -v "${projectRoot}:/workspace:ro" toba-cp2-check python -m etl.import_data --synthetic --dry-run --summary
docker run --rm -v "${projectRoot}:/workspace:ro" -v "${projectRoot}/reports:/workspace/reports" -v "${projectRoot}/docs:/workspace/docs" toba-cp2-check python -m etl.data_readiness --synthetic
docker run --rm -v "${projectRoot}:/workspace:ro" -v "${projectRoot}/reports:/workspace/reports" -v "${projectRoot}/notebooks:/workspace/notebooks" toba-cp2-check python -m etl.execute_eda
```

Sumber `data/sample` tetap read-only pada perintah Docker di atas. Untuk membaca jumlah data deployment lama tanpa menyentuhnya:

```powershell
docker compose exec -T db psql -U toba -d toba_health -c "SELECT 'profiles' AS tabel, count(*) FROM dim_participant_v2 UNION ALL SELECT 'daily',count(*) FROM fact_daily_behavior_v2 UNION ALL SELECT 'sessions',count(*) FROM fact_bp_session_v2;"
```

Catatan historis CP2: kontrak v1 di `backend/tests/test_api.py` sudah dihentikan dan kini ditandai skip eksplisit. Suite aktif adalah CP2, API v2, dan CP3 Tahap 1. Tidak ada commit/push otomatis; warehouse aktif belum dimuat ulang.

Dashboard tanpa login hanya melayani data **sintetis**. Data aktual tetap memakai skema dan kontrak dashboard yang sama, tetapi akses API/ekspor publik dibatasi sampai kontrol akses tersedia. Endpoint impor website telah dihapus; `ENABLE_IMPORT` dan `IMPORT_TOKEN` dari konfigurasi lama tidak mengaktifkan upload. Gunakan CLI ETL yang mewajibkan persetujuan manual dan hash prasyarat untuk warehouse berisi data. Sumber privat harus disimpan terpisah dari fixture dan Git.

## Hal yang belum selesai (jangan salah klaim)

- Data **primer/aktual** yang tervalidasi; dataset sintetis **tidak memenuhi** syarat minimal 500 baris data primer.
- Persetujuan dosen atas target `future_7d_mean_sbp`, protokol pengukuran, definisi tidur dan kriteria responden.
- Eksperimen **minimal tiga** algoritma beserta tuning, validasi pada data aktual, model card final dan deployment model produksi.
- Deployment publik dengan autentikasi, perlindungan data, uji usability, dan pengujian keamanan.
- Full checklist visualisasi advance/interaksi M9–M10, final storytelling berbasis data aktual, dokumen akhir dan jurnal.

## Keamanan dan kolaborasi

Jangan commit `.env`, data kesehatan asli, nama/kontak responden, atau data mentah privat. Jangan hapus volume Docker tanpa backup. Gunakan pull request dan logbook kontribusi; deklarasikan penggunaan AI sesuai brief dosen. Aplikasi publik harus dibatasi pada agregasi yang tidak mengidentifikasi individu.
