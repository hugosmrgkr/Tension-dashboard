# Laporan Verifikasi Akhir P0/P1 — Toba Health Insight

Tanggal pengujian: **10 November 2026**. Lingkungan: sandbox Linux sekali-pakai milik Claude (Ubuntu 24, Python 3.12.3, Node v22.23.4, PostgreSQL 16 di-install baru untuk sesi ini). **Tidak ada database aktif/produksi yang disentuh** — seluruh pengujian memakai SQLite in-memory atau database PostgreSQL sekali-pakai yang dibuat dan hanya ada di sandbox ini (`toba_cp2_test`, `toba_browser_demo`).

Semua hasil di bawah ini **benar-benar dijalankan pada sesi ini**, bukan disalin dari laporan audit sebelumnya. Bukti mentah ada di `reports/p0_p1_reverify/`.

## 1. Lingkungan pengujian

| Komponen | Versi |
|---|---|
| OS | Ubuntu 24.04 (container) |
| Python | 3.12.3 |
| Node.js | v22.23.4 |
| PostgreSQL | 16.15 (di-install baru untuk sesi verifikasi ini) |
| numpy / pandas / scikit-learn / joblib | 2.5.4 / 3.1.1 / 1.9.1 / 1.6.0 |

## 2. Perintah yang dijalankan dan hasilnya

### 2.1 Backend — SQLite in-memory (default)

```
.venv/bin/python -m pytest backend/tests -q -p no:cacheprovider
```
**Hasil: 73 passed, 1 skipped.** Dijalankan 3× pada sesi ini (awal, setelah insiden/pemulihan, dan konfirmasi akhir); hasil konsisten setiap kali. Bukti: `backend-reverify.xml`, `backend-sqlite-reverify-final.xml`.

Satu kegagalan transien sempat muncul pada percobaan pertama: `test_private_paths_cannot_be_accidentally_added_to_git` gagal karena arsip ZIP yang diunggah tidak menyertakan folder `.git` (ZIP adalah ekspor file, bukan clone Git, sehingga `git check-ignore` tidak dapat dijalankan). Ini diverifikasi **bukan bug aplikasi**: folder `.git` diinisialisasi secara lokal pada sesi ini dan kelima pola jalur privat (`data/actual/`, `data/private/`, `.env.local`, `.env.production`, `credentials.json`) dikonfirmasi benar diabaikan oleh `.gitignore` menggunakan `git check-ignore` langsung, sebelum pytest dijalankan ulang dan lulus penuh.

### 2.2 Backend — PostgreSQL 16 asli (database sekali-pakai)

```
export CP2_TEST_DATABASE_URL="postgresql+psycopg://postgres:postgres@127.0.0.1:5432/toba_cp2_test"
.venv/bin/python -m pytest backend/tests -q -p no:cacheprovider
```
**Hasil: 73 passed, 1 skipped.** Dijalankan 3× pada sesi ini; hasil konsisten. Bukti: `backend-postgres-reverify.xml`, `backend-postgres-reverify-final.xml`. Database `toba_cp2_test` dibuat khusus untuk sesi ini sesuai guard eksplisit pada `backend/tests/conftest.py` (menolak berjalan jika `CP2_TEST_DATABASE_URL` menunjuk ke nama database yang terlihat seperti produksi), lalu dihapus di akhir sesi — tidak pernah menyentuh warehouse aktif.

### 2.3 ETL dry-run sintetis

```
.venv/bin/python -m etl.import_data --synthetic --dry-run --summary
```
**Hasil:** profil 19/19 diterima, 0 dikarantina; harian 570/570 diterima, 0 dikarantina; sesi 1.140/1.140 valid, 0 parsial. Bukti: `etl-dry-run.json`.

### 2.4 Frontend — unit test

```
npm test   # node --test tests/dashboard.test.mjs
```
**Hasil: 10/10 passed, 0 failed.** Dijalankan 2× pada sesi ini; hasil konsisten. Bukti: `frontend-test.log`.

### 2.5 Frontend — production build

```
npm run build
```
**Hasil: sukses**, 1.592 modules, `dist/assets/index-aka-j8hL.js` (4.910,84 kB, gzip 1.489,54 kB). Hash nama bundle (`aka-j8hL`) **identik** pada kedua kali build sesi ini, dan identik dengan yang dicatat `P0_P1_FINAL_AUDIT.md` sebelumnya — mengonfirmasi kode yang diaudit sebelumnya dan yang diverifikasi sesi ini adalah kode sumber yang sama persis. Bukti: `frontend-build.log`.

### 2.6 Integration smoke test — backend + frontend berjalan nyata (tanpa Docker)

Docker tidak tersedia di sandbox kerja (tidak ada Docker daemon), sehingga stack `compose.p0-p1-audit.yaml` tidak bisa dijalankan apa adanya. Sebagai gantinya:

1. Database PostgreSQL sekali-pakai baru (`toba_browser_demo`) dibuat dan dimuat dengan fixture sintetis melalui `python -m etl.import_data --synthetic --commit --summary` (hasil sama seperti 2.3, di atas, kali ini dengan `--commit`).
2. Backend dijalankan langsung: `uvicorn app.main:app --host 127.0.0.1 --port 8000`.
3. Frontend dijalankan langsung: `npm run preview -- --host 127.0.0.1 --port 4173 --strictPort` (proxy bawaan Vite meneruskan `/api/*` dan `/health` ke `localhost:8000`, konfigurasi yang sama seperti produksi/Docker).
4. Seluruh endpoint API yang dipakai 8 halaman dashboard diuji manual via `curl` melalui proxy frontend (`http://127.0.0.1:4173`), bukan langsung ke backend, untuk meniru jalur akses pengguna sesungguhnya.

**Hasil (lihat `api-smoke-test.log` untuk output lengkap):**

| Endpoint | Status | Catatan |
|---|---|---|
| `GET /health` | 200 | `{"status":"ok","database":"postgresql"}` |
| `GET /api/meta` | 200 | 19 partisipan, 570 harian, 1.140 sesi; provinsi/kota sesuai formulir, **tanpa** field kecamatan |
| `GET /api/analytics` | 200 | 1.059.086 bytes |
| `GET /api/quality` | 200 | 32.246 bytes |
| `GET /api/model/baseline` | 200 | 5.305 bytes |
| `GET /api/model/predict-baseline?respondent_id=SIM001` | 200 | `prediction_mmHg:119.75`, `target_approved:false`, `is_diagnosis:false`, `artifact_run_id:"5d3bed0d6591cd2bc09d"` |
| `GET /api/data/export/sessions` | 200 | 95.356 bytes, kolom `sbp1/dbp1/sbp2/dbp2/review_status` sesuai grain P0-02 |
| `GET /api/data/export/daily` | 200 | 128.797 bytes |
| `GET /api/data/export/participants` | 200 | 2.027 bytes |
| `GET /` (index statis) | 200 | halaman dashboard termuat |

**Tidak dijalankan pada sesi ini:**
- **Playwright/browser E2E** (`npm run test:browser`) — tidak dapat dijalankan karena unduhan binary Chromium diblokir oleh kebijakan jaringan sandbox kerja (hanya domain pypi/npm/github yang diizinkan, bukan domain distribusi Playwright). Smoke test manual di atas adalah pengganti sebagian (membuktikan API bekerja benar dari balik proxy frontend), **bukan pengganti penuh** test interaksi UI/browser sungguhan.
- **Gladi bersih Docker Compose penuh** (`scripts/start_cp3_demo.ps1`, port 8081/8082) — tidak dapat dijalankan karena Docker daemon tidak tersedia di sandbox kerja.

Kedua keterbatasan ini murni keterbatasan lingkungan kerja sesi ini, bukan temuan kegagalan aplikasi — dan sudah dicatat sebagai catatan jujur, bukan diklaim lulus.

### 2.7 Integritas artefak ML

```
.venv/bin/python -m etl.verify_audit_checkout --output reports/p0_p1_reverify/checkout-reverify.json
```
**Hasil:** pada checkout Git mode LF maupun CRLF, `run_id` = `5d3bed0d6591cd2bc09d`, status prediksi 200, hash biner model **tidak berubah** (`binary_sha256_unchanged: true`) dibanding artefak yang sudah diaudit.

### 2.8 Reproduksi metrik baseline (di folder sementara, tidak menimpa artefak asli)

Dijalankan langsung memanggil `run_experiment(...)` dengan `out_dir`/`report_dir` diarahkan ke `/tmp/...`, **bukan** ke `models/` produksi (lihat bagian 3 di bawah untuk alasan kehati-hatian ini).

**Hasil, identik dengan `models/baseline_metrics.json` yang diaudit:**

| Model | MAE | RMSE | R² |
|---|---|---|---|
| Naive 7-day mean | 1,933673 | 2,234723 | 0,850309 |
| Linear Regression | 2,575492 | 3,113985 | 0,709343 |

`rows_training=60`, `rows_test=7` — sama persis dengan dokumentasi sebelumnya. Bukti: `baseline-reproduction.json`.

## 3. Insiden selama verifikasi dan penanganannya

Pada awal sesi ini, perintah `python -m etl.verify_baseline` sempat dijalankan untuk memverifikasi reproducibility. Skrip ini **secara default menulis ke folder produksi `models/`** dan `docs/CP3_BASELINE_REPORT.md`, bukan ke folder sementara — sehingga sempat **menimpa artefak ML asli yang sudah diaudit** dengan hasil retraining baru (skor metrik identik, tapi `run_id`/provenance berbeda karena perbedaan versi library terpasang). Ini terdeteksi dalam beberapa langkah berikutnya (dua pemanggilan fungsi yang seharusnya deterministik memberi hasil berbeda), diselidiki sampai akar penyebab ditemukan, lalu **seluruh file yang terdampak dipulihkan byte-demi-byte** dari arsip ZIP asli yang diunggah pengguna. Pemulihan dikonfirmasi dengan kecocokan SHA-256 dan `diff -rq` menyeluruh terhadap arsip asli. Rincian lengkap kronologi insiden ini ada di `docs/P0_P1_CHANGELOG.md` bagian 1. Semua langkah verifikasi setelahnya (2.1–2.8 di atas) dilakukan **setelah** pemulihan selesai dan dikonfirmasi bersih.

## 4. Jumlah lulus/gagal — ringkasan

| Jenis tes | Lulus | Gagal | Dilewati |
|---|---|---|---|
| Backend pytest (SQLite) | 73 | 0 | 1 |
| Backend pytest (PostgreSQL asli) | 73 | 0 | 1 |
| Frontend unit test | 10 | 0 | 0 |
| Frontend build | sukses | – | – |
| API smoke test manual | 10/10 endpoint | 0 | – |
| Playwright/browser E2E | tidak dijalankan (keterbatasan lingkungan) | – | – |
| Docker Compose gladi bersih | tidak dijalankan (keterbatasan lingkungan) | – | – |

**Tidak ada error yang ditemukan pada kode aplikasi.** Satu-satunya "error" yang ditemukan pada sesi ini disebabkan oleh tindakan verifikasi itu sendiri (lihat bagian 3), dan sudah diperbaiki sebelum laporan ini ditulis.

## 5. Batas pengujian

- Seluruh pengujian memakai **data sintetis/simulasi**, bukan data responden aktual — sesuai status proyek saat ini.
- Playwright/browser E2E dan gladi bersih Docker penuh tidak dapat dijalankan ulang pada sesi ini karena keterbatasan jaringan/Docker di sandbox kerja (lihat 2.6). Tim proyek perlu menjalankan keduanya sendiri sebelum demo ke dosen, menggunakan `scripts/start_cp3_demo.ps1` dan `npm run test:browser` sebagaimana didokumentasikan di `CP3_DEMO_SCRIPT.md`.
- Keputusan akademik (persetujuan target `future_7d_mean_sbp`, protokol jumlah pembacaan BP, semantik tidur formulir aktual, aturan penanganan anomali data aktual) **tetap di luar cakupan verifikasi teknis ini** — ini memang keputusan dosen, bukan sesuatu yang bisa "lulus tes".
- Verifikasi ini menguji bahwa kode **berjalan dan berperilaku sesuai yang didokumentasikan**; ini bukan audit keamanan penuh, bukan code review baris-per-baris menyeluruh pada seluruh basis kode, dan bukan jaminan kesiapan deployment publik.
