# Tugas Aldi untuk CP4 sampai final

Project: **Toba Health Insight**. Dokumen ini khusus tugas **Aldi** dan mengikuti
pembagian terakhir: Ruben menangani deployment serta Dashboard/Tren; Nahesson
menangani model serta Evaluasi/Faktor Risiko. Semua delapan halaman sudah dibagi.

Checklist adalah rencana kerja, **bukan klaim selesai**. Dokumen ini tidak membuat
branch, commit atau push. Jangan mengulang pekerjaan sintetis yang sudah selesai.

## Tugas utama
**Branch:** `feat/actual-data-readiness`  
**Halaman:** Kelola Data dan Data Partisipan  
**Tujuan:** dua ekspor formulir aktual dapat divalidasi, dibersihkan dan diterapkan
secara aman, dengan kualitas serta profil anonim yang dapat dipahami pengguna.

### Checklist pengerjaan

- [ ] Periksa header ekspor aktual terhadap kontrak dua formulir; lengkapi pemetaan
      yang terbukti perlu tanpa merusak dua CSV sintetis yang sudah digunakan.
- [ ] Validasi ID, relasi profil-harian, tanggal, grain ID-tanggal-sesi, dua
      pembacaan, satuan tidur dan seluruh kategori formulir.
- [ ] Catat missing, duplikasi, konflik koreksi dan anomali; pertahankan raw.
      Jangan memilih baris pertama atau membuat ID otomatis untuk menyembunyikan konflik.
- [ ] Dokumentasikan aturan ilmiah yang memerlukan keputusan dosen/tim. Jangan
      melonggarkan quality gate atau aturan BP secara sepihak.
- [ ] Siapkan prosedur ekspor ulang dan pembaruan batch berversi, accepted/rejected,
      dry-run, backup dan pemeriksaan target sebelum pemuatan manual.
- [ ] Hitung jumlah responden, tanggal, sesi valid dan window ML yang layak untuk
      Nahesson. Bedakan catatan tersedia dari contoh training yang benar-benar lengkap.
- [ ] Lengkapi visual Kelola Data: kelengkapan, karantina, cakupan periode dan
      status kesiapan analisis/ML dari API.
- [ ] Lengkapi visual Data Partisipan: demografi, BMI, lokasi dan tabel anonim;
      hitung profil satu kali per ID dan ikuti filter global.
- [ ] Bekerja sama dengan Hugo agar metadata aktual yang disetujui dapat ditampilkan
      secara terbatas; jangan membuka identitas pribadi atau data aktual ke publik.

### File milik Aldi

- `frontend/src/pages/KelolaData.jsx`, `DataPartisipan.jsx`
- `frontend/src/components/data-readiness/` — baru jika diperlukan
- `backend/app/survey_schema.py`, `pipeline.py`, `quality.py`, `bp_policy.py`,
  `readiness.py`, `etl_control.py`, `models.py`
- `etl/import_data.py`, `docs/DATA_DICTIONARY.md`, `docs/ERD.md`
- `warehouse/` dan `reports/actual_readiness/` — baru; dokumentasi/skema/bukti aman,
  bukan tempat mempublikasikan data responden aktual
- Tes khusus kompatibilitas formulir dan readiness, misalnya `test_actual_readiness.py`.

**DA:** cleaning, ETL, warehouse dan visual profil/kualitas. **DS:** kelayakan fitur,
target dan jumlah window untuk pemodelan.

**Hasil wajib:** kontrak data, hasil dry-run, laporan kualitas dan kelayakan ML,
visual React, serta panduan pembaruan dataset. Dokumen harus membedakan aturan
otomatis, koreksi yang disepakati dan isu pending.

**Dependensi:** ekspor aktual dan keputusan terkait formulir. Jika belum ada,
implementasikan validasi/tes kompatibilitas dengan fixture anonim; jangan klaim
validasi dataset aktual telah selesai. Tidak ada ETL commit ke DB aktif tanpa persetujuan.

## Titik awal bersama

- Delapan halaman aktif sudah dipisahkan dan tersedia pada checkout `main` yang
  diperiksa saat panduan dibuat. Cocokkan checkout masing-masing dengan hasil
  pemisahan sebelum mulai; lihat [peta halaman aktif](ACTIVE_PAGE_SPLIT.md).
- Dashboard, filter/cross-filter, tiga algoritma, tuning dan analisis error
  **sintetis** sudah ada. Jangan membuat ulang pekerjaan tersebut.
- Model serving sekarang masih jalur P2; artefak tuning/evaluasi Minggu 10 terpisah.
  Jangan menyalin model baru langsung ke lokasi serving tanpa pemeriksaan kompatibilitas.
- Target tetap `future_7d_mean_sbp`, memakai histori tujuh hari dan target rerata
  SBP tujuh hari berikutnya. Persetujuan target sebelumnya diasumsikan dalam tugas;
  simpan keputusan dosen/tim yang nyata, jangan mengarang bukti.
- Penelitian aktual membutuhkan data yang layak. Jika belum tersedia, lanjutkan
  pengembangan teknis dengan fixture sintetis berlabel jelas dan status pending.

## Koordinasi Aldi

Serahkan metadata kualitas dan kelayakan window kepada Nahesson. Sepakati metadata dan kebutuhan API bersama Hugo. Ruben memakai prosedur ETL/backup untuk pengujian terisolasi; Kasih memakai ringkasan kualitas yang aman untuk naskah.

## Aturan kerja untuk tugas ini

- Kerjakan hanya file pada bagian tanggung jawab sendiri. Nama file/folder baru
  adalah usulan; gunakan nama tes/output unik agar tidak bertabrakan.
- File bersama `App.jsx`, barrel `Pages.jsx`, `Common.jsx`, `Visuals.jsx`,
  `FilterBar.jsx`, `components/page-shared/Analysis.jsx`, API client dan CSS global
  dikoordinasikan Hugo. Anggota lain mengajukan kebutuhan melalui issue/PR.
- Jangan aktifkan `Dashboard.legacy.jsx` atau `OtherPages.jsx`. Jangan kembalikan
  implementasi seluruh halaman ke `Pages.jsx`.
- Jangan menimpa artefak model/laporan anggota lain. Data aktual, identitas,
  kredensial dan `.env` tetap privat; tidak masuk Git.
- Mulai dari `main` yang sudah berisi pemisahan halaman. Gunakan branch fitur pada
  bagian tugas sendiri; buat issue dan PR kecil dengan bukti tes/screenshot.
- Sinkronkan perubahan `main` sebelum PR, periksa diff dan selesaikan konflik
  bersama pemilik file. Minimal satu anggota lain mereview sebelum merge.
- Jangan push langsung ke `main`, force-push branch bersama, atau melakukan
  perubahan database/volume aktif tanpa persetujuan.
- Urutan integrasi utama: **Aldi > Nahesson > Hugo > Ruben > Kasih**. Infrastruktur,
  jurnal, tes dan komponen fitur dapat dimulai paralel menggunakan kontrak yang
  disepakati. Urutan ini bukan larangan mengerjakan tugas lebih awal.
- Sebelum paralel, sepakati jenis sumber, versi fitur, fingerprint training,
  manifest model, cakupan metrik, respons API dan alasan data/model belum tersedia.
  Batch inferensi yang bertambah tidak otomatis identik dengan batch training;
  kebijakan kompatibilitas harus jelas, bukan mengabaikan mismatch.

## Target checkpoint dan definisi selesai

| Waktu | Bukti yang dituju |
|---|---|
| Minggu 11 CP4 | Prototipe terintegrasi, visual hasil model, API dan draf Hasil; bedakan status sintetis/aktual dan keterbatasan yang belum selesai |
| Minggu 12 | Deployment, pengujian input baru dan uji 3-5 pengguna |
| Minggu 13 | Draf lengkap ke dosen dan tindak lanjut temuan |
| Minggu 14 | Freeze aplikasi, dokumentasi/README, revisi dan pemeriksaan similarity |
| Minggu 15 | Presentasi, demo, tanya jawab individu dan deliverable final |

Setiap anggota baru menyebut tugas selesai jika:

- [ ] Kontribusi DA dan DS dapat ditunjukkan dari implementasi/analisis yang nyata.
- [ ] Halaman React miliknya berfungsi dengan API; filter, grain, satuan, jumlah
      sampel, tooltip/keterangan dan interpretasi sesuai data.
- [ ] Loading, error dan empty state tersedia; tidak ada angka/grafik palsu.
- [ ] Tes terkait dan build yang diperlukan lulus; hasil dan kegagalan dicatat jujur.
- [ ] Screenshot, cara menjalankan, keterbatasan dan tautan bukti disertakan di PR.
- [ ] Bukti kontribusi masuk laporan mingguan dan materi jurnal yang relevan.

Gunakan akun sendiri, commit bermakna dan PR lintas DA/DS. Dokumen dosen meminta
minimal dua commit bermakna per anggota per minggu, minimal satu review per minggu
dan minimal enam PR merged per anggota sepanjang proyek yang mencakup DA dan DS.
Penuhi melalui pekerjaan nyata, bukan memecah perubahan kosong atau memalsukan riwayat.

## Referensi

- [Peta halaman aktif](ACTIVE_PAGE_SPLIT.md)
- [Tuning sintetis yang sudah dikerjakan](WEEK10_TUNING_REPORT.md)
- [Evaluasi sintetis yang sudah dikerjakan](WEEK10_EVALUATION_REPORT.md)
- [Runbook deployment](P2_DEPLOYMENT_RUNBOOK.md)
- `Tracking_Progress_Proyek_DA_DS.pdf`: timeline, kontribusi, laporan mingguan dan jurnal.
