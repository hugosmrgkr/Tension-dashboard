# Tugas Nahesson untuk CP4 sampai final

Project: **Toba Health Insight**. Dokumen ini khusus tugas **Nahesson** dan mengikuti
pembagian terakhir: Ruben menangani deployment serta Dashboard/Tren; Nahesson
menangani model serta Evaluasi/Faktor Risiko. Semua delapan halaman sudah dibagi.

Checklist adalah rencana kerja, **bukan klaim selesai**. Dokumen ini tidak membuat
branch, commit atau push. Jangan mengulang pekerjaan sintetis yang sudah selesai.

## Tugas utama
**Branch:** `feat/validated-model-release`  
**Halaman:** Evaluasi Model dan Analisis Faktor Risiko  
**Tujuan:** memperoleh evaluasi model yang sah untuk data yang layak, paket rilis
yang dapat direproduksi, dan visual asosiasi yang tidak menyesatkan.

### Checklist pengerjaan

- [ ] Gunakan hasil readiness Aldi untuk menentukan apakah data cukup untuk
      training, tuning dan test baru. Jangan memaksakan eksperimen jika tidak layak.
- [ ] Susun validasi responden/waktu dengan purge target dan preprocessing fit-only.
      Jika kalender belum cukup, catat batasnya; jangan mengklaim GroupKFold biasa
      sebagai validasi forecasting kronologis penuh.
- [ ] Pertahankan target dan fitur sesuai keputusan terdokumentasi. Jangan
      mengimputasi target atau memakai informasi yang belum tersedia saat prediksi.
- [ ] Jalankan eksperimen aktual hanya ketika layak; bandingkan algoritma dengan
      baseline naif. Gunakan validasi untuk memilih, bukan hasil test.
- [ ] Simpan rilis terpisah beserta manifest, sumber/fingerprint training, urutan
      fitur, versi dependency, metrik, horizon dan model card. Sepakati format dengan Hugo.
- [ ] Jangan menimpa model/hasil CP3, P2 dan Minggu 10; itu bukti eksperimen sintetis.
- [ ] Lengkapi Evaluasi Model agar menampilkan metrik, actual-vs-predicted, residual,
      error dan batas interpretasi dari rilis yang ditampilkan API.
- [ ] Lengkapi Analisis Faktor Risiko untuk tidur, stres, aktivitas, makanan asin,
      buah/sayur, kafein, merokok dan kepatuhan obat sesuai jawaban formulir.
- [ ] Tampilkan grain, jumlah sampel, missing dan kelompok kecil dengan benar.
      Hubungan adalah asosiasi, bukan sebab-akibat atau diagnosis.

### File milik Nahesson

- `frontend/src/pages/EvaluasiModel.jsx`, `AnalisisFaktorRisiko.jsx`
- `frontend/src/components/model-evaluation/`, `risk-analysis/` — baru jika diperlukan
- `backend/app/actual_experiment.py`, `risk_analysis.py` — baru jika diperlukan;
  fungsi analitik khusus, dengan pemasangan route melalui Hugo
- `etl/train_actual_model.py` dan notebook aktual baru bernama unik
- `models/releases/`, `reports/actual_model/` — baru; tanpa data privat di Git
- Tes khusus split temporal, preprocessing, artefak dan agregasi faktor risiko

**DA:** asosiasi dan agregasi faktor risiko yang benar. **DS:** desain eksperimen,
validasi, evaluasi dan rilis model.

**Hasil wajib:** protokol evaluasi, notebook, hasil yang dapat direproduksi,
model card/manifest, visual React dan catatan kelayakan. Bila data belum memadai,
hasil wajibnya adalah laporan keterbatasan serta implementasi yang menolak data tak layak.

**Dependensi:** kualitas/kalender data dari Aldi dan kontrak serving dengan Hugo.
Jangan memilih algoritma hanya karena lebih kompleks atau memaksakan skor lebih tinggi.

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

## Koordinasi Nahesson

Gunakan hasil readiness Aldi; sepakati manifest dan route hasil model dengan Hugo. Ruben menguji paket rilis pada staging. Serahkan angka, grafik dan batas evaluasi terverifikasi kepada Kasih; jangan mengedit naskah/output anggota lain bersamaan.

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
