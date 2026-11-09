# Panduan cepat dashboard Toba Health Insight (Checkpoint M6–M8)

> **DATA SINTETIS / SIMULASI** — semua angka adalah data contoh untuk pengujian sistem, bukan kesimpulan kesehatan masyarakat atau diagnosis.

## Mulai dari mana?

1. **Dashboard** — cek empat kartu: *Responden aktif* (jumlah ID unik), *Catatan harian valid* (ID × tanggal), *Sesi valid* (pagi atau malam), serta *Rata-rata sistolik* (mmHg). Jangan menyamakan 1.140 sesi dengan 1.140 orang.
2. **Gunakan Filter Global** pada bagian atas halaman bila ingin memilih rentang tanggal, wilayah, jenis kelamin, kelompok usia, sesi, atau pekerjaan. Klik **Reset filter** untuk kembali ke semua data.
3. **Lihat Tren Tekanan Darah** — dua garis berbeda warna mewakili pengukuran *Pagi* dan *Malam*. Arahkan kursor untuk melihat tanggal, rata-rata, dan banyaknya sesi. Ada tabel bacaan 1 dan 2 untuk pemeriksaan data.
4. **Buka Data Partisipan** — cari ID pseudonim. `BMI` dihitung dari tinggi dan berat, bukan jawaban langsung.
5. **Buka Analisis Faktor Risiko** — temukan sebaran tidur, stres 1–5, aktivitas, konsumsi asin, buah, sayur dan kafein. Hasil adalah **asosiasi deskriptif**, bukan bukti sebab-akibat.
6. **Buka Prediksi Hipertensi** — halaman ini *bukan alat prediksi diagnosis*. Pilih ID simulasi lalu klik **Hitung perkiraan baseline** untuk memperkirakan rata-rata **sistolik tujuh hari berikutnya** dengan rata-rata tujuh hari terakhir.
7. **Buka Evaluasi Model** — perbandingan sederhana metode *Naive 7-day mean* dan *Linear Regression* menggunakan MAE, RMSE dan R² hasil perhitungan aktual pada dataset sintetis. Nilai yang lebih baik pada data sintetis belum berarti model akan baik pada manusia nyata.
8. **Buka Laporan & Ringkasan** — baca lima ringkasan otomatis dari data yang terfilter. Halaman **Kelola Data** memperlihatkan sumber, peringatan kualitas, dan ekspor CSV tanpa nama.

## Arti angka pada tampilan awal

| Istilah | Arti pada dataset contoh |
| --- | --- |
| 19 responden | Ada 19 ID sintetis, bukan 19 responden penelitian aktual. |
| 570 catatan harian | Satu ID dapat memiliki 30 tanggal pengukuran. |
| 1.140 sesi | Dua sesi (pagi/malam) per catatan harian, sebelum filter diterapkan. |
| SBP | Sistolik, tekanan darah angka atas, mmHg. |
| DBP | Diastolik, tekanan darah angka bawah, mmHg. |
| `n` pada tooltip | Banyak sesi atau catatan valid, bukan jumlah penduduk. |
| Baseline | Model pembanding paling sederhana: rerata SBP tujuh hari terakhir. |
| MAE / RMSE | Ukuran kesalahan prediksi dalam mmHg; lebih kecil umumnya lebih baik. |
| R² | Ukuran kecocokan model pada data uji, perlu dilihat bersama MAE/RMSE. |

## Data dan pemrosesan

- **Form Awal:** satu profil per ID, mencatat demografi, riwayat, berat/tinggi, aktivitas umum; nama tidak ikut ditampilkan di dashboard.
- **Form Harian:** satu baris per ID × tanggal, menyimpan pagi dan malam, masing-masing dua pasang SBP/DBP, serta kebiasaan harian.
- **Warehouse:** tiga tabel dimensi (responden, tanggal, sesi) dan dua tabel fakta (tekanan darah per sesi, perilaku per hari). Kolom harian tidak digandakan saat menghitung analisis kebiasaan.
- **Workbook gabungan:** `data/Dataset_Sintetis_Tekanan_Darah_REFERENSI.xlsx` memuat sheet `Data_Responden`, `Data_Harian`, dan `Petunjuk`. Sumber otomatis Docker **dua CSV** di `data/sample/`; workbook digunakan sebagai referensi format, bukan sumber tambahan yang dihitung dua kali.
- **Asumsi tidur:** nilai `06:31` pada CSV **sintetis** ditafsirkan 6 jam 31 menit. Jangan menerapkan asumsi ini ke data asli sebelum definisinya dipastikan.

## Jika ada yang terlihat kosong

1. Klik **Reset filter**, lalu muat ulang halaman.
2. Periksa `http://localhost:8080/api/meta` (sumber dan jumlah data), lalu `http://localhost:8080/api/analytics`.
3. Jalankan `docker compose ps` dan pastikan frontend/backend/db `Up` serta db `healthy`.
4. Jika perlu, `docker compose logs --tail=100 backend frontend`. Jangan gunakan `docker compose down -v`: tindakan itu menghapus volume PostgreSQL.

## Batas pekerjaan pada M6–M8

Dashboard v1, warehouse, ETL, fitur historis, dan eksperimen baseline + satu pembanding dapat didemonstrasikan. Masih diperlukan persetujuan target model dari dosen, audit dataset aktual, tiga algoritma dan tuning, interaksi visual advance M9–M10, integrasi model akhir, privasi untuk penggunaan data nyata, serta deployment publik. Hasil eksperimen dan insight saat ini **tidak boleh dinyatakan sebagai hasil penelitian pada responden aktual**.
