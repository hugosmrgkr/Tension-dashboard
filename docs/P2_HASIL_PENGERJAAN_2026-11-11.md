# Hasil Pengerjaan P2 — Toba Health Insight

Tanggal: 11 November 2026 · Basis: arsip `mental-health-dashboard-source.zip` (folder `Tension-dashboard`) + dokumen serah terima `P0_P1_dan_Rencana_P2_Toba_Health_Insight.md`.

> **Semua model dan angka di dokumen ini adalah DATA SINTETIS / SIMULASI.** Target `future_7d_mean_sbp` belum disetujui dosen (`target_approved=false`). Tidak ada hasil di sini yang boleh dipakai sebagai klaim penelitian aktual atau diagnosis. Tidak ada data aktual yang diimpor.

## 1. Ringkasan status

| ID | Status | Intinya |
|---|---|---|
| P2-01 | **SELESAI (sintetis)** | Notebook `04_perbandingan_model_regresi.ipynb` + modul teruji; 3 algoritma + baseline naif; validasi leave-ID-out; tanpa leakage; reprodusibel; model card otomatis. |
| P2-02 | **SELESAI (sintetis)** | Endpoint `GET /api/model/predict` memakai artefak terverifikasi hash; paritas fitur training/inferensi diuji untuk seluruh window. |
| P2-03 | **SELESAI (sintetis)** | Halaman Evaluasi membaca artefak (bukan angka hardcode): validasi vs test, MAE/RMSE/R², aktual-vs-prediksi, residual, distribusi error, error per ID, peringatan sampel kecil. |
| P2-04 | **SELESAI** | Audit KPI: logika sudah benar; ditambahkan definisi tertulis (rumus, satuan, grain, filter, sumber) di API dan UI, plus 8 tes filter/periode. |
| P2-05 | **SELESAI (checklist otomatis)** | 10 tes browser baru (tooltip, cross-filter, reset, filter global, empty state, aksesibilitas dasar, ponsel). Audit visual manual penuh/pembaca layar belum dilakukan. |
| P2-06 | **SEBAGIAN** | Kode keamanan selesai dan teruji. **Konfigurasi Docker produksi, backup/restore, dan HTTPS belum dijalankan** (daemon Docker tidak aktif di lingkungan kerja). Wajib uji staging sebelum URL publik. |
| P2-07 | **SEBAGIAN (menunggu keputusan)** | Nama tampilan sudah konsisten dan dijaga tes. Nama folder/repository tidak diubah karena butuh konfirmasi tim/dosen; lihat `docs/BRANDING.md`. |
| P2-08 | **SELESAI untuk arsip ini** | Skrip `scripts/audit_repo.py` + tes: arsip bersih. Audit **repository Git sebenarnya** (`git ls-files`, riwayat commit) tetap harus dijalankan tim. |

## 2. Temuan penting (baca sebelum presentasi)

1. **Baseline naif mengalahkan semua model terlatih.** Pada data sintetis ini tidak ada algoritma yang lebih baik daripada rata-rata SBP 7 hari terakhir, baik di validasi maupun test. Ini temuan sah, bukan kegagalan; jangan menyebut model terlatih "lebih akurat".
2. **Sampel sangat kecil:** train 60 window dari 12 ID, test utama 7 origin dari 7 ID. Selisih antar-model tidak stabil dan tidak membuktikan generalisasi. UI dan model card menampilkan peringatan ini otomatis.
3. **Dokumen serah terima tidak cocok dengan arsip pada satu hal:** dokumen menyatakan menu `Prediksi Hipertensi` sudah diganti `Prediksi Tekanan Darah`, tetapi di arsip yang saya terima kode aktif (`Common.jsx`, `App.jsx`, tes) masih memakai nama lama. Saya menyelaraskannya sekarang. Bila teman Anda sudah mengubahnya di salinannya, gabungkan dengan hati-hati (konflik kecil di 4 berkas).
4. **Tes `test_private_paths_cannot_be_accidentally_added_to_git` gagal pada arsip tanpa folder `.git`** (bukan bug kode). Lulus di repository Git sungguhan.
5. Status P0/P1 **tidak diubah**: P0-01, P0-02, P0-04, P0-07 dan P1-08 tetap menunggu ekspor aktual dan keputusan dosen.

## 3. Hasil P2-01 (data sintetis, run `d43ac5c17c70cead67c7`, seed 42)

Split train/test identik baseline CP3 (ID held-out + purge label kronologis, cutoff 2026-09-18, target uji tidak overlap). Pemilihan model memakai validasi leave-ID-out 4 fold **di dalam train**; test dihitung sekali setelah pemilihan terkunci. Imputer median, scaler, dan model di-fit hanya pada data fit.

| Model | RMSE validasi | MAE validasi | RMSE test | MAE test | R² test |
|---|---:|---:|---:|---:|---:|
| Baseline naif (rerata 7 hari) | 2,377 | 1,908 | 2,235 | 1,934 | 0,850 |
| Linear Regression | 2,759 | 2,180 | 3,114 | 2,575 | 0,709 |
| Random Forest | 4,750 | 3,178 | 3,441 | 2,959 | 0,645 |
| HistGradientBoosting | 4,600 | 3,353 | 4,832 | 3,693 | 0,300 |

Satuan mmHg (R² tanpa satuan, bukan persen akurasi). Model terpilih berdasarkan aturan tetap (RMSE validasi terkecil di antara model terlatih) = **Linear Regression**, dan model itu **tidak** mengalahkan baseline naif pada validasi; endpoint P2-02 menampilkan peringatan ini bersama angka naif.

Hiperparameter tetap, tanpa tuning (tercatat di `MODEL_CARD.md`). Berkas CP3 (`models/*.joblib`, `reports/cp3_baseline`, notebook 01–03) **tidak diubah**.

## 4. Berkas baru dan berkas yang diubah

**Baru**
- `backend/app/model_comparison.py`, `backend/app/model_service.py`, `backend/app/security.py`
- `etl/run_model_comparison.py`, `notebooks/04_perbandingan_model_regresi.ipynb`
- `models/experiments/` (metrik, manifest, model terpilih, `MODEL_CARD.md`), `reports/p2_model_comparison/`
- `compose.prod.yaml`, `deploy/Caddyfile`, `deploy/production.env.example`, `scripts/make_secrets.py`, `scripts/backup_db.sh`, `scripts/restore_db.sh`, `scripts/audit_repo.py`
- `docs/BRANDING.md`, `docs/P2_DEPLOYMENT_RUNBOOK.md`, dokumen ini
- Tes: `test_p2_model_comparison.py`, `test_p2_model_api.py`, `test_p2_kpi.py`, `test_p2_security.py`, `test_p2_branding.py`, `test_p2_repo_hygiene.py`, `frontend/tests/browser/p2_interactions.spec.js`

**Diubah**
- `backend/app/main.py` (endpoint `/api/model/predict`, `/api/model/comparison`; middleware keamanan; CORS dari env; dokumentasi API dimatikan di staging/production)
- `backend/app/analytics_v2.py` (`kpi_definitions`, `comparison_definition`; logika KPI tidak berubah)
- `frontend/src/App.jsx`, `pages/Pages.jsx`, `components/Visuals.jsx`, `components/Common.jsx`, `lib/api.js`, `styles.css`; `frontend/tests/dashboard.test.mjs`, `tests/browser/dashboard.spec.js`
- `.gitignore`, `README.md`, `models/README.md`, `notebooks/README.md`

**Tidak disentuh:** `backend/app/baseline.py`, `pipeline.py`, `bp_policy.py`, endpoint `/api/model/baseline` dan `/api/model/predict-baseline` (tetap ada), kontrak ETL, `compose.yaml`, port 8080.

## 5. Detail per item

### P2-02 — Endpoint prediksi
- `GET /api/model/predict?respondent_id=...&asof_date=...` (read-only; metode lain 405).
- Memuat model hanya bila hash metrik dan model cocok dan nama fitur sesuai kontrak; jika tidak, **409** (gagal tertutup, tanpa angka pengganti).
- Validasi: ID wajib (1–40 karakter), tanggal valid, 7 hari kalender berturut-turut dengan SBP valid (422), ID tidak dikenal (404), sumber non-sintetis (409), kegagalan model (503).
- Respons memuat prediksi mmHg, pembanding naif, fitur yang dipakai, fitur diimputasi/di luar rentang training, metadata model (algoritma, versi/run, tanggal training, fitur, target, horizon, sumber data, `target_approved`, hash). `is_diagnosis=false`.
- Paritas: tes menghitung fitur inferensi untuk **setiap** window training dan mencocokkannya dengan `make_training`.

### P2-04 — KPI
Audit tidak menemukan galat hitung. Empat KPI (responden aktif, catatan harian, sesi valid, rerata SBP) cocok dengan baris sumber; sesi Pagi/Malam tidak menggandakan responden atau catatan harian; filter sesi hanya mengubah KPI sesi/SBP (terdokumentasi). Pembanding sama persis dengan query independen periode sebelumnya, mengikuti filter non-tanggal, dan **tidak muncul** tanpa kedua tanggal atau saat periode sebelumnya kosong. UI menampilkan blok "Definisi" per KPI.

### P2-05 — Interaksi grafik (bukti)
Dijalankan pada Chrome asli melawan API lokal (SQLite sementara, data sintetis): 17 tes browser lulus (7 lama + 10 baru). Checklist C1–C10: tooltip, klik = cross-filter, reset, setiap kartu punya judul/keterangan/catatan sampel, filter ID dipatuhi lintas halaman, tanggal terbalik, filter kosong, aksesibilitas dasar (nama tombol, alt gambar, label filter, fokus keyboard), ponsel 390 px tanpa overflow, halaman prediksi. **Belum dicakup:** kontras warna terukur, uji pembaca layar, navigasi keyboard pada elemen Plotly.

### P2-06 — Keamanan dan deployment
Selesai dan teruji (21 tes): autentikasi `Bearer` dengan hash SHA-256 (token asli tidak disimpan server), peran **viewer** (baca) dan **admin** (+ ekspor CSV, `/api/quality`), rate limit umum dan untuk percobaan gagal, header keamanan + `Cache-Control: no-store`, CORS eksplisit, dokumentasi API mati di staging/production, hanya GET, dan **pagar konfigurasi**: aplikasi menolak start di staging/production bila auth mati, hash token tidak valid/sama, password default, CORS wildcard/localhost, atau import aktif. Frontend meminta token (sessionStorage saja).

**Belum terbukti:** `docker compose up` produksi, HTTPS Caddy, backup/restore nyata, `read_only` container backend. Hanya `docker compose config` (sintaks + variabel wajib kosong ditolak) dan `bash -n` skrip yang diperiksa. Lihat `docs/P2_DEPLOYMENT_RUNBOOK.md` untuk uji staging.

### P2-07 dan P2-08
Lihat `docs/BRANDING.md` (nama yang sengaja tidak diubah: project Docker `tension-dashboard`, DB `toba_health`, volume). `scripts/audit_repo.py` memeriksa berkas terlarang (`.env`, `.venv`, `node_modules`, `dist`, cache, DB lokal, kunci/kredensial, data aktual/privat, backup), pola secret, berkas wajib (lockfile, manifest dependency, Dockerfile), dan pola `.gitignore`. Hasil pada arsip ini: **BERSIH**. Menghapus file dari commit terbaru tidak cukup bila secret pernah masuk Git; rotasi secret dan bersihkan riwayat.

## 6. Bukti pengujian (lingkungan kerja saya, 11 Nov 2026)

| Pemeriksaan | Hasil |
|---|---|
| Backend `pytest backend/tests` | **163 passed, 1 skipped** (sebelum P2: 80 passed + 1 skipped + 1 gagal karena tanpa `.git`) |
| Frontend `npm test` | **15 passed** (sebelumnya 10) |
| `npm run build` | berhasil |
| Browser (Chrome + API lokal sintetis) | **17 passed** |
| `python scripts/audit_repo.py` | BERSIH |
| Run ulang `etl.run_model_comparison` | `run_id` dan skor identik (diuji) |

Lingkungan: Python 3.13, scikit-learn 1.9.1, pandas 3.0.6, Node 22. Tes memakai SQLite dalam memori; **belum dijalankan ulang pada PostgreSQL Docker Anda**. Jalankan ulang di mesin tim sebelum merge.

## 7. Cara menjalankan ulang (PowerShell, dari root project)

```powershell
$env:PYTHONPATH = (Resolve-Path backend).Path
python -m pytest backend\tests -q -p no:cacheprovider
python -m etl.run_model_comparison          # menulis models\experiments dan reports\p2_model_comparison
Set-Location frontend; npm ci --no-audit --no-fund; npm test; npm run build
```
Untuk melihat halaman baru di `http://localhost:8080`, bangun ulang image (`scripts\start_main.ps1`) agar backend/frontend memuat kode P2; folder `models` sudah di-mount sehingga `models\experiments` terbaca. Jangan jalankan `docker compose down -v`.

## 8. Keputusan yang masih menunggu (tidak diasumsikan)

- Dosen: setujui/tolak target `future_7d_mean_sbp` dan horizon 7 hari; protokol jumlah pembacaan per sesi; arti jawaban tidur; reviewer/aturan anomali (P1-08).
- Tim/dosen: nama resmi repository/folder (P2-07).
- Tim: siapa menyiapkan staging, domain, dan kebijakan retensi backup (P2-06).
- Setelah ekspor Google Forms aktual tersedia: dry-run kontrak (P0-01) sebelum satu pun data aktual diimpor.

## 9. Gerbang P2 (dari dokumen serah terima)

- [x] P2-01 tiga algoritma dibandingkan, split bebas kebocoran
- [x] P2-02 endpoint memakai artefak terpilih, tes input/error
- [x] P2-03 metrik/grafik dari hasil eksperimen yang dapat direproduksi
- [x] P2-04 KPI: definisi, rumus, satuan, periode, pembanding, tes filter
- [x] P2-05 interaksi lulus checklist otomatis desktop + ponsel (audit manual belum)
- [ ] P2-06 staging aman diuji (kode selesai; uji Docker/HTTPS/backup belum)
- [ ] P2-07 nama proyek final dikonfirmasi (menunggu keputusan)
- [x] P2-08 arsip bersih (audit Git sebenarnya oleh tim)
- [x] Semua hasil eksperimen berlabel sintetis/simulasi
- [x] Keputusan dosen yang pending didokumentasikan, tidak diasumsikan
