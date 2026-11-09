# Progres terhadap deskripsi proyek IT Del — M6–M8 (bukan penilaian dosen)

Sumber: `Deskripsi_Proyek_DA_DS.pdf` tabel timeline halaman 6; `Daftar yang harus diperbaiki.pdf` P0–P2; `Panduan_Utama_Proyek_Tekanan_Darah_DALIS_DASI(1).pdf`.

| Luaran jadwal | Implementasi yang tersedia | Batasan |
| --- | --- | --- |
| M6 Dashboard v1 | Delapan halaman, sidebar, 4 KPI, deret waktu Pagi/Malam, box plot, heatmap, filter global, API PostgreSQL | Build React perlu diverifikasi di Docker pengguna jika npm registry tidak tersedia pada lingkungan review. |
| M6 Feature engineering & split | Feature `past_7d_*`, target `future_7d_mean_sbp` sintetis, pembagian responden tanpa overlap | Target masih **usulan**, belum disetujui dosen. |
| M7 Baseline + pembanding | Baseline mean 7-hari terakhir dan Linear Regression; metrik MAE, RMSE, R² awal dihitung, notebook & model artefak tersedia | Tidak ada tuning atau tiga model final. |
| M7 Analisis mendalam & filter dasar | Perbandingan sesi, hubungan gaya hidup, filter tanggal dan profil, trend per ID | Visualisasi advance interaktif final M9–M10 masih perlu evaluasi. |
| M8 Dashboard v1 + warehouse | 3 dimensi (`participant`, `date`, `session`) dan 2 fakta (`bp_session`, `daily_behavior`), seed dua dataset | Audit aktual, deployment publik, RBAC belum selesai. |
| M8 Laporan baseline dan rencana eksperimen | `models/baseline_metrics.json`, notebook, dokumentasi; rencana tambah model lanjutan setelah data readiness | Metrik adalah **data sintetis** dan tidak mengukur generalisasi pasien. |

## P0 yang diperbaiki

- P0-01: kontrak dua formulir, ETL menghubungkan melalui ID.
- P0-02: fakta per sesi (Pagi/Malam) menyimpan pembacaan 1 dan 2.
- P0-03: faktor tidur/stres/merokok/konsumsi di fakta harian, bukan dimensi peserta.
- P0-04: kolom tidur simulasi HH:MM menjadi jam desimal dengan asumsi terdokumentasi; aktual tetap menunggu klarifikasi.
- P0-05: ID wajib dan ID tak cocok ditahan.
- P0-06: wilayah provinsi/kabupaten; frekuensi asin, buah, sayur, kafein disimpan terpisah.
- P0-07: klasifikasi dummy diganti baseline **regresi numerik eksplisit** sesuai target **usulan**; tidak diklaim model klinis.

## Keputusan dosen yang masih dibutuhkan

1. Persetujuan target rata-rata sistolik 7 hari setelah tanggal t dan aturan minimum jumlah pengukuran valid.
2. Arti `jam tidur` di data aktual: waktu tidur/bangun atau durasi.
3. Kelayakan data primer dan syarat minimal 500 baris (catatan berulang dari responden yang sama tidak sama dengan individu berbeda).
4. Kriteria inklusi 15–64 / 18–64, izin pengumpulan, akses dan privasi.
5. Alternatif bila data primer tidak cukup untuk eksperimen tiga model yang reliabel.

## Penafsiran hasil baseline

Metrik adalah fungsi dari dataset sintetis yang disertakan, bukan angka contoh yang ditulis secara manual. Split train/test berdasarkan ID responden mencegah orang yang sama muncul di dua partisi. Target menggunakan tujuh hari setelah t dan seluruh fitur menggunakan data pada/sebelum t. Karena hanya ada 19 ID sintetis dan pengamatan 30 hari, evaluasi **tidak mendukung klaim kemampuan model di masyarakat nyata**. Baseline rata-rata 7 hari merupakan pembanding sederhana yang dapat diuji ulang.
