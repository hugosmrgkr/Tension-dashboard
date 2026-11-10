# CP3 Checklist - bukti kesiapan teknis

> **CATATAN SINKRONISASI (10 Nov 2026, CP3-K01):** Sebagian bukti di bawah menunjuk hasil CP3 lama. Bukti regresi P0/P1 terbaru ada di [`P0_P1_FINAL_AUDIT.md`](P0_P1_FINAL_AUDIT.md) dan [`reports/p0_p1_final_verification.md`](../reports/p0_p1_final_verification.md) (dijalankan ulang 10 Nov 2026: backend 73 passed/1 skipped pada SQLite dan PostgreSQL asli, frontend 10/10 passed, build sukses).

SELESAI berarti tersedia dan diuji pada **DATA SINTETIS / SIMULASI**; bukan tanda persetujuan dosen atau pemenuhan seluruh luaran final.

| Butir | Status | Bukti / catatan |
|---|---|---|
| Dua formulir, ID dan grain CP2 | SELESAI | Dictionary/ERD; 19 profil / 570 ID-tanggal / 1.140 sesi pada audit demo. |
| Missing, karantina dan EDA | SELESAI | `docs/CP2_DATA_READINESS.md`, notebook 02 dan `reports/cp2/`. Sumber tidak diubah. |
| 3 dimensi / 2 fakta / ETL reproducible | SELESAI | `reports/cp3_final/demo_warehouse.json`, PK/FK/unique, nol orphan; CLI CP2 tidak diubah. |
| Delapan halaman dashboard dari PostgreSQL | SELESAI | Browser Docker: screenshot desktop/mobile 1-8, `browser-results.json`. |
| Empat KPI, pembanding bila ada | SELESAI | API/tes filter dan UI; tidak membuat pembanding fiktif saat tidak tersedia. |
| Filter/ID/sesi/ekspor dan interaksi | SELESAI | Tes cross-filter, provinsi-kota, ID-tanggal-sesi dan unduhan CSV. |
| Empty/error state dan label simulasi | SELESAI | Backend empty warehouse dan browser response simulation; tanpa data dummy fallback. |
| Baseline naive + Linear Regression | SELESAI | `models/`, notebook 03, laporan baseline; bukan tiga algoritma final. |
| Audit fitur tidak memakai masa depan | SELESAI | Tes mutasi masa depan, window batas kalender, audit fit train/preprocessing. |
| Split ID + waktu + overlap target test | SELESAI | `models/baseline_metrics.json` audit: 0 ID/shared measurement/target-test overlap; training overlap diakui. |
| Metrik aktual, residual dan error analysis | SELESAI | `reports/cp3_baseline/metrics.csv`, prediksi presisi penuh, error CSV/PNG. |
| Integritas dan kompatibilitas artefak/API/UI | SELESAI | Manifest hash, reload joblib, penolakan file rusak; metrik UI dicocokkan pada browser. |
| Kesetaraan window ML dari warehouse | SELESAI | `warehouse-ml-equivalence.json`: 323 window cocok dan prediksi LR cocok. |
| Backend, frontend, build dan browser | SELESAI | XML/JSON di `reports/cp3_final/`; ringkasan terbaru pada laporan final. |
| Notebook reproducible dan dieksekusi | SELESAI | `03_verifikasi_baseline_cp3.ipynb`: 6 sel kode sukses, 3 gambar tersimpan. |
| Demo Docker terpisah dan skenario 5-10 menit | SELESAI | `compose.cp3-demo.yaml`, script start, `CP3_DEMO_SCRIPT.md`, port 8081. |
| Laporan kemajuan, checklist, rencana lanjut | SELESAI | Dokumen CP3 progress/baseline/demo/next/final. |
| Warehouse aktif dan berkas terlindungi | SELESAI | Fingerprint before/after, hash sumber/.env/pipeline/notebook CP2; tidak ada ETL aktif. |
| Persetujuan formal CP1/topik/target/KPI/pengguna | SEBAGIAN | Arah kerja ada; bukti persetujuan final dosen tidak ditemukan. |
| Dataset aktual, izin dan kecukupan primer | BELUM | Tidak digantikan dengan fixture sintetis. Keputusan jumlah ID/person-day dan protokol diperlukan. |
| Validasi statistik/klinis dan generalisasi aktual | BELUM | Hanya 7 origin test sintetis; tidak ada klaim pasien nyata. |
| Lima jenis advance final, tuning, >=3 algoritma | SEBAGIAN | Empat keluarga advance konservatif dan dua pendekatan awal; rencana M9-M10, belum seluruh ketentuan akhir. |
| Public deployment, model/input final, user study | BELUM | CP4-CP5; demo lokal bukan URL publik. |
| Logbook/kontribusi, deklarasi AI dan dokumen akhir | SEBAGIAN | Materi teknis tersedia; kontribusi tim/izin/pengesahan dan deklarasi AI harus diisi tim secara faktual. |

**Kesimpulan:** Definition of Done CP3 teknis sintetis terpenuhi. Checklist formal akademik dan penelitian aktual di atas tetap terbuka; bukan alasan mengklaim CP4/CP5 selesai.
