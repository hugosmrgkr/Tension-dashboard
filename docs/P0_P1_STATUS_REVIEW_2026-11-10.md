# Review status P0/P1 — Toba Health Insight

Tanggal review: 10 November 2026  
Basis: ZIP `Tension-dashboard-main.zip` yang diberikan pengguna.  
Batas: pemeriksaan kode dan regression test pada data sintetis. Bukan persetujuan dosen, validasi klinis, atau verifikasi dataset penelitian aktual.

## Ringkasan

- Implementasi teknis P0/P1 sebagian besar sudah tersedia pada jalur aktif v2.
- P0-01 masih perlu verifikasi ekspor Google Forms aktual.
- P0-02, P0-04, P0-07, dan P1-08 memiliki pagar teknis tetapi keputusan/protokol penelitian masih pending.
- Nama menu aktif yang sebelumnya masih `Prediksi Hipertensi` telah diganti menjadi `Prediksi Tekanan Darah` agar konsisten dengan output regresi SBP numerik.
- Modul lama `backend/app/service.py`, `backend/app/data_utils.py`, `frontend/src/pages/OtherPages.jsx`, `frontend/src/pages/Dashboard.jsx`, `frontend/src/components/DataTable.jsx`, dan `frontend/src/components/Charts.jsx` masih memuat logika lama. Modul tersebut tidak dipakai oleh entrypoint aktif (`backend/app/main.py` dan `frontend/src/App.jsx` → `frontend/src/pages/Pages.jsx`). Jangan menghidupkan endpoint/halaman legacy untuk demo.

## Status P0

| ID | Status review | Pemeriksaan dan penjelasan | Yang masih diperlukan |
|---|---|---|---|
| P0-01 | SEBAGIAN | `survey_schema.py` mendefinisikan kontrak terpisah untuk profil (24 field) dan harian (28 field). `pipeline.py` menghubungkan berdasarkan `respondent_id`, memeriksa ID dan header. Fixture sintetis dua file dapat diproses dan regression test header/relasi lulus. | Uji dry-run dengan dua ekspor Google Forms aktual yang sudah disanitasi. Jika header berubah, buat revisi kontrak eksplisit; jangan menebak urutan kolom. |
| P0-02 | TEKNIS SELESAI; KEPUTUSAN PENDING | `BPSession` memiliki grain unik partisipan–tanggal–sesi. Empat bacaan mentah disimpan dan gate pasangan bacaan mencegah silang SBP/DBP; tes silang, parsial, kontradiksi dan ekstrem lulus. | Dosen/tim harus menetapkan minimum pasangan, pengulangan, serta cakupan hari. Gate saat ini hanya pagar teknis sementara, bukan protokol klinis. |
| P0-03 | SELESAI | Profil responden berada di `Participant`, perilaku harian di `DailyBehavior` dengan grain ID–tanggal, dan tekanan darah di `BPSession`. Tes memastikan join tidak menggandakan perilaku karena dua sesi. | Tidak ada perubahan kode yang diperlukan berdasarkan daftar ini. |
| P0-04 | SEBAGIAN / KEPUTUSAN PENDING | `sleep_hours` disimpan sebagai nilai numerik jam. Parsing `HH:MM` hanya diaktifkan untuk fixture sintetis; pecahan Excel ambigu tidak otomatis dikali 24. Data aktual belum ditafsirkan jika semantik jawaban belum jelas. | Cocokkan dengan teks pertanyaan dan ekspor asli: apakah durasi tidur, jam tidur/bangun, atau serial waktu spreadsheet. Setelah disetujui, dokumentasikan mapping dan uji aktual. |
| P0-05 | SELESAI | ID wajib dari sumber; harian yang ID-nya tidak cocok dengan profil diterima dikarantina. Tidak ada pembuatan ID responden otomatis per baris. | Koreksi ID hanya dari sumber berversi dan decision log. |
| P0-06 | SELESAI | Skema menggunakan `province` dan `city`; konsumsi asin, buah, sayur, dan kafein disimpan terpisah. Tidak ada kolom kecamatan atau satu pola makan buatan yang diwajibkan. | Validasi ejaan/normalisasi wilayah setelah ekspor aktual tersedia. |
| P0-07 | TEKNIS SELESAI; TARGET PENDING | Jalur aktif menggunakan target regresi `future_7d_mean_sbp`, keluaran mmHg, artefak baseline, dan `target_approved=false`. Menu aktif dan dokumentasi yang relevan diselaraskan menjadi `Prediksi Tekanan Darah`. | Persetujuan dosen atas target dan horizon 7 hari. Jangan menyebut baseline sebagai model final atau hasil penelitian aktual. |

## Status P1

| ID | Status review | Pemeriksaan dan penjelasan | Yang masih diperlukan |
|---|---|---|---|
| P1-01 | SELESAI | Skor stres diparse sebagai integer 1–5 atau label formulir; nilai lain menjadi missing + issue, bukan skala 0–10. | Aturan kategori tinggi/rendah hanya jika disepakati secara eksplisit. |
| P1-02 | SELESAI | Kategori merokok menerima teks panjang `Tidak berlaku karena saya tidak merokok`; kolom menyimpan kategori sumber. Nilai jumlah kosong tidak otomatis menjadi nol. | Pastikan satuan jumlah mengikuti pertanyaan formulir; jangan asumsikan batang rokok. |
| P1-03 | SELESAI | `analytics_v2.py` mengagregasi BP sesi ke ID–tanggal sebelum join perilaku. Statistik faktor harian menggunakan grain harian; baseline menggunakan rangkaian waktu. Tidak memakai `first` untuk seluruh variabel berubah. | Tidak ada perubahan kode yang diperlukan pada jalur aktif. |
| P1-04 | SELESAI SECARA TEKNIS | ETL dua sumber berjalan melalui CLI dengan dry-run sebagai default, laporan accepted/rejected/reason, hash prasyarat dan persetujuan eksplisit sebelum promosi. API web aktif read-only; tidak ada endpoint upload/CRUD. | Tetap lakukan review manual dan otorisasi sebelum memuat data aktual. Data aktual tidak boleh dipromosikan hanya karena dry-run lulus. |
| P1-05 | SELESAI | Tinggi dan berat disimpan sebagai data sumber; BMI diturunkan dari `weight_kg / (height_cm/100)^2`. Input tidak valid menjadi missing. | Tidak ada perubahan kode yang diperlukan berdasarkan daftar ini. |
| P1-06 | SELESAI PADA JALUR AKTIF | `Pages.jsx` dan `analytics_v2.py` memakai variabel sumber terpisah: asin, buah, sayur, kafein, stres 1–5, merokok, aktivitas, tidur, dan obat. Grafik menjelaskan ukuran sampel/missing serta tidak mengklaim sebab-akibat. | Validasi akhir setelah data aktual tersedia; hindari interpretasi kausal. |
| P1-07 | SELESAI PADA JALUR AKTIF | `bp_policy.py` menjadi gate pusat konsistensi pasangan BP. Halaman aktif menampilkan mmHg dan peringatan eksperimen, bukan kelas diagnosis hipertensi. | Jika klasifikasi analitik dibutuhkan nanti, sepakati satu rule set dan sumbernya terlebih dahulu. |
| P1-08 | TEKNIS SEBAGIAN SELESAI; REVIEW AKTUAL PENDING | `quality.py` melaporkan kelengkapan, missing, issue, duplikasi, konflik, tanggal mencurigakan, dan flag IQR. Raw tidak dihapus otomatis; konflik dikarantina. Gate menolak commit aktual bila issue/anomali belum direview. | Tetapkan reviewer, reason code, periode studi, aturan koreksi/eksklusi dan decision log untuk data aktual. IQR adalah flag deskriptif, bukan bukti kesalahan atau diagnosis. |

## Pengujian yang dijalankan saat review

| Pemeriksaan | Hasil | Catatan |
|---|---:|---|
| Seluruh `backend/tests` | **73 passed, 1 skipped** | Perintah: `PYTHONPATH=backend python -m pytest backend/tests -q -p no:cacheprovider -rs`. Satu skip adalah kontrak API v1 lama yang memang sudah dipensiunkan (`backend/tests/test_api.py`); tes API v2/CP3 tetap berjalan. |
| ETL sintetis `--dry-run --summary` | **Lulus** | 19/19 profil diterima; 570/570 catatan harian diterima; 1.140 sesi diturunkan dan valid. Dijalankan dengan `DATABASE_URL` PostgreSQL sengaja diarahkan ke host/port yang tidak tersedia dan tanpa driver psycopg; sukses membuktikan dry-run tidak membuat engine/koneksi DB. Tidak ada perubahan database. |
| Frontend unit test/build | **BELUM DIVERIFIKASI** | `npm ci --no-audit --no-fund` timeout saat mengambil dependency. Karena `node_modules` tidak tersedia, `npm test`, `npm run build`, dan browser test tidak dijalankan pada review ini. |
| Data aktual Google Forms | **BELUM DIVERIFIKASI** | ZIP hanya berisi fixture sintetis; tidak ada ekspor aktual tersanitasi untuk dry-run. |

Lingkungan pengujian backend: Python 3.13.5, pandas 2.2.3, SQLAlchemy 2.0.50, FastAPI 0.128.2 dan scikit-learn 1.8.0. Hasil ini adalah pengujian baru pada lingkungan pemeriksaan Linux saat ini, bukan pengujian Windows/PostgreSQL baru. Artefak Windows/PostgreSQL yang tercantum di `P0_P1_FINAL_AUDIT.md` adalah bukti historis yang tersimpan dalam ZIP, bukan hasil yang dijalankan ulang pada sesi ini.

### Perbaikan tambahan dalam review 10 November

- `etl/import_data.py`: impor konfigurasi database dan modul promosi ETL dipindahkan ke cabang `--commit`. Dry-run tidak lagi memerlukan driver PostgreSQL dan tidak membuat engine.
- `backend/app/pipeline.py`: model ORM dimuat secara lokal hanya ketika fungsi pemuatan warehouse dipanggil. Validasi/parsing file tidak lagi membuat engine database sebagai efek samping impor.
- `backend/tests/test_p0_p1_audit.py`: pengujian aturan `.gitignore` memakai repository sementara, sehingga tetap bisa dijalankan dari ZIP yang tidak membawa metadata `.git`.

Perbaikan tambahan ini tidak mengubah target penelitian, protokol BP, pemetaan tidur aktual, isi fixture, artefak model, atau database.

## Langkah berikutnya sebelum memakai data penelitian

1. Dapatkan ekspor profil dan harian Google Forms aktual yang sudah disanitasi, tanpa nama/kontak atau identitas langsung.
2. Jalankan ETL `--dry-run --summary`; cocokkan header, jumlah ID, jumlah ID–tanggal, sesi, missing, duplikasi, tanggal, dan issue.
3. Minta keputusan dosen/tim tentang protokol BP, makna tidur, target/horizon regresi, inklusi, dan aturan review anomali.
4. Simpan hasil review dan keputusan dalam dokumen berversi; jangan commit ke warehouse aktif sebelum persetujuan eksplisit dan hash target diperiksa.

**Kesimpulan:** banyak masalah P0/P1 sudah diperbaiki secara teknis pada runtime aktif. Namun, integrasi dengan formulir aktual dan keputusan ilmiah belum dapat dinyatakan selesai dari ZIP sintetis ini saja.
