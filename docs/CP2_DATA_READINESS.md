# CP2 — Data Readiness: hasil implementasi dan verifikasi

**SELESAI SECARA TEKNIS PADA DATA SINTETIS / SIMULASI.** Ini bukan pernyataan bahwa persyaratan dataset penelitian aktual atau persetujuan dosen telah terpenuhi. Lingkup pekerjaan berhenti pada CP2; frontend, modelling, prediksi, dan artefak model tidak diubah.

## 1. Audit awal dan perubahan

Fondasi sebelumnya sudah memiliki dua CSV, tiga dimensi, dua fakta, parser, dan CLI. Kekurangan CP2: dictionary belum mencakup semua kolom, kualitas belum terukur sebelum–sesudah, belum ada notebook EDA data readiness, parser `hari` kehilangan seluruh aktivitas mingguan, serta belum ada bukti integrasi PostgreSQL/idempotensi yang terisolasi.

| File / kelompok | Status | Hasil |
| --- | --- | --- |
| backend/app/pipeline.py | Diubah | Parser berbasis kontrak kolom, integer tanpa pembulatan diam-diam, audit sel/baris, karantina, transaksi load dengan rollback |
| backend/app/survey_schema.py | Dibuat | Kontrak 24+28 kolom, satuan/kategori/format/NA dan asumsi tidur |
| backend/app/quality.py | Dibuat | Completeness/validity/consistency/uniqueness, normalisasi, fingerprint, IQR, jejak nomor baris sumber |
| backend/app/readiness.py | Dibuat | Analisis dengan grain yang sama, sepuluh figur dan renderer laporan/dictionary |
| backend/app/warehouse_audit.py | Dibuat | Introspeksi PK/FK/unique index, orphan, hitungan, hash isi natural; SELECT-only |
| etl/import_data.py | Diubah | Dry-run default, mode commit eksklusif, laporan terstruktur, error batch tanpa koneksi DB pada dry-run |
| etl/data_readiness.py | Dibuat | Generator laporan/dictionary/temuan/gambar tanpa koneksi database |
| etl/execute_eda.py | Dibuat | Runner notebook memakai Python pemanggil dan kernel sementara |
| etl/verify_warehouse.py | Dibuat | Audit read-only, optional laporan JSON; PostgreSQL memakai transaksi READ ONLY |
| backend/tests/test_cp2.py; conftest.py | Dibuat | Skenario valid/invalid, privasi, relasi, rollback, idempotensi dan isolasi DB |
| backend/tests/test_api_v2.py | Diubah | Fixture terisolasi per test; menghapus pola pembuatan/penghapusan test_tmp.db di root |
| backend/requirements-dev.txt; backend/Dockerfile.cp2 | Diubah / dibuat | Kebutuhan notebook/plotting/test dan image tooling mandiri |
| notebooks/02_eda_data_readiness.ipynb | Dibuat, dieksekusi | 20 sel total, 10 sel kode lulus, 10 gambar PNG tertanam |
| docs/DATA_DICTIONARY.md; ERD.md | Diperbarui | Seluruh 52 kolom sumber, kolom turunan, natural key, grain, PK/FK/index |
| docs/DATA_QUALITY_REPORT.md; EDA_FINDINGS.md | Dibuat dari perhitungan | Laporan sebelum–sesudah dan lima temuan SIMULASI |
| reports/cp2/ | Dibuat | JSON kualitas/EDA/provenance/warehouse, CSV, gambar, bukti verifikasi |
| README.md; .gitignore | Diubah | Perintah Windows/VS Code/Docker; cache lokal diabaikan |

`backend/app/models.py`, `analytics_v2.py`, dan `compose.yaml` diperiksa. Struktur/grain/FK yang ada sudah memadai; tidak memerlukan perubahan skema atau service produksi untuk CP2. Bukti warehouse memeriksa constraint dan unique index yang benar-benar terpasang.

## 2. Hasil audit dan cleaning

| Ukuran | Profil | Harian | Sesi turunan |
| --- | ---: | ---: | ---: |
| Raw | 19 × 24 kolom | 570 × 28 kolom | Dua sesi per catatan harian |
| Diterima / dihasilkan | 19 | 570 | 1140 |
| Dikarantina pada fixture | 0 | 0 | 0 sesi tidak lengkap |
| Kelebihan natural key duplikat | 0 | 0 | 0 |
| ID harian tanpa profil diterima | — | 0 | — |

- Parser aktivitas mingguan kini menerima `3 hari` sampai `7 hari` pada kolom bersatuan hari; 19 nilai terpulihkan pada hasil ETL baru. Tidak ada nilai sumber diubah.
- Tidur tetap NA pada 6/570 catatan (1,053%); duduk 3/570 (0,526%); jumlah merokok 550/570 (96,491%). Missing jumlah merokok tidak diasumsikan nol.
- Semua pembacaan fixture lolos pagar numerik teknis; 1140 sesi memiliki SBP dan DBP rerata. Ada **25 sesi** dengan setidaknya satu flag pencilan 1,5 IQR; tetap dipertahankan, tidak dihapus hanya karena flag statistik.
- Kategori duduk dalam sumber sebenarnya menggunakan en dash yang valid. Alias karakter rusak diuji dengan input mutasi, bukan diklaim sebagai kesalahan yang ditemukan pada fixture asli.
- Sel invalid pada input uji menjadi NA dengan alasan. ID/tanggal invalid, ID tanpa profil, dan duplikasi berikutnya dikarantina. Skema yang tidak cocok membatalkan seluruh batch.
- Perbandingan sebelum–sesudah mencakup 52 kolom sumber. Tipe/satuan diinterpretasikan sesuai dictionary, bukan menganggap semua string CSV sebagai invalid. Identitas dikeluarkan secara sengaja; bukan missing baru yang harus diimputasi.

Rincian per kolom tersedia di `DATA_QUALITY_REPORT.md`, `reports/cp2/quality.json` dan `completeness_before.csv`/`completeness_after.csv`. `issues.csv` dan `pressure_anomalies.csv` menghubungkan temuan ke nomor baris sumber tanpa menyalin nama. `source_manifest.json` menyimpan hash kedua raw CSV, kode perhitungan, bentuk tabel, dan versi lingkungan.

## 3. Lima temuan EDA — SIMULASI

| No. | Temuan dari perhitungan | Bukti grafik |
| --- | --- | --- |
| 1 | 19 ID, usia 20–59 tahun, rerata 41,42 tahun; 9 provinsi dan 16 kabupaten/kota. 570 catatan bukan 570 orang. | 01_profile_age.png; 02_profile_gender.png; 03_profile_location.png |
| 2 | Pada 570 pasangan ID-tanggal, rerata selisih SBP Malam−Pagi adalah **0,470 mmHg**. | 05_session_comparison.png |
| 3 | Rerata SBP sesi 1 September **117,816 mmHg**, 30 September **118,711 mmHg**; selisih **+0,895 mmHg**. | 06_daily_trend.png |
| 4 | Korelasi Pearson aktivitas menit–SBP harian **−0,012**; tidur–SBP **0,059**. Catatan berulang tetap saling berkaitan. | 07_lifestyle.png; 08_numeric_correlation.png |
| 5 | Missing tidur dan duduk tetap terlihat, jumlah merokok tidak diisi nol, dan 25 sesi berflag IQR dipertahankan. | 09_missing_before_after.png; 10_pressure_anomalies.png |

Semua hasil hanya menggambarkan data buatan. Tidak ada klaim sebab-akibat, diagnosis, prevalensi, atau inferensi populasi. Notebook mencakup histogram sistolik/diastolik, perbandingan sesi, tren, stres 1–5, tidur, aktivitas, korelasi, missing, duplikasi, dan outlier. Lihat `EDA_FINDINGS.md` untuk uraian/gambar dan `reports/cp2/eda_summary.json` untuk nilai terstruktur.

## 4. Warehouse PostgreSQL

| Tabel | PostgreSQL aktif (read-only) | Load baru PostgreSQL terisolasi |
| --- | ---: | ---: |
| dim_participant_v2 | 19 | 19 |
| dim_date_v2 | 30 | 30 |
| dim_session_v2 | 2 | 2 |
| fact_bp_session_v2 | 1140 | 1140 |
| fact_daily_behavior_v2 | 570 | 570 |
| dataset_state_v2 | 1 | 1 |
| Orphan pada lima relasi FK | 0 | 0 |
| active_days_week NA | 19 (hasil ETL lama) | 0 (parser diperbaiki) |

PK `id`, unique index ID/tanggal dimensi, serta unique constraint natural key fakta diverifikasi. Semua tes mutasi dilakukan pada PostgreSQL terpisah `toba_cp2_test`, port localhost acak, tmpfs, tanpa memakai volume aplikasi.

**Warehouse aktif tidak di-reset, di-update, atau di-load ulang.** Hash isi natural sebelum dan sesudah pekerjaan tetap:

`2c72512aed5d6c4f1e124f1be7ec47a03d0635fe2a6579fe6c3a7edd9c14c267`

Hash isi natural hasil load baru terisolasi:

`0a91e24fecb8482092b2687cf144e84cf64fccfadbb46c7653d061fbbb2deefc`

Perbedaan mencerminkan transformasi baru (misalnya aktivitas mingguan dan normalisasi jam), bukan kehilangan baris. Perbaikan workspace belum dipromosikan ke isi warehouse/image backend aktif. Penerapan ke deployment merupakan tindakan terkontrol terpisah, bukan bagian pekerjaan ini.

`warehouse_active_readonly.json` dan `warehouse_isolated.json` menyimpan bukti. Tes reload membandingkan natural key/nilai/hash, bukan menuntut surrogate ID sama. Tes juga membuktikan rollback jika batch gagal, penolakan FK/natural key duplikat, dan pemeliharaan tabel sentinel di luar daftar tabel v2.

## 5. Perintah dan hasil pengujian sebenarnya

| Pemeriksaan | Perintah / konteks | Hasil |
| --- | --- | --- |
| ETL dry-run | `python -m etl.import_data --synthetic --dry-run --report-dir reports/cp2/dry_run --summary` | Lulus; tanpa koneksi/perubahan DB |
| Laporan EDA/kualitas | `python -m etl.data_readiness --synthetic` | Lulus; 52 kolom, 5 temuan, 10 PNG; hash raw tidak berubah |
| Windows / SQLite memori | `python -m pytest backend/tests/test_cp2.py backend/tests/test_api_v2.py -q -p no:cacheprovider` | **27 passed**, 13,16 detik |
| Windows / PostgreSQL 16 sementara | Perintah pytest sama; `CP2_TEST_DATABASE_URL` menunjuk `localhost/toba_cp2_test` terisolasi | **27 passed**, 16,47 detik |
| Docker / Python 3.12 / SQLite memori | `docker run --rm -v "${projectRoot}:/workspace:ro" toba-cp2-check` | **27 passed**, 14,00 detik |
| Notebook Run All otomatis | `python -m etl.execute_eda` (host), dan runner yang sama melalui image `toba-cp2-check` | 10 sel kode lulus; 10 PNG tertanam; tidak ada error sel |
| CLI commit | `python -m etl.import_data --synthetic --commit --summary` dengan DATABASE_URL **sementara** | Lulus; 19/570/1140 |
| Verifikasi warehouse | `python -m etl.verify_warehouse --output reports/cp2/warehouse_isolated.json` pada DB sementara | PK/FK/keunikan benar; orphan 0; aktivitas mingguan NA 0 |
| Image tooling | `docker build -f backend/Dockerfile.cp2 -t toba-cp2-check ./backend` | Build berhasil; service aktif tidak di-restart |
| Konsistensi artefak | Perbandingan JSON kualitas CLI vs EDA, hash kode/raw, validasi nbformat/output | Lulus |

Setiap run pytest menghasilkan satu peringatan deprecation dari Starlette/httpx; bukan kegagalan tes. Kernel notebook sementara juga memberi peringatan transport TCP, tetapi seluruh sel berhasil dan kernel dihentikan setelah eksekusi. Container PostgreSQL tes milik sesi ini dihentikan dan dibersihkan otomatis setelah verifikasi; image tooling tetap tersedia untuk reproduksi.

Versi paket host dicatat di manifest. Windows memakai Python 3.13 dan image tooling memakai Python 3.12; pandas juga berbeda minor, dengan hasil uji dan angka EDA konsisten. Dependensi masih berupa rentang versi; reproduksi numerik dapat diperiksa terhadap manifest dan input hash. Tidak ada klaim notebook bit-identical lintas versi/rendering platform.

Suite `backend/tests/test_api.py` merupakan kontrak v1 yang dihentikan dan berada di luar suite CP2/v2 terpilih ini. Tidak diklaim lulus; frontend dan perbaikan kontrak v1 tidak dikerjakan pada CP2.

## 6. Checklist CP2

| Kebutuhan | Status |
| --- | --- |
| Audit implementasi dan dua fixture | SELESAI |
| Dictionary lengkap 24+28 kolom dan asumsi | SELESAI |
| Completeness, validity, consistency, uniqueness sebelum–sesudah | SELESAI |
| Audit BP, karantina/alasan dan jejak sumber | SELESAI |
| Notebook EDA berurutan, grafik berlabel, minimal 5 temuan | SELESAI |
| Minimum 1 fakta + 3 dimensi, grain, PK/FK/index | SELESAI (2 fakta + 3 dimensi) |
| ETL dry-run, load PostgreSQL, idempotensi dan rollback | SELESAI pada database terisolasi |
| Reproduksi Windows/VS Code dan Docker | SELESAI |
| Perlindungan raw/identitas, pemisahan sintetis-aktual | SELESAI untuk lingkup fixture CP2 |
| Data penelitian aktual tervalidasi dan memenuhi minimum | BELUM SELESAI; tidak dipenuhi dengan simulasi |
| Persetujuan definisi data/protokol/kriteria oleh dosen | BELUM SELESAI |

## 7. Hal yang masih membutuhkan data aktual/konfirmasi dosen

1. Definisi pertanyaan tidur aktual, tipe input dan perlakuan pecahan Excel.
2. Kriteria usia/wilayah/inklusi, izin dan persetujuan responden, registry ID aktual.
3. Apakah minimum baris primer dapat dipenuhi oleh catatan berulang; laporkan jumlah individu secara terpisah.
4. Verifikasi tanggal tidak wajar, koreksi duplikasi, kategori jawaban lain, serta nilai BP ekstrem berdasarkan sumber/protokol; tidak ditebak dari fixture.
5. Ketentuan pengukuran terlewat dan aturan sesi/hari valid untuk penelitian. Definisi teknis minimal satu SBP dan satu DBP per sesi saat ini harus ditinjau sebelum klaim penelitian.

Pekerjaan berhenti pada CP2. Tidak ada penggabungan sintetis-aktual, perubahan frontend/modul prediksi, reset volume, atau commit/push otomatis.
