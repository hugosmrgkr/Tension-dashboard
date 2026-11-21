# Tugas Hugo untuk CP4 sampai final

Project: **Toba Health Insight**. Dokumen ini khusus tugas **Hugo** dan mengikuti
pembagian terakhir: Ruben menangani deployment serta Dashboard/Tren; Nahesson
menangani model serta Evaluasi/Faktor Risiko. Semua delapan halaman sudah dibagi.

Checklist mencatat rencana dan hasil yang sudah diuji; status sintetis dan aktual
dibedakan pada bagian progres di bawah. Dokumen ini tidak membuat
branch, commit atau push. Jangan mengulang pekerjaan sintetis yang sudah selesai.

## Tugas utama
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
- [x] Tampilkan riwayat SBP/DBP, hasil estimasi **rerata SBP** tujuh hari berikutnya,
      rentang tanggal, pembanding naif, asal data dan versi model pada React.
- [x] Bedakan observasi historis dari estimasi target dengan jelas. Jangan
      menggambar tujuh nilai prediksi harian dari satu output rerata.
- [x] Pertahankan pembatalan request, validasi ID/tanggal, dan loading/error/empty
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

## Koordinasi Hugo

Aldi menyediakan kontrak dataset; Nahesson menyediakan paket model; Ruben menguji deployment; Kasih memakai bukti hasil. Hugo menyatukan kontrak API/routing tanpa mengambil alih pekerjaan fitur mereka.

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

### Progres Hugo — 17 November 2026

Empat tahap teknis telah dikerjakan bertahap setelah konfirmasi Hugo. Ini bukan
klaim seluruh tugas final atau aktivasi aktual selesai. Checklist yang belum
dicentang tetap memerlukan dependensi/review; beberapa sudah diterapkan terbatas
untuk adapter sintetis seperti dijelaskan berikut.

| Tahap | Hasil | Status/batas |
|---|---|---|
| 1 | [Draf kontrak](MODEL_INTEGRATION_CONTRACT.md) | Selesai disusun; review Aldi/Nahesson pending |
| 2 | [Registry dan API](HUGO_STAGE2_REPORT.md) | Adapter P2 sintetis terverifikasi; menolak hash/fitur/batch yang tidak cocok; bukan loader rilis final |
| 3 | [Prediksi React](HUGO_STAGE3_REPORT.md) | Grafik histori SBP/DBP, estimasi rerata vs naif, origin, provenance dan perlindungan respons usang |
| 4 | [Acceptance terisolasi](HUGO_STAGE4_REPORT.md) | SQLite 232 passed + 1 skipped; PostgreSQL 232 passed + 1 skipped; frontend 22 passed; browser 21 passed; build berhasil |

Pemisahan sumber telah diterapkan secara konservatif: sintetis berlabel, sumber
aktual tetap diblokir; belum akses aktual end-to-end atau paket rilis Nahesson.
Review kontrak, kebijakan batch baru, deployment, uji pengguna dan kontribusi
commit/PR nyata tetap menjadi pekerjaan lanjutan. Tidak membuat commit/push otomatis.

- [Peta halaman aktif](ACTIVE_PAGE_SPLIT.md)
- [Tuning sintetis yang sudah dikerjakan](WEEK10_TUNING_REPORT.md)
- [Evaluasi sintetis yang sudah dikerjakan](WEEK10_EVALUATION_REPORT.md)
- [Runbook deployment](P2_DEPLOYMENT_RUNBOOK.md)
- `Tracking_Progress_Proyek_DA_DS.pdf`: timeline, kontribusi, laporan mingguan dan jurnal.
