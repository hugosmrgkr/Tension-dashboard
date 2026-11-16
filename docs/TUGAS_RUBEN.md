# Tugas Ruben untuk CP4 sampai final

Project: **Toba Health Insight**. Dokumen ini khusus tugas **Ruben** dan mengikuti
pembagian terakhir: Ruben menangani deployment serta Dashboard/Tren; Nahesson
menangani model serta Evaluasi/Faktor Risiko. Semua delapan halaman sudah dibagi.

Checklist adalah rencana kerja, **bukan klaim selesai**. Dokumen ini tidak membuat
branch, commit atau push. Jangan mengulang pekerjaan sintetis yang sudah selesai.

## Tugas utama
**Branch:** `feat/deployment-and-recovery`  
**Halaman:** Dashboard dan Tren Tekanan Darah  
**Tujuan:** aplikasi dapat dijalankan dan dipulihkan secara teruji; KPI dan grafik
tetap konsisten dengan sumber warehouse setelah deployment.

### Checklist pengerjaan

- [ ] Uji konfigurasi staging yang sudah ada; catat hasil nyata sebelum mengubahnya.
      Gunakan lingkungan terisolasi, jangan reset database/volume utama.
- [ ] Buktikan HTTPS, autentikasi, pembatasan port DB, pengelolaan secret, restart,
      persistensi, backup dan restore. Perbaikan middleware dikoordinasikan dengan Hugo.
- [ ] Uji restore pada database sementara dan verifikasi jumlah data/fingerprint;
      pastikan target berisi data tidak tertimpa tanpa prosedur eksplisit.
- [ ] Uji alur CSV sintetis ke ETL, PostgreSQL, API, React dan prediksi secara
      terisolasi. Uji input baru, artefak tidak cocok dan riwayat kurang.
- [ ] Periksa KPI Dashboard terhadap warehouse: responden aktif, catatan harian,
      sesi valid dan rerata SBP mengikuti definisi/grain yang sudah disepakati.
- [ ] Lengkapi visual cakupan/kontinuitas pengamatan dan kesegaran dataset dari API.
      Bedakan tanggal pengamatan terbaru dari waktu impor; jangan menyebutnya real-time
      jika data hanya diperbarui lewat ETL manual.
- [ ] Periksa Tren: panel **Pagi** dan **Malam**, masing-masing berisi garis
      **SBP dan DBP**; pertahankan tooltip, jumlah sampel, filter klik dan detail bacaan.
- [ ] Uji delapan halaman di desktop/ponsel, termasuk filter, empty/error state,
      ekspor dan konsistensi nilai setelah restart/restore.
- [ ] Catat URL saat tersedia, lingkungan, perintah menjalankan dan hasil uji pada
      runbook. Jangan mengklaim deployment publik selesai hanya dari localhost.

### File milik Ruben

- `frontend/src/pages/Dashboard.jsx`, `TrenTekananDarah.jsx`
- `frontend/src/components/data-coverage/` — baru jika diperlukan
- `compose*.yaml`, Dockerfile backend/frontend dan konfigurasi nginx
- `deploy/`, skrip startup/backup/restore pada `scripts/`
- `tests/e2e/`, `reports/deployment/` — baru jika diperlukan
- `docs/P2_DEPLOYMENT_RUNBOOK.md`

**DA:** verifikasi warehouse, KPI, filter, ekspor dan visual tren. **DS:** pemeriksaan
artefak/inferensi dan input baru di lingkungan deployment, tanpa mengubah algoritma.

**Hasil wajib:** bukti pengujian staging dan restore, runbook, screenshot Dashboard/Tren,
hasil tes end-to-end, daftar kegagalan yang masih tersisa dan URL jika benar tersedia.

**Dependensi:** bisa mulai staging dengan data sintetis sekarang. Uji penerimaan
rilis aktual mengikuti integrasi Hugo serta data/model Aldi dan Nahesson.

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

## Koordinasi Ruben

Koordinasikan sumber/uji warehouse dengan Aldi, rilis model dengan Nahesson, endpoint/otorisasi dengan Hugo, serta rilis stabil dan temuan pengguna dengan Kasih. Perubahan middleware/API bersama melalui Hugo.

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
