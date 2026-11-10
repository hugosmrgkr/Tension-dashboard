# Audit dan perbaikan final P0/P1 — Toba Health Insight

> **Catatan setelah audit:** laporan ini merekam audit sebelum sinkronisasi database utama. Pada 10 November 2026 pengguna mengotorisasi penerapan teruji ke stack 8080; bukti baru berada di [CP3_MAIN_CONSOLIDATION_REPORT.md](CP3_MAIN_CONSOLIDATION_REPORT.md). Klaim warehouse aktif tidak berubah pada audit ini berlaku pada sesi audit tersebut, bukan pada sesi konsolidasi sesudahnya.

Tanggal penyelesaian: 9 November 2026 (Asia/Bangkok). Cakupan: source CP2–CP3 setelah HEAD awal `ad22898`, beserta perubahan working tree audit ini. **DATA SINTETIS / SIMULASI**, bukan penelitian aktual, diagnosis, atau validasi klinis.

## Kesimpulan dan batas cakupan

Masalah teknis yang direproduksi telah diperbaiki dan pemeriksaan akhir lulus: backend Windows 73 passed / 1 skipped, backend Linux dengan PostgreSQL 73 passed / 1 skipped, frontend 10 passed, browser 7 passed, dan production build berhasil. Tidak ada failure/error pada eksekusi akhir tersebut. Satu skip adalah modul uji legacy, bukan skip regression test P0/P1.

Ini kesiapan teknis CP3 dengan data sintetis. Persetujuan target, protokol pembacaan BP, semantik tidur aktual, dan keputusan penanganan anomali penelitian belum diperoleh. Status akademik tersebut tidak dinyatakan selesai hanya karena kode sudah memiliki pagar teknis.

Dokumen yang diperiksa: `Deskripsi_Proyek_DA_DS.pdf` (10 halaman; jadwal CP3 halaman 6), `Daftar yang harus diperbaiki.pdf` (bagian 4.1–4.2 dan usulan data/KPI), panduan utama, serta dokumentasi CP2–CP3 di repository. Daftar perbaikan memuat rekomendasi/usulan; misalnya definisi KPI dan target bukan bukti persetujuan dosen. Instruksi kerja pengguna membatasi implementasi pada P0/P1 dan melarang ETL ke warehouse aktif. Minimum tiga algoritma, tuning, dan deployment publik tetap luaran tahap berikutnya menurut jadwal resmi; tidak dikerjakan dalam audit ini.

## Matriks lengkap

SELESAI berarti perbaikan teknis pada jalur aplikasi aktif telah dibuktikan, bukan seluruh penelitian selesai. BUTUH KEPUTUSAN berarti pagar teknis tersedia tetapi keputusan ilmiah belum final.

| ID / komponen | Status | Implementasi dan bukti file/baris | Kekurangan / keputusan tersisa |
| --- | --- | --- | --- |
| P0-01 — Dua formulir dan relasi ID | SEBAGIAN | [pipeline.py:30](../backend/app/pipeline.py#L30), [pipeline.py:73](../backend/app/pipeline.py#L73), [pipeline.py:99](../backend/app/pipeline.py#L99). Kontrak 24 kolom profil dan 28 kolom harian; FK dan grain diuji pada PostgreSQL; header BOM/spasi/kapital/CRLF diuji. | Dua CSV sintetis terbukti terintegrasi. Ekspor Google Forms aktual terbaru belum tersedia untuk membuktikan kontrak akhirnya. Kolom hilang, pertanyaan berubah atau urutan berubah ditolak, bukan ditebak. |
| P0-02 — Grain ID–tanggal–sesi dan dua pembacaan | BUTUH KEPUTUSAN | [pipeline.py:139](../backend/app/pipeline.py#L139), [bp_policy.py:11](../backend/app/bp_policy.py#L11), [analytics_v2.py:114](../backend/app/analytics_v2.py#L114), [baseline.py:35](../backend/app/baseline.py#L35). Keempat komponen mentah dipisah; ETL/API/model memakai gate pasangan yang sama. Regression test pasangan silang, parsial, ekstrem dan SBP≤DBP lulus. | Minimum satu atau dua pasangan, pengulangan, dan cakupan hari penelitian perlu persetujuan. Gate sementara konservatif bukan aturan klinis final. |
| P0-03 — Profil versus perilaku harian | SELESAI | [survey_schema.py:28](../backend/app/survey_schema.py#L28), [pipeline.py:135](../backend/app/pipeline.py#L135), [ERD](ERD.md). Profil di dimensi, perilaku pada fakta harian, BP pada fakta sesi. Tes daily-grain mencegah penggandaan perilaku akibat dua sesi. | Tidak ada perubahan grain ilmiah diam-diam. |
| P0-04 — Tidur dalam jam | BUTUH KEPUTUSAN | [survey_schema.py:97](../backend/app/survey_schema.py#L97), [data dictionary](DATA_DICTIONARY.md). Simulasi `06:30` = 6,5 jam; pecahan hari ambigu tidak otomatis dikali 24. Uji parsing/missing lulus. | Jawaban aktual dapat berarti durasi, waktu tidur, atau pecahan serial spreadsheet. Aktual ditahan NA dengan issue sampai semantik disepakati; raw dipertahankan. |
| P0-05 — ID kosong/tidak dikenal | SELESAI | [pipeline.py:73](../backend/app/pipeline.py#L73), [pipeline.py:99](../backend/app/pipeline.py#L99). ID wajib; harian tanpa profil diterima dikarantina; tidak membuat respondent ID otomatis. | Surrogate PK database bukan ID responden baru. Koreksi ID harus ditelusuri ke sumber. |
| P0-06 — Wilayah dan variabel konsumsi | SELESAI | [survey_schema.py:28](../backend/app/survey_schema.py#L28), [survey_schema.py:58](../backend/app/survey_schema.py#L58), [analytics_v2.py:137](../backend/app/analytics_v2.py#L137). Provinsi/kabupaten-kota; asin, buah, sayur dan kafein terpisah; tidak mengarang kecamatan/pola makan. | Teks wilayah mengikuti sumber; registry/ejaan wilayah aktual belum diverifikasi. |
| P0-07 — Target regresi | BUTUH KEPUTUSAN | [baseline.py:43](../backend/app/baseline.py#L43), [baseline.py:140](../backend/app/baseline.py#L140), [main.py:94](../backend/app/main.py#L94), [baseline report](CP3_BASELINE_REPORT.md). `future_7d_mean_sbp`, `target_approved=false`, hasil numerik mmHg, metrik artefak nyata. | Dosen harus menyetujui target dan kelayakan horizon 7 hari. Tidak mengklaim hasil penelitian/diagnosis. |
| P1-01 — Stres 1–5 | SELESAI | [survey_schema.py:69](../backend/app/survey_schema.py#L69), [survey_schema.py:97](../backend/app/survey_schema.py#L97). Integer/label eksplisit 1–5; nilai invalid menjadi NA + issue, bukan kategori 0–10. | Pengelompokan tinggi/rendah ilmiah tidak dibuat otomatis. |
| P1-02 — Kategori merokok | SELESAI | [survey_schema.py:65](../backend/app/survey_schema.py#L65), [models.py](../backend/app/models.py). Kategori panjang lengkap diterima; jumlah kosong tidak otomatis nol; konflik status/jumlah diaudit. | Frekuensi mengikuti satuan formulir, tidak diasumsikan jumlah batang. |
| P1-03 — Agregasi perilaku | SELESAI | [analytics_v2.py:124](../backend/app/analytics_v2.py#L124), [analytics_v2.py:137](../backend/app/analytics_v2.py#L137), [baseline.py:43](../backend/app/baseline.py#L43). BP sesi dirata-ratakan ke ID–tanggal sebelum join perilaku; statistik harian dan histori menggunakan mean/count sesuai grain, bukan `first`. | Jalur legacy tidak digunakan aplikasi aktif; lihat catatan di bawah. |
| P1-04 — ETL dua sumber dan keamanan perubahan | SELESAI | [import_data.py:24](../etl/import_data.py#L24), [etl_control.py:7](../backend/app/etl_control.py#L7), [main.py:69](../backend/app/main.py#L69). Dry-run default; accepted/rejected/reason; hash prasyarat, transaksi dan persetujuan eksplisit pergantian sumber. Web API hanya baca, tanpa upload/CRUD. | Koreksi dilakukan melalui sumber bersih berversi dan decision log; tidak ada persetujuan otomatis memuat ulang warehouse aktif. |
| P1-05 — BMI | SELESAI | [pipeline.py:88](../backend/app/pipeline.py#L88), [survey_schema.py:41](../backend/app/survey_schema.py#L41). Tinggi/berat asal disimpan; BMI = kg/(cm/100)², 3 desimal; input invalid tetap NA. | Tidak menambahkan klasifikasi BMI klinis. |
| P1-06 — Grafik faktor risiko | SELESAI | [analytics_v2.py:137](../backend/app/analytics_v2.py#L137), [Pages.jsx](../frontend/src/pages/Pages.jsx), [test_cp3_stage2.py](../backend/tests/test_cp3_stage2.py). Grafik memakai kategori sumber, stres 1–5, tidur, aktivitas, konsumsi, merokok dan obat; ukuran sampel/NA dan asosiasi dijelaskan. | Data simulasi bukan bukti sebab-akibat; kelompok kecil tetap perlu kehati-hatian. |
| P1-07 — Konsistensi BP dan non-diagnosis | SELESAI | [bp_policy.py:9](../backend/app/bp_policy.py#L9), [baseline.py:140](../backend/app/baseline.py#L140), [App.jsx](../frontend/src/App.jsx), [Pages.jsx](../frontend/src/pages/Pages.jsx). Jalur aktif tidak menghitung kelas hipertensi/akurasi demo; memakai angka mmHg dan peringatan eksperimen. | Jika klasifikasi analitik ditambahkan kelak, dosen harus menyetujui satu rule set terpusat. Gate validitas bukan klasifikasi hipertensi. |
| P1-08 — Missing, duplikasi, tanggal, outlier dan quality gate | BUTUH KEPUTUSAN | [pipeline.py:73](../backend/app/pipeline.py#L73), [pipeline.py:99](../backend/app/pipeline.py#L99), [quality.py:62](../backend/app/quality.py#L62), [etl_control.py:7](../backend/app/etl_control.py#L7). Konflik semua versi dikarantina; tanggal mencurigakan ditahan; raw tetap ada; actual commit dengan issue/karantina/IQR belum selesai ditolak. | IQR simulasi tetap flag deskriptif, bukan penghapusan otomatis. Keputusan retain/koreksi/eksklusi aktual, batas penelitian dan log review wajib ditetapkan. |

Modul lama seperti `service.py`, `data_utils.py`, dan halaman React versi lama masih ada sebagai legacy; entrypoint `app.main:app` serta `frontend/src/App.jsx` memakai jalur v2. Klaim selesai di atas berlaku pada runtime aktif yang diuji, bukan pernyataan bahwa semua kode legacy sudah dimodernisasi. Tidak perlu menghidupkan ulang endpoint legacy untuk demo.

## Temuan terbukti dan perbaikannya

Eksekusi reproduksi awal mencatat delapan failure pada [reproduction-before.xml](../reports/p0_p1_audit/reproduction-before.xml). Perbaikan disertai 14 regression test tambahan di [test_p0_p1_audit.py](../backend/tests/test_p0_p1_audit.py), ditambah penyesuaian tes kompatibilitas baseline/CP2 dan satu tes frontend untuk KPI tanpa BP valid.

| Temuan | Akar masalah / perbaikan | Bukti regresi |
| --- | --- | --- |
| Artefak menjadi unavailable setelah perubahan line ending | Hash JSON berdasarkan physical bytes sehingga checkout LF berbeda dari CRLF. Manifest v3 + hash UTF-8/LF dan `.gitattributes`; hash biner tetap ketat. | `test_artifacts_survive_lf_and_crlf_checkout`, `test_model_bytes_and_metric_values_still_have_strict_integrity`; checkout Windows/Linux. |
| SBP pembacaan 1 dan DBP pembacaan 2 dianggap sesi valid | Mean masing-masing komponen dihitung terpisah. Gate sekarang memeriksa pasangan bernomor sama di ETL, API dan baseline. | `test_cross_reading_components_are_pending_review`, `test_api_rechecks_legacy_cross_readings_and_exposes_review`. |
| SBP≤DBP / ekstrem dapat berkontribusi pada agregat | Flag lama belum mengecualikan derived BP. Gate sementara menahan mean dan model, menyimpan raw untuk review. | `test_contradictory_bp_is_retained_but_not_aggregated`, `test_extreme_and_suspicious_inputs_are_not_silently_used`. |
| Duplikat konflik memilih jawaban pertama | Dedup by key tanpa membedakan konflik. Kini semua versi konflik profil/ID–tanggal dikarantina; duplikat identik tetap satu dan diaudit. | Tes konflik harian diuji kedua urutan; tes konflik profil membuktikan 30 harian terkait tidak dimuat. |
| Responden aktif hilang ketika BP kosong | KPI bergantung valid-session IDs. Kini active = accepted-daily IDs; `respondents_with_valid_bp` terpisah; mean null dan grafik kosong. | `test_active_respondents_are_daily_ids_even_without_bp`, tes frontend `daily-active respondents...`. |
| Header BOM diikuti spasi tidak dikenali | Normalisasi meninggalkan spasi sesudah penghapusan BOM. Ditambah strip setelah BOM; urutan kolom tetap divalidasi ketat. | `test_header_contract_accepts_whitespace_but_never_guesses_order`. |
| Folder data aktual/privat dan env bertingkat belum cukup terlindungi Git | Tambah ignore `data/actual`, `data/private`, `data/raw`, nested `.env*`, nama kredensial dan key. Laporan actual dibatasi ke `data/private/`. | `test_private_paths_cannot_be_accidentally_added_to_git`; pemeriksaan tracked files. Ignore tidak menghapus rahasia yang sudah terlanjur ada di histori. |
| Quality gate aktual belum menahan semua review | Commit actual kini menolak rejected rows, issues dan IQR yang belum diselesaikan; tidak ada override diam-diam. | `test_actual_quality_gate_blocks_unreviewed_issues`; tes hash/source-change/rollback yang sudah ada. |

Dua temuan tambahan **urgent di luar daftar utama** juga diperbaiki:

1. **CSV formula injection**: teks profil yang dimulai karakter formula dapat dieksekusi spreadsheet saat ekspor. [main.py:113](../backend/app/main.py#L113) mengawali teks berisiko dengan apostrof, tanpa mengubah nilai database atau sel numerik. `test_csv_formula_text_is_escaped` lulus.
2. **Kebocoran nama file sumber aktual lewat `/api/meta`**: nama sumber yang sensitif masih muncul meski akses data aktual dibatasi. [analytics_v2.py:44](../backend/app/analytics_v2.py#L44) mengembalikan label generik. Tes `test_public_metadata_does_not_disclose_actual_source_name` lulus. Endpoint analitik/ekspor/quality aktual tetap diblokir.

## Definisi konsisten dan keputusan review

- Responden aktif: jumlah ID unik dengan setidaknya satu catatan harian **diterima ETL** pada filter. Ini berbeda dari jumlah responden dengan BP valid. Catatan harian diterima tidak berarti semua pertanyaan terisi; missing non-kunci tetap NA dengan audit.
- Sesi valid sementara: sedikitnya satu pasangan SBP/DBP lengkap pada nomor sama, tanpa komponen parsial, pembacaan invalid atau pasangan tidak konsisten. Satu pasangan lengkap dengan pasangan kedua seluruhnya kosong dapat digunakan sementara. Jika komponen yang lain ambigu, seluruh derived sesi ditahan. Protokol final menunggu dosen.
- Status serving `ready / incomplete / pending_review`, alasan review dan jumlah pasangan tersedia pada tabel/ekspor sesi. Serving memeriksa ulang raw legacy, tidak mempercayai mean lama begitu saja. Mean tersimpan NA akibat review tidak direkonstruksi diam-diam.
- Batas 60–260/35–170 dan pagar tanggal 2024–2030 merupakan pagar teknis yang sudah ada, bukan pedoman klinis/kriteria inklusi baru. Tanggal setelah timestamp pengiriman ditahan, bukan diubah. Nilai sumber asli tetap pada file raw; sel canonical yang gagal parsing dapat menjadi NA dengan issue.
- Duplikat konflik tidak diselesaikan dengan first/last/timestamp. Pertahankan raw, buat versi sumber koreksi terpisah dengan alasan dan reviewer, dry-run, baru minta otorisasi promosi. Tidak ada koreksi warehouse aktif dalam audit ini.
- IQR sintetis hanya flag eksplorasi, bukan diagnosis. Aktual memerlukan keputusan ilmiah dan audit review sebelum lolos gate. Header aktual memerlukan contoh ekspor dan mapping berversi bila berbeda; kontrak saat ini tidak mengklaim mendukung semua variasi Google Forms.

## Verifikasi ML Windows/Linux

[baseline.py:30](../backend/app/baseline.py#L30) menormalisasi **hanya physical CRLF menjadi LF** sebelum SHA256 teks UTF-8. Nilai JSON, spasi lain dan isi tetap dilindungi; JSON tidak diabaikan atau ditulis ulang saat validasi. [baseline.py:169](../backend/app/baseline.py#L169) menolak mode hash tidak dikenal, mismatch metrics, mismatch binary dan kontrak target/run. Manifest lama tanpa mode tetap menggunakan pemeriksaan raw-bytes, bukan bypass.

[.gitattributes](../.gitattributes) mengunci LF bagi JSON/source/fixture CSV dan menandai `.joblib` sebagai biner. Generator artefak menulis JSON UTF-8/LF secara eksplisit dan menyertakan fingerprint pipeline serta BP policy pada provenance. Target dan fitur tidak diganti.

| Lingkungan | Pengujian sebenarnya | Hasil |
| --- | --- | --- |
| Windows native | Git `checkout-index` pada repository/index sementara, `core.autocrlf=false` dan `true`; startup FastAPI TestClient, evaluasi dan prediksi | Kedua checkout available; prediction HTTP 200; binary SHA256 identik; [checkout-windows-final.json](../reports/p0_p1_audit/checkout-windows-final.json). |
| Linux Python 3.12 container | Prosedur Git yang sama pada OS Linux | Kedua checkout available; prediction HTTP 200; binary SHA256 identik; [checkout-linux-final.json](../reports/p0_p1_audit/checkout-linux-final.json). |
| Mutasi line ending dan isi | Regression test LF/CRLF sengaja diubah, metrik diubah nilainya, dan joblib ditambah bytes | LF/CRLF diterima; perubahan nilai/biner ditolak. Lulus pada kedua full backend suite. |

Simulasi checkout memakai **kandidat working tree terbaru**, bukan clone HEAD lama yang belum memuat perbaikan. Tidak ada commit, push, atau perubahan index Git project utama. Kedua checkout Git menghasilkan LF sesuai atribut; tes mutasi CRLF terpisah membuktikan normalizer tetap bekerja jika file diubah editor Windows.

Artefak run `5d3bed0d6591cd2bc09d`, 60 train windows / 12 ID train; 7 test origins / 7 ID test; cutoff 2026-09-18. Hold-out ID, purge label menurut waktu, non-overlapping target uji, dan preprocessing train-only diuji. Overlap dalam train tetap keterbatasan korelasi observasi, bukan sampel independen tambahan.

| Eksperimen sintetis | MAE (mmHg) | RMSE (mmHg) | R² |
| --- | --- | --- | --- |
| Naive mean 7 hari | 1.933673 | 2.234723 | 0.850309 |
| Linear Regression | 2.575492 | 3.113985 | 0.709343 |

Angka berasal dari [baseline_metrics.json](../models/baseline_metrics.json), bukan input manual. Regenerasi artefak tidak mengubah skor fixture bersih. Endpoint demo menyajikan baseline **naive**, sedangkan Linear Regression adalah pembanding eksperimen; tidak diklaim endpoint melayani model terbaik final. Notebook [03_verifikasi_baseline_cp3.ipynb](../notebooks/03_verifikasi_baseline_cp3.ipynb) sudah dieksekusi pada audit: 6 code cells dan 3 keluaran PNG. Target `future_7d_mean_sbp` tetap usulan; hasil tujuh test origins tidak mendukung validitas klinis atau generalisasi penelitian aktual.

## Pengujian dan bukti akhir

| Pemeriksaan | Hasil yang benar-benar dijalankan | Bukti |
| --- | --- | --- |
| Backend Windows / SQLite in-memory | **73 passed, 1 skipped**, 81,29 detik; tanpa failure/error | [backend-windows-final.xml](../reports/p0_p1_audit/backend-windows-final.xml) |
| Backend Linux / PostgreSQL 16 RAM | **73 passed, 1 skipped**, 70,78 detik; tanpa failure/error | [backend-linux-postgresql-final.xml](../reports/p0_p1_audit/backend-linux-postgresql-final.xml) |
| Frontend component tests | **10 passed**, termasuk KPI accepted daily ketika BP valid nol | [frontend-final.xml](../reports/p0_p1_audit/frontend-final.xml) |
| Production build | **Lulus**, 1.592 modules; hasil bundle `index-aka-j8hL.js` | `npm run build` dijalankan sesudah perubahan UI terakhir; warning ukuran bundle tetap ada, bukan build error |
| Browser Edge/Playwright | **7 passed**, 36,1 detik; delapan halaman desktop/mobile, filter dan cross-filter, ekspor, prediksi/evaluasi, empty/error state | [browser-results.json](../reports/p0_p1_audit/browser-results.json), [screenshots](../reports/p0_p1_audit/screenshots) |
| ETL dry-run dua CSV | **Lulus**; profil 19/19, harian 570/570, derived/valid sesi 1.140/1.140; tidak menghubungi/mengubah DB pada dry-run | [dry-run-final/quality.json](../reports/p0_p1_audit/dry-run-final/quality.json) dan laporan completeness/issues |
| HTTP → PostgreSQL → UI audit | **Lulus**; metadata/KPI/filter/export, empty filter, seluruh naive predictions held-out sesuai artefak | [http-verification-final.json](../reports/p0_p1_audit/http-verification-final.json) |
| ML integrity dan checkout | **Lulus Windows dan Linux**, autocrlf true/false, tamper rejection | Dua checkout-final JSON di atas dan 14 regression tests |
| Perlindungan data | **Lulus**; fingerprint warehouse aktif sebelum/sesudah sama dan hash semua file data/notebook CP2 yang dilindungi sama | [verification-summary.json](../reports/p0_p1_audit/verification-summary.json), [active-before.json](../reports/p0_p1_audit/active-before.json), [active-after.json](../reports/p0_p1_audit/active-after.json) |

Kualitas fixture: missing tidur 6/570, duduk 3/570, jumlah merokok 550/570; IQR menandai 25 sesi. Missing tetap NA, bukan nol; IQR tidak dijadikan hasil klinis. Profil/daily tidak mempunyai baris ditolak pada fixture bersih. Bukti abnormal/missing/conflict berasal dari mutasi fixture di test, bukan perubahan CSV asli.

Kegagalan antara disimpan untuk transparansi: delapan reproduksi awal; `backend-first.xml` sebelum penyelesaian kompatibilitas; `backend-windows-sandbox-error.xml` berisi empat setup errors karena folder temporary Windows ditolak sandbox; `browser-docker-off.json` berisi tujuh kegagalan koneksi ketika Docker mati. Setelah izin fixture dan lingkungan diperbaiki, semua rerun akhir pada tabel lulus. Kegagalan infrastruktur tersebut tidak disamarkan sebagai tes lulus. Peninjauan otomatis sempat tertahan batas penggunaan pada sesi sebelumnya; verifikasi tertunda kini berhasil dijalankan.

Warning non-blocking tersisa: deprecation TestClient/httpx dan bundle Plotly sekitar 4,91 MB uncompressed. Ini bukan error runtime yang direproduksi pada tujuh browser tests, dan tidak dipaksakan menjadi redesign/upgrade dependency dalam audit P0/P1.

## Isolasi, data aktif dan file perubahan

Stack audit memakai [compose.p0-p1-audit.yaml](../compose.p0-p1-audit.yaml), project `toba-p0-p1-audit`, URL lokal `http://127.0.0.1:8082`, API `8002`, database RAM `toba_p0_p1_audit`. Dua CSV hanya dimuat ke database audit yang diperiksa kosong. Full integration test memakai PostgreSQL RAM lain `toba_cp2_test`; fixture menolak nama/host DB selain namespace tes. Container `toba-p0-p1-tests` dihentikan setelah seluruh tes lulus dan label auditnya diverifikasi; stack audit 8082 tetap berjalan untuk pemeriksaan. Tidak ada ETL commit ke warehouse aktif dan tidak ada reset/penghapusan volume aktif.

Docker Desktop perlu dinyalakan kembali pada sesi lanjutan; container aktif dengan restart policy kembali berjalan. Tidak dilakukan rebuild/promosi aplikasi aktif. Kode audit terbaru dibuktikan melalui test suite dan stack audit; image produksi aktif tetap perlu dibangun dari perubahan ini ketika tim memutuskan deploy. Artefak model bind-mounted tetap tersedia, tidak mengubah isi warehouse.

Fingerprint natural-content aktif sebelum dan sesudah identik: `2c72512aed5d6c4f1e124f1be7ec47a03d0635fe2a6579fe6c3a7edd9c14c267`. Pemeriksaan sesudah memakai transaksi PostgreSQL `READ ONLY`. Tidak ada modifikasi `.env`, CSV/XLSX sumber, notebook CP2, atau identitas aktual. Tidak ditemukan data actual/private atau kredensial yang tracked pada pemeriksaan Git audit ini; ini bukan pemindaian lengkap rahasia seluruh histori.

Kelompok file dibuat/diubah:

- Gate dan serving: `backend/app/bp_policy.py` (baru), `pipeline.py`, `survey_schema.py`, `quality.py`, `etl_control.py`, `analytics_v2.py`, `main.py`.
- Integritas/eksperimen: `backend/app/baseline.py`, `etl/verify_baseline.py`, `etl/verify_audit_checkout.py` (baru), `models/baseline_metrics.json`, `models/baseline_manifest.json`, `models/README.md`, notebook 03, `reports/cp3_baseline/experiment.json`. Model biner yang diregenerasi identik dan tidak memerlukan perubahan Git.
- Frontend: `frontend/src/pages/Pages.jsx`, `frontend/tests/dashboard.test.mjs`. Perbaikan label/quality/empty state, tanpa redesign.
- Tes dan isolasi: `backend/tests/test_p0_p1_audit.py` (baru), `test_cp2.py`, `test_cp3_baseline.py`, `backend/Dockerfile.audit` (baru), `compose.p0-p1-audit.yaml` (baru).
- Privasi/dokumentasi: `.gitignore`, `.gitattributes` (baru), `etl/import_data.py`, `backend/app/readiness.py`, `docs/DATA_DICTIONARY.md`, `docs/ERD.md`, `docs/CP3_BASELINE_REPORT.md`, `README.md`, laporan ini, serta bukti `reports/p0_p1_audit/`. Laporan CP2/CP3 lama dipertahankan sebagai historis; gunakan klarifikasi final ini untuk definisi terbaru.

## Menjalankan ulang pemeriksaan

Dari root project, dengan Python environment/dependency dev yang tersedia:

```powershell
.venv\Scripts\python.exe -m pytest backend/tests -q -p no:cacheprovider
.venv\Scripts\python.exe -m etl.import_data --synthetic --dry-run --summary
.venv\Scripts\python.exe -m etl.verify_audit_checkout --output reports/p0_p1_audit/checkout-windows-final.json
cd frontend
npm test
npm run build
$env:CP3_BROWSER_BASE_URL='http://127.0.0.1:8082'
$env:CP3_REPORT_DIR='../reports/p0_p1_audit'
npm run test:browser
```

Browser membutuhkan stack audit yang **sudah siap dan berisi fixture**, bukan warehouse aktif. Compose audit dapat dinyalakan dengan `docker compose -p toba-p0-p1-audit -f compose.p0-p1-audit.yaml up -d --build db backend frontend`; database memakai tmpfs sehingga setelah restart daemon data audit dapat kosong lagi. Jangan menjalankan commit ETL ke konfigurasi default project. Pengisian ulang audit harus menunjuk eksplisit database `toba_p0_p1_audit` yang kosong. Eksperimen offline dapat direproduksi dengan notebook 03 atau `python -m etl.verify_baseline`; itu menulis artefak model/laporan, bukan database.

## Keputusan dosen/tim sebelum data aktual

| Keputusan | Opsi dan konsekuensi | Rekomendasi sementara |
| --- | --- | --- |
| Target/horizon | Mean tujuh hari berikutnya memerlukan histori dan target lengkap; target lain mengubah framing dan evaluasi. | Pertahankan nama/flag usulan sekarang, minta persetujuan tertulis sebelum eksperimen aktual. |
| Minimum pasangan BP | Satu pasangan meningkatkan coverage; dua pasangan menurunkan coverage tetapi mendekati protokol pengukuran berulang. Aturan partial/repeat memengaruhi KPI, n dan model. | Gunakan pending_review untuk ambigu; setujui protokol dan uji sensitivitas, bukan memilih setelah melihat skor. |
| Arti tidur aktual | Durasi, jam tidur/bangun atau pecahan hari membutuhkan transformasi berbeda. | Periksa formulir/ekspor asli; simpan raw; jangan infer satuan otomatis. |
| Anomali, tanggal dan koreksi | Retain, koreksi dari sumber, atau eksklusi memengaruhi distribusi dan bias seleksi. Rentang tahun teknis bukan tanggal studi. | Tetapkan periode studi, reviewer, reason code dan input koreksi berversi; tidak menghapus raw. |
| Kecukupan dan izin data | 500 catatan primer berulang bukan 500 individu independen. Data kesehatan aktual membutuhkan izin dan pembatasan akses. | Konfirmasi unit sampel, inklusi usia, consent dan desain evaluasi; API publik actual tetap diblokir. |
| Header aktual dan promosi | Header/urutan dapat berubah ketika pertanyaan Forms diubah. | Verifikasi dua contoh ekspor, perbarui kontrak berversi secara eksplisit, dry-run dan review sebelum promosi. |

## Checklist melanjutkan CP4

- [x] Jalur CP3 sintetis, dua sumber → ETL → PostgreSQL → API → delapan halaman, diuji.
- [x] Gate BP, KPI, missing/duplicate/empty/filter konsisten pada jalur aktif.
- [x] Artefak tervalidasi ketat dan kompatibel checkout Windows/Linux; baseline reproducible.
- [x] Bukti tes, kualitas data, browser/screenshot, dan fingerprint aktif tersedia.
- [x] Tidak commit/push, tidak memuat ulang/reset warehouse aktif, tidak mengubah `.env`/sumber.
- [ ] Persetujuan dosen untuk target, tidur aktual, protokol BP, inklusi dan penanganan anomali.
- [ ] Data aktual legal, cukup, tervalidasi header dan quality review; tetap terpisah dari simulasi.
- [ ] Minimal tiga algoritma, tuning, evaluasi dan model card final pada data layak (CP4, belum dikerjakan).
- [ ] Deployment publik dengan kontrol akses data aktual dan input model baru (tahap berikutnya, belum diklaim selesai).

Secara teknis siap melanjutkan perencanaan CP4 pada basis CP3 sintetis yang diuji. Kesiapan penelitian aktual dan seluruh luaran akhir DALIS–DASI masih bergantung pada butir yang belum dicentang.
