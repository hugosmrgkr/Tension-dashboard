# Hasil pengerjaan P0/P1 — 10 November 2026

## Ringkasan

Pemeriksaan dilakukan pada ZIP proyek terbaru yang tersedia. Mayoritas perubahan P0/P1 pada backend v2 dan frontend aktif sudah berada di arsip hasil tinjauan sebelumnya. Pada sesi ini, bagian ETL dan pengujian diperbaiki lagi agar dry-run benar-benar terpisah dari konfigurasi database dan regression test dapat dijalankan dari ZIP tanpa metadata Git.

Pekerjaan teknis pada fixture sintetis telah diverifikasi dengan suite backend. Namun, P0/P1 belum dapat dinyatakan selesai untuk penggunaan data penelitian aktual karena ekspor Google Forms aktual dan beberapa keputusan dosen/tim belum tersedia.

## Perubahan kode pada sesi ini

1. `etl/import_data.py`
   - Konfigurasi database serta fungsi promosi ETL hanya diimpor ketika `--commit` digunakan.
   - Mode `--dry-run` memvalidasi CSV tanpa membuat engine atau membuka koneksi database.
   - Pengujian dilakukan dengan `DATABASE_URL` PostgreSQL yang sengaja tidak dapat diakses dan tanpa driver PostgreSQL terpasang; dry-run tetap berhasil.

2. `backend/app/pipeline.py`
   - Model ORM dipindahkan menjadi impor lokal di fungsi yang benar-benar menulis atau membaca warehouse.
   - Import modul untuk parsing dan validasi tidak lagi membuat engine database sebagai efek samping.

3. `backend/tests/test_p0_p1_audit.py`
   - Tes aturan `.gitignore` sekarang membuat repository sementara, sehingga tidak bergantung pada folder `.git` yang memang tidak ikut di dalam ZIP.

## Hasil verifikasi yang benar-benar dijalankan

| Pemeriksaan | Hasil |
|---|---|
| Seluruh tes backend | 73 passed, 1 skipped |
| Tes yang dilewati | Tes API v1 lama; API v1 telah dipensiunkan dan kontrak aktif v2/CP3 tetap diuji |
| ETL dry-run fixture | 19/19 profil diterima; 570/570 catatan harian diterima; 1.140 sesi diturunkan dan valid |
| ETL dry-run tanpa driver PostgreSQL | Lulus; tidak membuat koneksi atau mengubah database |
| Kompilasi modul Python | `compileall` berhasil |
| Frontend `npm test`, build, browser test | Belum dijalankan pada sesi ini karena `npm ci` timeout saat mengunduh dependensi |

Perintah backend yang berhasil:

```bash
PYTHONPATH=backend python -m pytest backend/tests -q -p no:cacheprovider -rs
```

Perintah dry-run yang berhasil:

```bash
PYTHONPATH=backend python -m etl.import_data --synthetic --dry-run --summary
```

## Status P0/P1 yang masih memerlukan tindak lanjut

| ID | Status dan syarat berikutnya |
|---|---|
| P0-01 | Kontrak dua formulir telah diuji pada fixture sintetis. Masih perlu dry-run terhadap ekspor Google Forms aktual yang sudah disanitasi. |
| P0-02 | Struktur sesi dan penyimpanan empat bacaan tersedia. Minimum pasangan, pengulangan, dan cakupan hari masih menunggu keputusan dosen/tim. |
| P0-04 | Tidur tersimpan sebagai jam. Semantik jawaban aktual belum boleh ditebak; cocokkan dengan pertanyaan serta ekspor aktual sebelum mapping. |
| P0-07 | Jalur aktif menggunakan regresi SBP numerik dan target `future_7d_mean_sbp`. Persetujuan target/horizon tetap pending (`target_approved=false`). |
| P1-08 | Audit kualitas, karantina, dan flag IQR tersedia. Periode penelitian, reviewer, keputusan koreksi/eksklusi, dan decision log aktual masih harus ditetapkan. |

P0-03, P0-05, P0-06 serta P1-01 sampai P1-07 sudah memiliki implementasi teknis pada jalur aktif v2 menurut inspeksi kode dan regression tests. Ini bukan pengesahan metodologi atau validasi klinis.

## Batas pemeriksaan

- Arsip yang diberikan berisi fixture sintetis, bukan ekspor responden aktual. Angka 19 profil, 570 catatan ID–tanggal, dan 1.140 sesi adalah data simulasi.
- Tidak ada pemuatan ETL ke warehouse, reset database, penghapusan volume, perubahan `.env`, atau perubahan CSV/XLSX sumber pada sesi ini.
- Tidak ada commit atau push Git.
- Komponen legacy seperti `backend/app/service.py`, `frontend/src/pages/OtherPages.jsx`, dan `frontend/src/pages/Dashboard.jsx` masih memiliki logika lama, tetapi tidak dipakai oleh entrypoint aktif. Jangan menghubungkannya kembali tanpa migrasi terpisah.
- Frontend belum diretest pada sesi ini. Laporan audit lama di repository memuat bukti test/build terdahulu, tetapi bukan hasil pengulangan baru.

## Langkah sebelum memakai data aktual

1. Siapkan ekspor profil dan harian yang sudah menghapus nama, nomor kontak, dan identitas langsung.
2. Cocokkan header secara eksplisit; jangan mengubah urutan atau menebak kolom.
3. Jalankan ETL `--dry-run`, baca laporan accepted/rejected/issues, lalu minta persetujuan aturan BP, tidur, target dan penanganan anomali.
4. Jangan gunakan `--commit` pada warehouse aktif sampai hash target, akses, backup, dan persetujuan eksplisit diperiksa.
