# Changelog — Sesi Verifikasi dan Sinkronisasi P0/P1 (10 November 2026)

**DATA SINTETIS / SIMULASI.** Dokumen ini mencatat perubahan yang benar-benar dibuat pada sesi ini (10 November 2026), berbeda dari implementasi P0/P1 yang sudah ada sebelumnya dari sesi kerja terdahulu (lihat [`P0_P1_FINAL_AUDIT.md`](P0_P1_FINAL_AUDIT.md), 9 November 2026).

## Ringkasan

Repository yang diunggah sudah memuat implementasi teknis untuk hampir seluruh P0/P1. Sesi ini **tidak menulis ulang logika P0/P1 yang sudah benar**. Pekerjaan nyata sesi ini adalah: (1) verifikasi independen dengan menjalankan ulang seluruh bukti, (2) perbaikan satu insiden yang disebabkan sesi ini sendiri, (3) sinkronisasi dokumentasi historis, (4) penyusunan laporan status/changelog/verifikasi final sesuai permintaan.

## 1. Insiden dan perbaikan — artefak ML sempat tertimpa, lalu dipulihkan

**Apa yang terjadi:** Untuk memverifikasi reproducibility baseline, skrip `python -m etl.verify_baseline` dijalankan. Skrip ini **secara default menulis ke folder `models/` yang asli** (parameter `--output-dir` default-nya adalah folder produksi, bukan folder sementara), dan juga menulis ulang `docs/CP3_BASELINE_REPORT.md`. Karena environment Python sesi ini memasang versi library (numpy/pandas/scikit-learn/Python) yang sedikit berbeda dari environment saat artefak original dibuat, menjalankan skrip ini menghasilkan `run_id` baru (`64ad96f0cdbf7bccfcb3`) yang menimpa `run_id` asli (`5d3bed0d6591cd2bc09d`) pada tiga file: `models/baseline_metrics.json`, `models/baseline_manifest.json`, `models/linear_regression_synthetic.joblib`, serta seluruh isi `reports/cp3_baseline/` dan satu baris pada `docs/CP3_BASELINE_REPORT.md`.

**Bagaimana terdeteksi:** Dua pemanggilan berturutan terhadap fungsi yang seharusnya deterministik (`load_experiment`) mengembalikan `run_id` berbeda — ini langsung dicurigai sebagai anomali dan diselidiki sebelum dilaporkan ke pengguna.

**Perbaikan:** Semua file yang tertimpa dipulihkan **byte-demi-byte** dari arsip ZIP asli yang diunggah pengguna (`/mnt/user-data/uploads/Tension-dashboard-main.zip`), yang tidak pernah diubah. Pemulihan dikonfirmasi dengan:
- `run_id` pada `models/baseline_manifest.json` kembali `5d3bed0d6591cd2bc09d`.
- SHA-256 `models/linear_regression_synthetic.joblib` sesi ini **identik** dengan SHA-256 file pada arsip asli.
- `diff -rq` menyeluruh antara seluruh repository hasil kerja dan arsip asli (di luar `.venv`, `node_modules`, `.git`, cache, dan folder bukti baru) menunjukkan **nol perbedaan**.

**Pencegahan untuk verifikasi selanjutnya:** Reproduksi metrik baseline pada sesi ini selanjutnya **selalu diarahkan ke folder sementara** (`/tmp/...`, bukan `models/`) agar tidak menyentuh artefak produksi. Metrik berhasil direproduksi persis di folder terpisah tanpa menimpa apa pun (lihat bagian 3).

File yang terdampak insiden ini (dipulihkan ke kondisi asli, **tidak ada perubahan bersih** pada file-file berikut):
- `models/baseline_metrics.json`, `models/baseline_manifest.json`, `models/linear_regression_synthetic.joblib`
- `docs/CP3_BASELINE_REPORT.md`
- `reports/cp3_baseline/*.csv`, `reports/cp3_baseline/experiment.json`, `reports/cp3_baseline/figures/*.png`

## 2. Dokumentasi — sinkronisasi penanda historis (CP3-K01)

Dokumen CP3 lama ditandai jelas sebagai historis, mengarahkan pembaca ke sumber terbaru, **tanpa menimpa isi aslinya**:

| File | Perubahan |
|---|---|
| `docs/CP3_FINAL_REPORT.md` | Ditambah catatan di bagian atas: run ID lama (`242a4f84499a00fc1028`) digantikan oleh `5d3bed0d6591cd2bc09d` (skor metrik tidak berubah, hanya provenance), menunjuk ke `P0_P1_FINAL_AUDIT.md` dan laporan verifikasi baru. |
| `docs/CP3_PROGRESS_REPORT.md` | Ditambah catatan: definisi sesi valid terbaru (gate pasangan bersama) ada di audit P0/P1, bukan dokumen ini. |
| `docs/CP3_CHECKLIST.md` | Ditambah catatan: sebagian bukti menunjuk hasil lama; bukti regresi terbaru (73 passed/1 skipped pada SQLite **dan** PostgreSQL asli, 10 frontend passed, build sukses) ada di laporan verifikasi baru. |
| `docs/CP3_DEMO_SCRIPT.md` | Ditambah catatan: gladi bersih Docker penuh tidak dapat dijalankan ulang pada sesi ini (keterbatasan lingkungan kerja); dijelaskan apa yang dijalankan sebagai gantinya dan bahwa ini bukan pengganti penuh. |

Dokumen baru pada sesi ini:
- `docs/P0_P1_FINAL_STATUS.md` — tabel status 15 item P0/P1 (lihat dokumen tersebut untuk rincian lengkap per item).
- `docs/P0_P1_CHANGELOG.md` — dokumen ini.
- `reports/p0_p1_final_verification.md` — log pengujian lengkap sesi ini.
- `reports/p0_p1_reverify/` — bukti mentah (JUnit XML, JSON) dari pengujian yang dijalankan ulang sesi ini.

## 3. Verifikasi yang benar-benar dijalankan sesi ini (bukan diklaim dari laporan lama)

Ringkasan singkat; log lengkap termasuk perintah persis ada di `reports/p0_p1_final_verification.md`.

- Backend test suite pada **SQLite in-memory**: dijalankan 2×, hasil konsisten **73 passed, 1 skipped**.
- Backend test suite pada **PostgreSQL 16 asli** (di-install baru di lingkungan kerja, database sekali-pakai `toba_cp2_test` sesuai guard di `conftest.py`, bukan database aktif): **73 passed, 1 skipped**.
- Satu kegagalan transien pada percobaan pertama (`test_private_paths_cannot_be_accidentally_added_to_git`) disebabkan arsip ZIP tidak menyertakan folder `.git` (karena ZIP adalah ekspor file, bukan clone Git) — bukan bug aplikasi. Dikonfirmasi dengan menginisialisasi Git lokal dan memeriksa `git check-ignore` secara langsung untuk kelima pola jalur privat: semua benar diabaikan.
- ETL dry-run sintetis: profil 19/19 diterima, harian 570/570 diterima, sesi 1.140/1.140 valid, 0 dikarantina.
- ETL commit sungguhan ke database sekali-pakai terpisah (`toba_browser_demo`, bukan warehouse aktif) untuk keperluan smoke test API — berhasil.
- Frontend component test (`npm test`): **10/10 passed**.
- Frontend production build (`npm run build`): berhasil, 1.592 modules, bundle `index-aka-j8hL.js` — hash bundle identik dengan yang dicatat audit sebelumnya, mengonfirmasi kode yang diaudit dan kode yang diverifikasi sesi ini adalah kode yang sama.
- Smoke test manual seluruh endpoint API (`/health`, `/api/meta`, `/api/analytics`, `/api/quality`, `/api/model/baseline`, `/api/model/predict-baseline`, `/api/data/export/{sessions,daily,participants}`) terhadap backend `uvicorn` yang dijalankan langsung (tanpa Docker, karena Docker daemon tidak tersedia) — semua merespons benar.
- Reproduksi metrik baseline di folder sementara terpisah (tidak menimpa `models/`): MAE/RMSE/R² identik dengan yang tercatat di `models/baseline_metrics.json` dan `CP3_BASELINE_REPORT.md`.
- Verifikasi integritas checkout Git LF/CRLF (`etl.verify_audit_checkout`): kedua mode checkout menghasilkan `run_id` dan hash biner yang identik dengan artefak asli, setelah pemulihan dari insiden di bagian 1.
- **Tidak dijalankan**: Playwright/browser E2E penuh (unduhan Chromium diblokir jaringan sandbox) dan gladi bersih Docker Compose penuh (Docker daemon tidak tersedia di sandbox). Keduanya dicatat sebagai keterbatasan lingkungan kerja, bukan hasil lulus yang dipalsukan.

## 4. Tidak ada perubahan pada

- Logika bisnis/kode P0/P1 yang sudah diimplementasikan dan diverifikasi benar pada sesi sebelumnya (tidak diubah, sesuai instruksi "jangan mengulang perubahan yang sudah benar").
- `.env` atau kredensial apa pun.
- Database/warehouse aktif (tidak ada yang disentuh; semua pengujian memakai database sekali-pakai lokal yang dibuat dan dihapus dalam sesi ini).
- Keputusan akademik: target `future_7d_mean_sbp`, protokol jumlah pembacaan BP, semantik tidur aktual, dan aturan penanganan anomali **tetap berstatus pending/usulan**, tidak diubah menjadi disetujui.
