# Jalur utama CP3 — Toba Health Insight

Tanggal: 10 November 2026. **DATA SINTETIS / SIMULASI**. Target ML tetap usulan, bukan diagnosis.

## Satu jalur penggunaan

| Bagian | Nilai |
| --- | --- |
| Project Compose | `tension-dashboard` |
| Konfigurasi | `compose.yaml` |
| Dashboard | http://127.0.0.1:8080 |
| API docs | http://127.0.0.1:8080/api/docs |
| PostgreSQL | Service `db`, database `toba_health`, volume utama yang sudah ada |
| Dataset CP3 | 19 profil / 570 ID–tanggal / 1.140 sesi sintetis |

React → FastAPI → satu PostgreSQL permanen. Tidak ada penggabungan volume atau salinan database 8081 ke 8080. Konfigurasi `compose.cp3-demo.yaml` dan `compose.p0-p1-audit.yaml` disimpan untuk riwayat/QA terisolasi; jangan dipakai sebagai aplikasi harian.

## Menjalankan aplikasi

Dari root project, setelah Docker Desktop aktif:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start_main.ps1
```

Script menunggu healthcheck dan memeriksa baseline/batch untuk sumber sintetis. Tidak melakukan ETL, membuat data contoh, reset database, mengganti volume, atau mengubah `.env`. Alias lama `scripts/start_cp3_demo.ps1` memanggil script utama yang sama dan tidak lagi membuat stack 8081.

Jika clone baru mempunyai warehouse kosong, empty state adalah perilaku yang benar. Startup tidak mengisi data otomatis. Prosedur initial load berbeda dari sinkronisasi database berisi data dan membutuhkan validasi serta otorisasi tersendiri. Jangan memakai script sinkronisasi di bawah untuk mengisi database kosong.

## Memeriksa tanpa perubahan database

```powershell
docker compose -p tension-dashboard ps
docker compose -p tension-dashboard run --rm --no-deps maintenance python -m etl.sync_main_warehouse --dry-run
.venv\Scripts\python.exe -m etl.verify_cp3_demo --url http://127.0.0.1:8080 --output reports/cp3_main_consolidation/http-verification.json
```

Service `maintenance` memakai profile tools dan hanya berjalan saat dipanggil eksplisit. Workspace di-mount read-only. Pada mesin baru, bangun image dengan `docker compose -p tension-dashboard build maintenance`. Jangan mencetak environment atau `docker compose config` yang mengandung secret ke laporan publik.

Sinkronisasi hanya mengenali dataset sintetis yang seluruh barisnya sama dengan dua CSV fixture. Perubahan yang diperbolehkan: mengisi `active_days_week` kosong dari profil sumber, mengubah waktu `HH:MM` menjadi **waktu yang sama** `HH:MM:00`, dan memperbarui metadata ETL. Nilai BP/perilaku, semua PK/FK, jumlah baris serta tabel legacy dipertahankan. Perbedaan lain, data aktual, hash yang berubah, atau input kosong ditolak. Ini bukan ETL replace dan tidak menggunakan DELETE/INSERT pada database target.

Mode commit membutuhkan `--expected-current-hash`, `--backup-file` dan `--backup-sha256`. Jangan menyalin hash contoh dari laporan untuk database lain. Lakukan backup, restore-test staging, dry-run dan review baru sebelum commit berikutnya. Pengguna telah mengotorisasi penerapan pada database utama dalam sesi konsolidasi ini; otorisasi tersebut bukan izin otomatis untuk mengganti data aktual di kemudian hari.

## Backup dan pemulihan

Backup custom-format `pg_dump -Fc` sebelum konsolidasi berada pada `data/private/backups/`; lokasi dan SHA256 dicatat pada `reports/cp3_main_consolidation/operation.json`. Folder ini diabaikan Git dan dikecualikan pembuat ZIP. Simpan salinan backup pada media privat yang dikelola tim; jangan unggah ke repo atau lampiran publik.

Backup telah dipulihkan ke PostgreSQL RAM staging sebelum pengujian sinkronisasi. Untuk pemulihan di masa depan: pulihkan dahulu ke instance terisolasi, bandingkan fingerprint/jumlah/tabel, lalu review rencana pemulihan. Jangan menjalankan `pg_restore --clean` atau restore ke database utama tanpa persetujuan baru; hal tersebut dapat menimpa perubahan setelah backup.

Rollback saat transaksi sinkronisasi gagal dilakukan otomatis sebelum commit. Setelah commit, tindakan pemulihan harus mempertimbangkan data yang mungkin masuk kemudian; jangan mengembalikan seluruh backup secara otomatis.

## Pengujian dan batas

Gunakan laporan [CP3_MAIN_CONSOLIDATION_REPORT.md](CP3_MAIN_CONSOLIDATION_REPORT.md) untuk hasil yang benar-benar dijalankan. Browser diarahkan ke 8080 melalui `CP3_BROWSER_BASE_URL`; bukti memakai folder `reports/cp3_main_consolidation/`. Test backend menggunakan SQLite in-memory atau PostgreSQL `toba_cp2_test` yang terisolasi, bukan `toba_health`.

Target `future_7d_mean_sbp` tetap `target_approved=false`. Tidak ada training ulang, perubahan `.env`, pencampuran data aktual/sintetis, deployment publik atau pekerjaan CP4 dalam konsolidasi ini.
