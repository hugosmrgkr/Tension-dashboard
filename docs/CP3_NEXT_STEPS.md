# Setelah CP3: rencana CP4-CP5 (belum diimplementasikan)

Urutan mengikuti dependensi dan timeline brief, bukan pekerjaan yang diam-diam dijalankan pada finalisasi CP3.

| Urutan | Pekerjaan | Kriteria selesai / dependensi |
|---|---|---|
| 1 | Konfirmasi dosen dan pengguna | Setujui judul/tujuan, target `future_7d_mean_sbp` atau perubahan yang tercatat, akhir hari t, bobot sesi/hari, minimum pengukuran/hari, protokol tidur, kriteria inklusi, KPI dan pengguna. Jangan mengubah target tanpa keputusan eksplisit. |
| 2 | Akuisisi aktual dan tata kelola | Consent, registry ID, sumber/izin, penyimpanan privat, timestamp ketersediaan profil/late submission, pemeriksaan data primer/jumlah responden. Sintetis tidak digabungkan dengan aktual. |
| 3 | Validasi ulang CP2 pada aktual | Dry-run, audit missing/duplikasi/tanggal/format; dictionary dan keputusan koreksi; kelayakan window ML tanpa imputasi target. Load aktif hanya setelah pemeriksaan/backup/persetujuan target DB. |
| 4 - M9 | Dashboard v2 / visual advance relevan | Tinjau pengguna dan pertanyaan keputusan; pilih jenis advance kelima yang sesuai data, bukan memaksa peta/Sankey. Evaluasi interaksi, rentang sumbu, aksesibilitas dan ukuran bundle. |
| 5 - M9-M10 | Eksperimen lanjutan | Minimal tiga algoritma sesuai brief termasuk baseline dan model lanjutan, fitur temporal yang tersedia saat prediksi; validation/test terpisah, group-time/purging, tuning tanpa menyentuh test. Tambah kalender/jumlah ID agar test tidak hanya 7 origin. |
| 6 - M10 | Evaluasi/model card | MAE/RMSE/R2 dan metrik lain yang sesuai, analisis residual/kelompok, ketidakpastian yang sah, sensitivitas missing/window, argumentasi pemilihan berdasarkan validation. Tidak menganggap overlapping windows independen. |
| 7 - M11 / CP4 | Integrasi model final | Simpan artefak/versioning/manifest, inferensi fitur konsisten, input baru tervalidasi, guard dan observabilitas, tes kompatibilitas. Bedakan data tersedia pada origin vs target belum diketahui. |
| 8 - M12 | Deployment dan uji pengguna | URL publik, autentikasi/otorisasi/data minimization, HTTPS/secrets/backup/retensi, 3-5 calon pengguna, uji perangkat dan perbaikan berdasarkan temuan nyata. |
| 9 - M13 / CP5 | Luaran final | Laporan 12-20 halaman, jurnal, data docs/ERD, model card 1-2 halaman, slide, logbook/peer assessment dan pernyataan penggunaan AI; kontribusi anggota sesuai bukti. |

Metrik CP3 tetap disimpan sebagai eksperimen simulasi/historis ketika data aktual tersedia, bukan diganti label menjadi hasil penelitian. Buat versi sumber/model dan regresi penuh sebelum perpindahan sumber. Batas API publik untuk data aktual tidak boleh dimatikan hanya agar demo tampak berisi data.
