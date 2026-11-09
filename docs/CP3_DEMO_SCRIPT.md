# CP3 Demo Script - 8 menit (fleksibel 5-10 menit)

Demo **DATA SINTETIS / SIMULASI** untuk dosen. Target `future_7d_mean_sbp` masih usulan. Jangan menyatakan akurasi klinis, diagnosis, 570 responden unik atau persetujuan target yang belum ada.

## Persiapan sebelum presentasi

1. Baca [CP3_FINAL_REPORT.md](CP3_FINAL_REPORT.md) dan [CP3_BASELINE_REPORT.md](CP3_BASELINE_REPORT.md); bagi bagian presentasi sesuai kontribusi anggota.
2. Pastikan Docker Desktop berjalan. Dari root: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start_cp3_demo.ps1`. Script hanya load awal bila database **demo terpisah** kosong; bila sudah berisi, mempertahankannya. Tidak ada `.env` yang harus diubah.
3. Buka `http://127.0.0.1:8081`, API `http://127.0.0.1:8001/api/docs`, notebook 03 dan dokumen laporan. Gunakan 8081, bukan service lama 8080.
4. Reset filter, cek label sumber, 19 profil / 570 harian / 1.140 sesi. Cek Evaluasi Model: artefak tersedia dan fingerprint batch cocok. `python -m etl.verify_cp3_demo` menyediakan smoke check tanpa penulisan DB.
5. Siapkan screenshot nyata pada `reports/cp3_final/screenshots/` dan 3 grafik di `reports/cp3_baseline/figures/` sebagai bukti cadangan. Jangan menyebut screenshot sebagai demo live bila live gagal.

## Alur utama

| Waktu | Layar/bagian | Yang ditunjukkan dan disampaikan |
|---|---|---|
| 0:00-0:45 | Dashboard | “Ini prototipe CP3 berbasis dua formulir. Semua hasil simulasi; data asli masih dikumpulkan. Tujuan sementara membaca cakupan, pola sesi, dan keterbatasan pengukuran.” Tunjukkan empat KPI dan bedakan ID, ID-tanggal dan sesi. |
| 0:45-1:35 | Dashboard dan kualitas | Jelaskan rerata SBP sesi, missing tidur/duduk/merokok dan missing bukan nol. Pilih tanggal 8-14 September 2026 agar tersedia pembanding 1-7 September. Tunjukkan pembanding asli, lalu reset. Klik titik/heatmap untuk memfilter tanggal-sesi dan reset lagi. |
| 1:35-2:20 | Data Partisipan | Histogram usia/BMI, pendidikan/pekerjaan/lokasi dan tabel tanpa nama. Klik provinsi, pilih kota, tunjukkan perubahan semua grafik. Jelaskan satu profil satu ID dan kelompok kecil. Reset. |
| 2:20-3:15 | Analisis Faktor Risiko | Tidur, stres 1-5, aktivitas, asin/buah/sayur/kafein, merokok dan obat. Tunjukkan n hari/n ID pada tooltip; tidak menggunakan obat berbeda dari tidak patuh. Jelaskan asosiasi, bukan sebab-akibat. |
| 3:15-4:00 | Tren Tekanan Darah | Pilih SIM001, sesi Malam, tanggal 1-3 September: 3 harian/3 sesi. Dua bacaan, rerata dan pagination. Bandingkan Pagi/Malam setelah reset pilihan yang sesuai. |
| 4:00-5:00 | Prediksi | Pilih SIM001, klik Hitung perkiraan baseline. Jelaskan origin akhir riwayat, histori 7 hari dan rentang 7 hari setelahnya. Output mmHg adalah estimasi naive dari riwayat, bukan tekanan darah terukur masa depan/diagnosis atau inferensi LR. |
| 5:00-6:15 | Evaluasi Model | Tunjukkan run ID, cutoff, 60 train / 7 test, MAE/RMSE/R2 aktual. Naive lebih rendah MAE daripada LR pada test kecil ini. Jelaskan holdout ID + batas waktu + target test tidak overlap; imputer/scaler hanya fit train. R2 bukan accuracy persen. |
| 6:15-7:00 | Notebook 03 / laporan baseline | Tunjukkan assertion audit, tabel skor dan residual/error terbesar. Skema subject-only lama dihitung ulang sebagai sensitivitas, bukan dipakai mengklaim hasil baru lebih baik. Tegaskan hanya 7 origin test sintetis; target belum disetujui final. |
| 7:00-8:00 | Laporan & Ringkasan dan Kelola Data | Narasi dinamis, keterbatasan dan tindakan verifikasi. Ekspor CSV mengikuti filter. Petunjuk dry-run, tidak ada upload website. Akhiri dengan checklist CP3 teknis dan keputusan yang masih perlu dosen. |

Untuk 5 menit: gabungkan profil/faktor/tren menjadi 90 detik, tampilkan notebook hanya audit dan skor, tetap sampaikan keterbatasan. Untuk 10 menit: tambahkan API metadata, hash artefak, diagram warehouse dan bukti tes; jangan habiskan waktu menjalankan ulang build/training saat presentasi.

## Pertanyaan yang perlu dijawab jujur

- **Mengapa hanya 7 test?** Data sintetis 19 ID selama 30 hari. Setelah holdout ID/waktu, target test dibuat tidak overlap; hanya satu origin primer tersedia per ID. 42 rolling origin adalah sensitivitas berkaitan, bukan 42 sampel independen.
- **Apakah model lebih baik?** Pada split primer ini naive memiliki MAE lebih kecil. Tidak ada klaim signifikansi/generalisasi. Tuning dan tiga algoritma belum dikerjakan.
- **Apakah target disetujui?** Belum. Minta konfirmasi definisi target/bobot hari-sesi, minimum bacaan valid, origin akhir hari, serta strategi validasi aktual.
- **Apakah data primer cukup?** Belum dibuktikan. 570 baris sintetis bukan data primer atau 570 orang; tanyakan interpretasi minimum 500 baris pengamatan berulang dan kebutuhan jumlah ID.
- **Apakah sudah online?** Ini demo lokal Docker CP3. URL publik, akses data aktual, uji pengguna dan model final merupakan tahap selanjutnya.

## Cadangan bila ada gangguan

API kosong: jangan isi angka manual. Periksa `docker compose -f compose.cp3-demo.yaml -p toba-cp3-demo ps` dan log backend; gunakan script start hanya untuk stack demo. Jika artefak tidak tersedia, periksa manifest/hasil verifikasi offline; jangan menyunting JSON metrik. Jika Docker/browser tidak dapat berjalan, tampilkan bukti tes dan screenshot yang benar-benar tersedia sambil menyebut bahwa itu bukti rekaman pengujian, bukan live demo.

Database demo berada di RAM. Jangan menghentikan/recreate service db selama presentasi. Tidak perlu menyentuh service aktif, volume, data aktual, `.env`, atau menjalankan ETL aktif untuk memperbaiki demo.
