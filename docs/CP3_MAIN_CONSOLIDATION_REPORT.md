# Laporan konsolidasi CP3 ke stack utama 8080

Tanggal: **10 November 2026**. Status: **selesai diterapkan dan diverifikasi pada DATA SINTETIS / SIMULASI**.

Pengguna secara eksplisit meminta satu aplikasi utama dengan satu database permanen dan mengotorisasi pelaksanaan saran backup, staging, pembaruan teruji, serta penghentian demo tambahan. Tidak ada perubahan target akademik, klaim diagnosis atau implementasi CP4.

## 1. Hasil akhir

| Komponen | Hasil |
| --- | --- |
| Project Docker utama | `tension-dashboard` |
| Dashboard | **http://127.0.0.1:8080** |
| API docs | http://127.0.0.1:8080/api/docs |
| Database aplikasi | PostgreSQL `toba_health`, service/volume utama yang sudah ada |
| Data | **19 profil / 570 catatan ID–tanggal / 1.140 sesi** |
| Profil dengan hari aktif mingguan kosong | **19 → 0** |
| Metadata ETL dan fingerprint | Tersedia dan sesuai hasil parser CP2 terbaru |
| Kecocokan warehouse–artefak | `warehouse_batch_match`: **null → true** |
| Run baseline | `5d3bed0d6591cd2bc09d`, sama seperti sebelum penerapan |
| Container yang tetap berjalan | Hanya frontend, backend dan db milik `tension-dashboard`; backend/db healthy |
| Demo 8081 / audit 8082 | Tidak berjalan; konfigurasi dipertahankan untuk histori/QA |

Tidak ada penggabungan dua volume, reset, penghapusan tabel/baris, atau penggantian database utama. PostgreSQL utama tetap menggunakan volume yang sama. Frontend/backend dibangun dan dijalankan ulang dengan kode workspace terbaru. Database staging berhenti setelah verifikasi selesai; database aplikasi tetap berjalan.

## 2. Kondisi sebelum dan akar masalah

8080 sebenarnya sudah berisi 19/570/1.140 data sintetis saat sesi ini dimulai. Screenshot lama yang menyebut kosong tidak menggambarkan kondisi live saat pemeriksaan. Enam file inti backend dalam container sudah cocok dengan workspace, tetapi data/metadata warehouse tertinggal dari bentuk keluaran ETL terbaru:

- Seluruh `active_days_week` pada 19 profil masih null, sementara nilai sumber tersedia.
- Metadata audit ETL/fingerprint belum tersimpan sehingga API tidak dapat membuktikan kecocokan batch dengan artefak model.
- Seluruh 1.140 waktu sesi menggunakan format `HH:MM`, sementara parser terbaru menyimpan `HH:MM:00`.

Perbandingan menyeluruh dengan keluaran dua CSV menunjukkan perbedaan hanya pada hal tersebut. Nilai tekanan darah, perilaku harian, profil lain, tanggal, sesi dan relasi sesuai sumber. Format waktu yang berubah tetap merepresentasikan jam/menit yang sama, bukan koreksi waktu pengukuran atau imputasi waktu hilang.

## 3. Backup, staging dan mekanisme pembaruan

1. Dibuat backup penuh PostgreSQL dengan `pg_dump -Fc` melalui binary stream. Ukuran backup **67.995 bytes**, header/archive-list valid.
2. Backup disimpan di folder privat yang diabaikan Git. Lokasi dan SHA256 tersedia di [operation.json](../reports/cp3_main_consolidation/operation.json). Jangan unggah isi backup ke repository atau lampiran publik.
3. Backup dipulihkan menggunakan `pg_restore --exit-on-error` hanya ke PostgreSQL RAM `toba-cp3-main-staging`, tidak ke database aktif.
4. Preview staging membandingkan seluruh isi warehouse dengan fixture. Pagar awal menolak perbedaan format waktu; setelah dibuktikan hanya `HH:MM` → waktu sama `HH:MM:00`, normalisasi ekuivalen tersebut ditambahkan secara terbatas dan diuji. Drift waktu yang benar-benar berbeda tetap ditolak.
5. Commit staging sukses; fingerprint, ID, jumlah baris dan relasi terverifikasi. Seluruh backend suite dijalankan pada SQLite Windows serta PostgreSQL khusus `toba_cp2_test` dalam staging.
6. Preview read-only utama memastikan hash utama masih sama dengan salinan yang sudah diuji. Commit utama memakai hash prasyarat, backup/SHA256 dan transaksi dengan lock.
7. Dilakukan pembaruan **UPDATE saja pada target**, mempertahankan seluruh surrogate ID dan FK. Tidak menggunakan ETL replace, DELETE, INSERT, drop atau reset pada database target.
8. Backend/frontend utama dibangun ulang, API/browser diverifikasi, lalu staging dan jalur demo/audit tambahan dihentikan tanpa menghapus volume.

Implementasi: [warehouse_sync.py](../backend/app/warehouse_sync.py), [sync_main_warehouse.py](../etl/sync_main_warehouse.py). Dry-run adalah default dan memakai transaksi PostgreSQL READ ONLY. Sumber aktual, database kosong, isi berbeda, hash stale, serta backup yang tidak cocok ditolak. Nilai mingguan non-null yang berbeda tidak ditimpa. Jika pemeriksaan setelah flush gagal, transaksi di-rollback; perilaku ini diuji.

Hash natural-content utama:

- Sebelum: `2c72512aed5d6c4f1e124f1be7ec47a03d0635fe2a6579fe6c3a7edd9c14c267`.
- Sesudah: `0a91e24fecb8482092b2687cf144e84cf64fccfadbb46c7653d061fbbb2deefc`.
- Fingerprint batch ETL: `51394dad1ec8fa22d6ff2ed5503319625e956b366fe8ed87b92e8e0824d32427`.

Hash natural-content berubah sesuai pembaruan profil/format waktu yang diotorisasi; ini bukan klaim bahwa database sama persis byte demi byte setelah pembaruan. Fingerprint batch ETL memakai definisi berbeda dari hash natural-content SQL, sehingga kedua nilai tidak diharapkan identik.

## 4. Pengujian yang benar-benar dijalankan

| Pemeriksaan | Hasil akhir | Bukti |
| --- | --- | --- |
| Backend Windows / SQLite | **81 passed, 1 skipped**, 94,12 detik | [backend-windows.xml](../reports/cp3_main_consolidation/backend-windows.xml) |
| Backend Linux / PostgreSQL 16 terisolasi | **81 passed, 1 skipped**, 81,28 detik | [backend-postgresql.xml](../reports/cp3_main_consolidation/backend-postgresql.xml) |
| Frontend component | **10 passed**, tanpa failure/error | [frontend.xml](../reports/cp3_main_consolidation/frontend.xml) |
| Frontend production build host | **Berhasil**, 1.592 modules, bundle `index-aka-j8hL.js`, 38,34 detik | Eksekusi `npm run build` pada sesi ini; ringkasan pada verification JSON |
| Docker build/start utama | **Berhasil**; DB utama tetap running, backend/frontend dibangun ulang; healthcheck/startup lulus | `scripts/start_main.ps1` benar-benar dijalankan |
| Browser Edge / Playwright melalui **8080** | **7 passed**, 42,2 detik; delapan halaman desktop/mobile, filter/cross-filter, CSV, prediksi/evaluasi, empty/error | [browser-results.json](../reports/cp3_main_consolidation/browser-results.json), [screenshots](../reports/cp3_main_consolidation/screenshots) |
| HTTP/API/SQL/CSV utama | **Lulus**; hitungan, NA, filter, ekspor, seluruh prediksi naive held-out dan empty filter sesuai | [http-verification.json](../reports/cp3_main_consolidation/http-verification.json) |
| Warehouse → fitur/Linear Regression | **323 window cocok**, 7 prediksi uji cocok, selisih maksimum **0.0** | [warehouse-ml-equivalence.json](../reports/cp3_main_consolidation/warehouse-ml-equivalence.json) |
| Preview dan commit staging | **Lulus**, backup dapat direstore dan pembaruan terverifikasi | [staging-preview.json](../reports/cp3_main_consolidation/staging-preview.json), [staging-commit.json](../reports/cp3_main_consolidation/staging-commit.json) |
| Preview dan commit utama | **Lulus**, ID/jumlah/relasi tetap; metadata dan profil lengkap | [main-preview.json](../reports/cp3_main_consolidation/main-preview.json), [main-commit.json](../reports/cp3_main_consolidation/main-commit.json) |
| Preview akhir / idempotensi | **Lulus**, 0 weekly updates, 0 normalisasi waktu, metadata sudah sesuai; tidak melakukan commit tambahan | [main-after-preview.json](../reports/cp3_main_consolidation/main-after-preview.json) |
| Proteksi ZIP | **Lulus pada Windows/Linux**; tes menjalankan script ZIP asli pada proyek palsu di temporary directory, tidak mengarsipkan proyek asli | [test_source_archive.py](../backend/tests/test_source_archive.py) dalam full suite |

Satu skip adalah tes kontrak API v1 lama, bukan tes sinkronisasi. Tujuh tes sinkronisasi baru mencakup preview tanpa perubahan, update/ID/idempotensi, penolakan drift harian, weekly yang berbeda, source aktual, hash stale, drift waktu, dan rollback setelah flush (kasus parameterized dihitung sesuai output pytest). Satu tes ZIP tambahan membawa jumlah backend dari 73 menjadi 81.

Kegagalan antara yang diperbaiki: fungsi audit awal menginspeksi Engine sehingga dapat mengganggu transaksi SQLite in-memory; kini memakai koneksi transaksi yang sama. Satu assertion PostgreSQL sempat menganggap urutan SELECT tanpa ORDER BY stabil; assertion diperbaiki membandingkan pemetaan ID, bukan posisi baris. Bukti kegagalan PostgreSQL awal disimpan sebagai `backend-postgresql-first.xml`, bukan diklaim lulus. Tidak ada kegagalan pada suite akhir di atas.

Warning non-blocking: deprecation Starlette/httpx dan bundle Plotly sekitar 4,91 MB uncompressed. Tidak ada redesign atau upgrade dependency besar dalam tugas ini.

## 5. Bukti tidak ada data yang hilang

[tables-before.json](../reports/cp3_main_consolidation/tables-before.json) dan [tables-after.json](../reports/cp3_main_consolidation/tables-after.json) mencatat hash/jumlah seluruh **11 tabel** pada transaksi read-only. Jumlah semua tabel tetap sama. Hanya tiga tabel yang hash-nya berubah sesuai rencana:

- `dim_participant_v2`: 19 nilai hari aktif mingguan diisi dari sumber.
- `fact_bp_session_v2`: 1.140 string waktu dinormalkan tanpa mengubah waktu atau angka BP.
- `dataset_state_v2`: metadata ETL dan nama sumber yang terverifikasi diperbarui.

Delapan tabel lainnya, termasuk seluruh tabel legacy serta fakta perilaku harian/dimensi tanggal/sesi, mempunyai hash yang sama. Pemetaan semua ID utama/FK pada warehouse dipertahankan oleh pemeriksaan sinkronisasi.

[verification.json](../reports/cp3_main_consolidation/verification.json) juga membuktikan `.env`/ketiadaannya, kedua CSV sumber, notebook CP2, serta ketiga artefak ML tetap mempunyai hash yang sama. Tidak ada training ulang atau perubahan target. Artefak baseline asli tetap tervalidasi, `target_approved=false`, `real_model_validated=false`.

## 6. File dibuat/diubah

| Kelompok | File |
| --- | --- |
| Sinkronisasi terbatas | Baru `backend/app/warehouse_sync.py`, `etl/sync_main_warehouse.py` |
| Audit transaksi | Diubah `backend/app/warehouse_audit.py` agar inspeksi memakai koneksi transaksi yang sama |
| Regression tests | Baru `backend/tests/test_warehouse_sync.py`, `backend/tests/test_source_archive.py` |
| Docker/startup | Diubah `compose.yaml`: backend healthcheck, frontend menunggu backend, maintenance profile tools; baru `scripts/start_main.ps1`; `scripts/start_cp3_demo.ps1` menjadi alias utama tanpa initial load |
| Verifier dan keamanan arsip | Default `etl/verify_cp3_demo.py` diarahkan ke 8080/folder bukti baru; `buat_zip.py` mengecualikan private/actual/raw, backup, credentials/key, DB lokal, folder konfigurasi sensitif dan symlink file |
| Panduan/laporan | `README.md`, `docs/CP3_DEMO_SCRIPT.md`; penanda riwayat pada CP3 final/progress/checklist, audit P0/P1 dan handoff; baru `docs/CP3_MAIN_STACK.md` serta laporan ini |
| Bukti | `reports/cp3_main_consolidation/`; backup privat lokal di `data/private/backups/` yang diabaikan Git |

Perubahan/untracked files yang sudah ada sebelum tugas ini dipertahankan. Tidak ada Git commit/push otomatis. Script ZIP tidak dijalankan pada repository asli; pengujiannya hanya menggunakan proyek palsu.

## 7. Cara menjalankan dan pekerjaan tersisa

```powershell
# Dari root, Docker Desktop aktif. Tidak ada ETL atau reset otomatis.
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start_main.ps1
```

Buka **http://127.0.0.1:8080**. Panduan operasi, backup dan batas sinkronisasi: [CP3_MAIN_STACK.md](CP3_MAIN_STACK.md). Jangan menjalankan `down -v`, menggabungkan volume, atau memuat ulang dataset hanya untuk mengganti alamat dashboard. Backup di lokasi privat perlu disimpan tim dengan kebijakan akses/retensi yang sesuai.

Konsolidasi teknis ini tidak menutup keputusan dosen mengenai target/horizon, protokol pasangan BP, arti tidur aktual, periode/inklusi, penanganan anomali, kecukupan/izin data primer, atau penerimaan demo sintetis untuk CP3. Logbook, kontribusi dan deklarasi AI tetap harus dilengkapi tim secara faktual. Data aktual tidak dicampur dengan sintetis dan tidak dipromosikan ke API publik.
