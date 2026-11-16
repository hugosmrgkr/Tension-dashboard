# Tugas Kasih untuk CP4 sampai final

Project: **Toba Health Insight**. Dokumen ini khusus tugas **Kasih** dan mengikuti
pembagian terakhir: Ruben menangani deployment serta Dashboard/Tren; Nahesson
menangani model serta Evaluasi/Faktor Risiko. Semua delapan halaman sudah dibagi.

Checklist adalah rencana kerja, **bukan klaim selesai**. Dokumen ini tidak membuat
branch, commit atau push. Jangan mengulang pekerjaan sintetis yang sudah selesai.

## Tugas utama
**Branch:** `feat/research-evidence-and-usability`  
**Halaman:** Laporan & Ringkasan  
**Tujuan:** insight dashboard, hasil model dan naskah memiliki angka serta batas
interpretasi yang sama, didukung uji pengguna dan bukti kontribusi.

### Checklist pengerjaan

- [ ] Tentukan jurnal target bersama kelompok/dosen; simpan tautan verifikasi,
      template resmi, scope, panduan penulis dan informasi yang benar-benar diperiksa.
- [ ] Susun Pendahuluan, Metode, desain eksperimen dan draf Hasil; lanjutkan
      Pembahasan serta bagian final menurut timeline. Semua anggota menyumbang
      materi fiturnya, bukan menyerahkan seluruh penulisan pada Kasih.
- [ ] Buat skrip ekspor tabel/gambar dari hasil terverifikasi. Uji kesamaan angka,
      satuan, jumlah sampel, sumber dan versi model dengan artefak/API.
- [ ] Lengkapi Laporan & Ringkasan: insight dinamis, perbandingan yang sah,
      ukuran sampel, batas analisis dan penelusuran ke halaman terkait.
- [ ] Siapkan ekspor ringkasan yang aman jika diperlukan untuk laporan/jurnal,
      tanpa membuka data identitas atau metrik yang dibuat manual.
- [ ] Susun skenario uji 3-5 pengguna, lakukan ketika rilis stabil tersedia,
      catat temuan nyata dan buat issue perbaikan untuk pemilik halaman.
- [ ] Kompilasikan laporan mingguan dari bukti setiap anggota: target/capaian,
      commit/PR/issue, jam kerja faktual, progres jurnal dan rencana berikutnya.
- [ ] Lengkapi checklist CP4/final, petunjuk pengguna, materi demo, deklarasi data/AI
      dan bukti similarity sesuai ketentuan. Jangan mengarang pengujian, tanggal,
      referensi, kontribusi atau persetujuan.

### File milik Kasih

- `frontend/src/pages/LaporanRingkasan.jsx`
- `frontend/src/components/research-summary/` — baru jika diperlukan
- `etl/export_publication_evidence.py` dan tes konsistensi angka — baru
- `paper/`, `reports/weekly/`, `reports/usability/` — baru
- Checklist/laporan CP4 dan final baru; `README.md`, panduan pengguna

**DA:** storytelling dan evaluasi kegunaan. **DS:** kode ekspor/pemeriksaan bukti
model, interpretasi metrik dan konsistensi angka naskah dengan hasil eksperimen.

**Hasil wajib:** halaman ringkasan, skrip/bukti konsistensi hasil, draf jurnal,
laporan usability, laporan mingguan dan paket final. Simulasi harus tetap disebut
simulasi di naskah maupun dashboard.

**Dependensi:** jurnal/struktur laporan dapat dimulai sekarang. Hasil final memakai
artefak Nahesson, integrasi Hugo dan rilis stabil Ruben; data dijelaskan bersama Aldi.

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

## Koordinasi Kasih

Minta materi data dari Aldi, hasil model dari Nahesson, penjelasan integrasi dari Hugo dan bukti deployment dari Ruben. Semua anggota menyumbang materi serta bukti fiturnya; Kasih mengompilasi, bukan mengarang atau mengerjakan semua kontribusi mereka.

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
