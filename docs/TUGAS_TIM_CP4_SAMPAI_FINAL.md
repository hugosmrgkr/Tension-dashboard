# Pembagian pekerjaan Toba Health Insight

Panduan kerja Hugo, Aldi, Ruben, Nahesson dan Kasih dari CP4 sampai final.
Ruben menangani deployment dan halaman Dashboard/Tren; Nahesson menangani model
dan halaman Evaluasi/Faktor Risiko. Pembagian ini sudah mengikuti pertukaran tugas terakhir.

Checklist di bawah adalah **pekerjaan yang harus dikerjakan**, bukan klaim selesai.
Nama branch merupakan rencana; dokumen ini tidak membuat branch, commit atau push.

## Ringkasan pemilik

| Anggota | Branch fitur | Halaman React | Fokus |
|---|---|---|---|
| Hugo | `feat/source-aware-model-integration` | Prediksi Tekanan Darah | Integrasi sumber, otorisasi dan model ke aplikasi |
| Aldi | `feat/actual-data-readiness` | Kelola Data dan Data Partisipan | Kesiapan data aktual dan ETL |
| Ruben | `feat/deployment-and-recovery` | Dashboard dan Tren Tekanan Darah | Deployment, pemulihan dan konsistensi visual |
| Nahesson | `feat/validated-model-release` | Evaluasi Model dan Analisis Faktor Risiko | Validasi, rilis model dan interpretasi asosiasi |
| Kasih | `feat/research-evidence-and-usability` | Laporan & Ringkasan | Storytelling, jurnal, bukti penelitian dan usability |

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

## 1 Hugo

**Branch:** `feat/source-aware-model-integration`  
**Halaman:** Prediksi Tekanan Darah  
**Tujuan:** pengguna memperoleh hasil prediksi dari model dan sumber yang sesuai,
atau penjelasan jelas mengapa prediksi belum tersedia.

### Checklist pengerjaan

- [ ] Sepakati kontrak metadata dataset dan artefak dengan Aldi/Nahesson sebelum
      mengubah API: jenis sumber, versi fitur, fingerprint training, versi model,
      horizon, cakupan metrik dan status kelayakan.
- [ ] Siapkan pemilihan/pemuatan rilis model terverifikasi, termasuk penolakan
      artefak rusak dan kontrak fitur yang tidak cocok. Pertahankan hash integrity.
- [ ] Bedakan sumber sintetis dan aktual, serta data training dan data inferensi.
      Jangan hanya mengganti label sintetis menjadi aktual.
- [ ] Lengkapi otorisasi akses aktual melalui API dan React; pembatasan sumber
      aktual tidak boleh dihapus begitu saja agar dashboard terlihat berisi data.
- [ ] Integrasikan rilis dari Nahesson ke endpoint prediksi/evaluasi tanpa merusak
      kompatibilitas atau eksperimen historis.
- [ ] Tampilkan riwayat SBP/DBP, hasil estimasi **rerata SBP** tujuh hari berikutnya,
      rentang tanggal, pembanding naif, asal data dan versi model pada React.
- [ ] Bedakan observasi historis dari estimasi target dengan jelas. Jangan
      menggambar tujuh nilai prediksi harian dari satu output rerata.
- [ ] Pertahankan pembatalan request, validasi ID/tanggal, dan loading/error/empty
      state. Tampilkan kondisi riwayat kurang atau model belum tersedia tanpa angka palsu.
- [ ] Integrasikan endpoint/perubahan agregasi yang diminta anggota lain melalui
      PR terkoordinasi; jangan membiarkan beberapa orang menyunting `main.py` bersamaan.

### File milik Hugo

- `frontend/src/pages/PrediksiTekananDarah.jsx`
- `frontend/src/components/prediction/` — baru jika diperlukan
- `frontend/src/App.jsx`, `frontend/src/lib/api.js`
- `backend/app/main.py`, `analytics_v2.py`, `security.py`, `model_service.py`
- `backend/app/model_registry.py` — baru jika diperlukan
- Tes khusus API/React integrasi dengan nama file unik, misalnya
  `backend/tests/test_release_integration.py`.

**DA:** konsistensi sumber, riwayat dan filter. **DS:** paritas fitur training/inferensi,
integritas artefak dan penggunaan model yang benar.

**Hasil wajib:** alur API ke React yang diuji; contoh prediksi dan kegagalan yang
ditangani; screenshot halaman; catatan kontrak dan keputusan akses.

**Dependensi:** kontrak dataset Aldi dan paket rilis Nahesson. Bisa mulai dari model
sintetis yang sudah ada; aktivasi aktual menunggu data/model/otorisasi siap.

## 2 Aldi

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

## 3 Ruben

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

## 4 Nahesson

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

## 5 Kasih

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

## File bersama dan pencegahan konflik

| Area | Pemilik koordinasi | Aturan |
|---|---|---|
| Routing, `App.jsx`, barrel `Pages.jsx`, API client | Hugo | Anggota lain mengajukan kebutuhan; jangan mengedit bersamaan |
| `Common.jsx`, `Visuals.jsx`, `FilterBar.jsx`, `components/page-shared/Analysis.jsx`, CSS global | Hugo | Dahulukan komponen khusus di folder fitur; perubahan bersama melalui PR terkoordinasi |
| Kontrak ETL, profil dan fakta warehouse | Aldi | Nahesson/Hugo mengonsumsi kontrak; perubahan harus disepakati sebelum merge |
| Manifest dan isi paket rilis model | Nahesson | Hugo menangani loader/serving; sepakati schema sebelum implementasi paralel |
| Compose, Dockerfile, nginx dan deployment | Ruben | Uji terisolasi; tidak mengubah DB/volume aktif tanpa persetujuan |
| README, naskah, laporan mingguan dan paket final | Kasih | Semua anggota memberikan isi/bukti dari fiturnya |

`Dashboard.legacy.jsx` dan `OtherPages.jsx` tidak aktif: jangan dihidupkan kembali.
Jangan mengembalikan implementasi delapan halaman ke `Pages.jsx`.

Setiap anggota memakai nama tes/output yang unik pada area fiturnya. Jangan
menjalankan skrip yang menimpa artefak anggota lain. Nama folder/file baru di panduan
adalah usulan, bukan berkas yang sudah diimplementasikan.

## Kontrak yang disepakati sebelum kerja paralel

- [ ] Jenis sumber dan metadata dataset, versi fitur, tanggal pengamatan/impor serta
      status kualitas/kelayakan.
- [ ] Struktur manifest rilis: versi model, target/horizon, fitur berurutan,
      fingerprint training, metrik dan scope evaluasi, hash artefak.
- [ ] Bentuk respons API, status akses serta alasan model/data belum tersedia.
- [ ] Aturan perubahan batch: data inferensi yang bertambah tidak otomatis sama
      dengan batch training. Tampilkan provenance dan tetapkan kebijakan kompatibilitas;
      jangan memaksa fingerprint selalu identik atau mengabaikan mismatch diam-diam.
- [ ] Lokasi output, pemilik file dan langkah pembuktian fitur selesai.

## Urutan kerja dan merge

1. Semua anggota mulai dari `main` yang sudah memuat pemisahan halaman dan cek
   working tree masing-masing. Jangan menganggap file legacy sebagai halaman aktif.
2. Sepakati kontrak di atas dan buat issue ber-assignee, label serta milestone.
3. Kerjakan PR kecil: kontrak/tes, implementasi, kemudian bukti pengujian. Tidak
   perlu menunggu satu fitur besar lengkap untuk mengirim satu PR.
4. Urutan integrasi utama: **Aldi > Nahesson > Hugo > Ruben > Kasih**. Ini urutan
   dependensi hasil akhir, bukan larangan bekerja paralel.
5. Ruben bisa menguji staging sintetis sejak awal. Kasih bisa mulai jurnal, skrip
   bukti dan rancangan usability. Semua anggota bisa mengerjakan komponen React
   dengan kontrak/fixture sintetis yang disepakati, bukan metrik dummy produksi.
6. Sebelum PR: sinkronkan `main`, periksa diff, jalankan tes terkait dan frontend
   build bila mengubah React. Selesaikan konflik bersama pemilik file.
7. Minimal satu anggota lain mereview sebelum merge. Jangan push langsung ke `main`
   menurut ketentuan dosen; jangan force-push ke branch bersama.

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

## Referensi proyek

- [Peta pemisahan halaman aktif](ACTIVE_PAGE_SPLIT.md)
- [Laporan tuning Minggu 10](WEEK10_TUNING_REPORT.md)
- [Evaluasi dan analisis error Minggu 10](WEEK10_EVALUATION_REPORT.md)
- [Runbook deployment yang perlu dibuktikan](P2_DEPLOYMENT_RUNBOOK.md)
- Ketentuan dosen: `Tracking_Progress_Proyek_DA_DS.pdf`, khususnya timeline,
  kontribusi, laporan mingguan dan naskah jurnal.
