# Hugo Tahap 4 — Pengujian integrasi dan bukti penerimaan

Tanggal: **17 November 2026**. Status: **SELESAI untuk integrasi teknis sintetis**.
Tahap ini dilanjutkan setelah konfirmasi Hugo. Bukan klaim proyek final selesai,
bukan persetujuan dosen, dan bukan bukti model layak untuk responden aktual.

## Ringkasan hasil

Alur yang benar-benar diuji: **dua CSV sintetis → ETL CP2 → PostgreSQL → FastAPI →
model P2 terverifikasi → React**. Tidak ada perubahan kode produksi baru pada
Tahap 4; tambahan berupa regression/acceptance test, verifier dan dokumentasi.
Implementasi produksi Tahap 2–3 dipertahankan dan diuji bersama seluruh suite.

| Pemeriksaan | Hasil nyata | Bukti |
|---|---|---|
| Seluruh backend, SQLite | 232 passed, 1 skipped; 135,42 detik | [JUnit SQLite](../reports/hugo_stage4/backend-sqlite.xml) |
| Seluruh backend, PostgreSQL 17.6 | 232 passed, 1 skipped; 238,98 detik | [JUnit PostgreSQL](../reports/hugo_stage4/backend-postgresql.xml) |
| Frontend unit/component | 22 passed | `npm test`, catatan hasil di [verification.json](../reports/hugo_stage4/verification.json) |
| Production build | Berhasil; 1.602 modul; 13,94 detik | `npm run build`; ringkasan pada verification.json |
| Browser Edge/Playwright | 21 passed, 0 failed, 0 flaky; seluruh 8 halaman desktop/ponsel | [JSON browser](../reports/hugo_stage4/browser-results.json) |
| Verifier HTTP pada PostgreSQL sementara | Seluruh 7 pemeriksaan lulus | [HTTP verification](../reports/hugo_stage4/http-verification.json) |
| Artefak/dataset/Compose terlindungi | 16 hash SHA256 sebelum/sesudah identik | [Sebelum](../reports/hugo_stage4/protected_before.json), [sesudah](../reports/hugo_stage4/protected_after.json) |

Satu skip backend adalah modul API v1 yang sudah dipensiunkan, bukan pengujian
integrasi baru yang dilewati. Ada satu peringatan deprecation Starlette/httpx.
Build memberi peringatan ukuran bundle Plotly (~4,9 MB); build tidak gagal.
Optimasi bundle menjadi tindak lanjut performa, tanpa redesign pada tahap ini.

## Lingkungan dan perlindungan data

- Docker daemon tidak tersedia saat pemeriksaan; build/container Docker dan Linux
  **tidak diuji pada tahap ini**. Tidak menjalankan stack utama `localhost:8080`.
- Menggunakan binary PostgreSQL lokal 17.6 untuk membuat **cluster baru** di folder
  sementara berawalan `toba_hugo_stage4_`, loopback `127.0.0.1:63846`.
- Database `toba_cp2_test` khusus pytest dan `hugo_browser_test` khusus API/browser.
  Cluster ini terpisah dari layanan PostgreSQL Windows yang sudah ada.
- API uji berjalan sementara di `127.0.0.1:59724`; browser memakai preview 4173
  dengan proxy ke API tersebut. Browser membaca PostgreSQL, bukan respons analitik mock.
- ETL commit hanya terjadi pada database pengujian terisolasi. Tidak ada ETL commit
  pada warehouse aktif, reset volume, perubahan `.env`, data aktual atau model.
- Autentikasi dimatikan hanya pada server browser lokal sementara. Tes backend juga
  memeriksa mode token dengan role viewer/admin dan guard aktual.
- API dan cluster pengujian telah dihentikan setelah pengujian. Folder sementara
  tidak dihapus rekursif; tidak ada layanan PostgreSQL utama yang dihentikan.
- Konfigurasi uji tercatat di [postgresql-test-context.json](../reports/hugo_stage4/postgresql-test-context.json).

## Matriks penerimaan

| Area | Bukti yang diperiksa | Hasil / batas |
|---|---|---|
| Grain dan jumlah | SQL Participant / DailyBehavior / BPSession | 19 profil, 570 ID-tanggal, 1.140 ID-tanggal-sesi |
| KPI dari warehouse | Hitung SQL dan bandingkan API; serving dilarang membuka CSV lewat monkeypatch | Sesuai; rerata SBP 118,9 dan DBP 72,6 mmHg pada batch penuh |
| Filter dan ekspor | ID SIM001, 1–3 September, Pagi dan Malam secara terpisah | Masing-masing 3 sesi; API dan CSV memiliki cakupan sama |
| Paritas fitur | Rekonstruksi seluruh 323 window dari warehouse vs hasil persiapan CSV | Sama; bukan hanya perbandingan angka tampilan |
| Paritas prediksi | Seluruh 7 origin test historis pada artefak P2 | Output API sama dengan prediksi artefak pada pembulatan 2 desimal |
| Histori dan waktu | 7 hari historis, fitur training/inferensi dan batas origin | Riwayat berasal dari window yang sama; tidak memasukkan hari target |
| Provenance | Manifest/hash, run ID dan fingerprint training/inferensi | Cocok; `synthetic_historical_test`, bukan skor validasi data aktual |
| Sumber aktual dan akses | Token viewer/admin; source guard dalam fixture uji | Ekspor viewer 403/admin 200; analitik aktual 403/prediksi aktual 409 |
| Error dan hasil lama | Injeksi HTTP 409 `MODEL_INCOMPATIBLE` setelah prediksi sukses | UI menghapus angka/grafik lama dan menampilkan error |
| Data kosong | Filter tanggal tanpa data dan empty state browser | Tidak ada grafik/angka estimasi palsu; rerata null |
| UI 8 halaman | Browser desktop/ponsel, filter, ekspor, cross-filter, tooltip | 21 tes lulus; screenshot tersedia |

Injeksi 409 di browser adalah simulasi kegagalan yang disengaja untuk memeriksa
perilaku UI, bukan klaim backend benar-benar mengalami kerusakan model.
Tujuh origin historis merupakan contoh test tersimpan, bukan tujuh responden baru
atau pengukuran performa independen tambahan. Tidak melatih ulang atau mengganti model.

Model aktif tetap Linear Regression P2, run `d43ac5c17c70cead67c7`.
Fingerprint batch `51394dad1ec8fa22d6ff2ed5503319625e956b366fe8ed87b92e8e0824d32427`.
Peringatan bahwa model tidak mengungguli naif pada validasi tetap ditampilkan.
Status artefak `target_approved=false` tetap dipertahankan karena belum ada bukti
persetujuan formal yang disimpan. Tidak mengubah keputusan akademik secara diam-diam.

## Bukti visual

- [Prediksi desktop](../reports/hugo_stage4/screenshots/prediction-desktop.png).
- [Riwayat pada ponsel](../reports/hugo_stage4/screenshots/prediction-mobile-history.png).
- [Empty state](../reports/hugo_stage4/screenshots/empty.png).
- [Semua screenshot](../reports/hugo_stage4/screenshots/): `desktop-1`–`desktop-8`
  dan `mobile-1`–`mobile-8` mengikuti urutan navigasi aktif.

Gambar prediksi desktop/ponsel diperiksa secara visual: riwayat SBP/DBP memakai
sumbu mmHg yang sama, berhenti pada origin; dua batang membandingkan satu rerata
masa depan dengan naif. Label sintetis, rentang tanggal dan batas interpretasi terlihat.

## Percobaan yang gagal dan koreksinya

Percobaan browser pertama membaca path konfigurasi relatif dari folder `frontend`
secara keliru (`reports/...` alih-alih `../reports/...`). Proxy menjadi port 80
dan menghasilkan connection refused pada tiga tes awal; proses dihentikan.
Path dan error handling PowerShell diperbaiki, lalu seluruh suite dijalankan ulang:
**21 lulus**. Ini kesalahan harness pengujian, bukan bug aplikasi yang disembunyikan.

Saat cleanup, validasi path awal mengenali perbedaan nama pendek Windows
`TUFGAM~1` dan nama panjang `TUF GAMING`; validasi dikoreksi menggunakan
`[IO.Path]::GetTempPath()` sebelum menghentikan cluster unik yang sama.
Penghentian cluster memerlukan eksekusi di luar sandbox, lalu berhasil. Tidak
menghentikan service PostgreSQL Windows atau proses berdasarkan pencarian nama umum.

## File Tahap 4

| File | Perubahan |
|---|---|
| `backend/tests/test_hugo_acceptance.py` | 4 kasus penerimaan: SQL/API/CSV, fitur dan 7 origin, otorisasi/source guard |
| `frontend/tests/browser/prediction_acceptance.spec.js` | Regression browser: kegagalan model membersihkan hasil lama |
| `frontend/tests/browser/dashboard.spec.js` | Nama tes diperjelas sebagai API-backed; tidak mengklaim PostgreSQL pada semua konfigurasi |
| `etl/verify_hugo_integration.py` | Verifier HTTP read-only, URL loopback eksplisit, tanpa ETL/training/database write |
| `docs/HUGO_STAGE4_REPORT.md` | Laporan penerimaan ini |
| `docs/MODEL_INTEGRATION_CONTRACT.md`, `docs/TUGAS_HUGO.md` | Status dan batas penyelesaian diperbarui |
| `reports/hugo_stage4/` | JUnit, browser JSON/screenshot, hash dan hasil verifier |

Perubahan aplikasi Tahap 2 ada di `model_registry.py`, `model_service.py`, `main.py`;
Tahap 3 menambah histori inferensi dan grafik di `PrediksiTekananDarah.jsx` serta
`components/prediction/PredictionCharts.jsx`. Lihat laporan tahap masing-masing.
Semua perubahan tetap lokal; tidak membuat commit, push, merge atau branch.

## Menjalankan ulang dengan aman

Gunakan **database disposable khusus pengujian**. Suite backend membuat/menghapus
tabel fixture; jangan memberikan URL warehouse aktif. Contoh dari root workspace:

```powershell
$env:CP2_TEST_DATABASE_URL = 'sqlite://'
$env:OMP_NUM_THREADS = '1'
$env:OPENBLAS_NUM_THREADS = '1'
.\.venv\Scripts\python.exe -m pytest backend/tests -q -p no:cacheprovider
```

Untuk PostgreSQL, siapkan cluster/database uji baru dan ganti variabel tersebut
dengan URL database pengujian yang diizinkan fixture, misalnya `toba_cp2_test`.
Port 63846 pada laporan ini sudah dihentikan; jangan menganggap server masih tersedia.

```powershell
Set-Location frontend
npm test
npm run build
# Setelah API sintetis pada database uji terisolasi tersedia:
$ErrorActionPreference = 'Stop'
$env:TOBA_API_PROXY_TARGET = 'http://127.0.0.1:<PORT_API_UJI>'
$env:CP3_REPORT_DIR = '../reports/hugo_stage4-rerun'
$env:PLAYWRIGHT_CHANNEL = 'msedge'
npm run test:browser
```

Verifier read-only (jalankan dari root, ganti placeholder port terlebih dahulu):

```powershell
.\.venv\Scripts\python.exe -m etl.verify_hugo_integration --url http://127.0.0.1:<PORT_API_UJI> --require-postgres --output reports/hugo_stage4-rerun/http-verification.json
```

Verifier tidak menyediakan token; gunakan hanya API pengujian lokal yang sengaja
disiapkan tanpa autentikasi. Jangan mematikan autentikasi deployment untuk menjalankannya.
Fixture verifier khusus batch sintetis 19/570/1140, bukan validator dataset aktual umum.

## Status seluruh tahapan Hugo dan dependensi berikutnya

| Tahap | Status | Batas |
|---|---|---|
| 1. Draf kontrak integrasi | Selesai disusun | Review Aldi/Nahesson dan bukti persetujuan masih pending |
| 2. Registry/validasi artefak dan API | Selesai untuk adapter P2 sintetis | Belum registry rilis final/aktivasi model tuning atau aktual |
| 3. Visualisasi prediksi React | Selesai dan diuji | Model/label sesuai artefak sintetis yang tersedia |
| 4. Integrasi dan acceptance | Selesai untuk lingkungan sintetis terisolasi | Docker/Linux dan deployment utama belum diverifikasi pada tahap ini |

Yang masih memerlukan pekerjaan/koordinasi berikutnya:

1. **Aldi + Hugo:** kontrak data aktual, quality gate, kebijakan batch inferensi
   bertambah dan otorisasi aktual. Guard aktual tetap tertutup.
2. **Nahesson + Hugo:** paket rilis model yang disetujui, kontrak fitur dan bukti
   kelayakan sebelum mengganti adapter P2; tidak ada pemilihan model terbaru otomatis.
3. **Tim/dosen:** simpan bukti keputusan target, syarat data dan kelayakan ilmiah;
   hasil sintetis tidak membuktikan performa klinis atau performa pada data aktual.
4. **Ruben:** verifikasi container/deployment, HTTPS, backup/restore dan konfigurasi
   produksi ketika lingkungannya tersedia. Tahap ini tidak menggantikan pengujian itu.
5. **Kasih/tim:** review hasil, uji pengguna dan masukkan bukti kontribusi ke laporan.

Tahap 4 berhenti di sini sesuai pola konfirmasi Hugo. Tidak melanjutkan aktivasi
aktual, deployment, promosi model atau pekerjaan anggota lain secara otomatis.
