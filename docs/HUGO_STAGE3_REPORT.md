# Hugo Tahap 3 Visualisasi halaman Prediksi

Tanggal: 17 November 2026. Hugo mengonfirmasi kelanjutan Tahap 3 melalui percakapan.

## Hasil

Halaman Prediksi Tekanan Darah kini menampilkan dua grafik dari respons API yang
sama dengan hasil prediksi:

1. **Riwayat SBP dan DBP:** tujuh rerata harian satu ID sampai akhir origin.
2. **Estimasi rerata SBP tujuh hari berikutnya:** dua batang pembanding model dan
   baseline naif. Masing-masing satu nilai agregat, bukan tujuh prediksi harian.

Pengguna dapat memilih tanggal origin atau membiarkannya kosong agar server
memakai tanggal terakhir dengan SBP tersedia pada ID. Halaman menjelaskan bahwa
input ID/origin ini terpisah dari filter kelompok analitik.

## Asal dan grain data

- Tambahan `history_daily` pada respons `/api/model/predict` dibuat dari window
  harian yang **sama** dengan `inference_features`, bukan dari agregat kelompok
  dashboard atau data contoh frontend.
- Setiap baris berisi tanggal, SBP dan DBP untuk satu ID-tanggal. Nilai harian
  merata-ratakan sesi yang lolos gate BP menurut pipeline CP3.
- Riwayat dimulai t-6 dan berakhir t. `history_grain=respondent-date` menjelaskan
  grain tersebut. Pagi/Malam digabung di sini sesuai feature engineering;
  halaman Tren yang memisahkan sesi tidak diubah.
- Backend tetap mensyaratkan tujuh hari berturut-turut. DBP kosong ditampilkan
  null, tidak diisi nol. Frontend tidak menyambungkan missing dengan nilai palsu.
- Grafik riwayat tidak menampilkan tanggal setelah origin. Riwayat tidak ada atau
  duplikat tidak menghasilkan titik otomatis.
- Model tetap menghasilkan satu `prediction_mmHg` untuk `forecast_start` sampai
  `forecast_end`. Tidak ada prediksi DBP, confidence interval, atau deret prediksi
  harian yang dibuat dari satu angka rerata.

## Penanganan konteks dan metadata

- Hasil dibersihkan dan request dibatalkan ketika ID/origin berubah.
- Perubahan sumber, versi dataset, run model, status tersedia dan versi fitur
  membatalkan hasil/request lama walau daftar ID tidak berubah.
- Respons dengan ID, origin eksplisit, versi model atau fingerprint yang tidak
  cocok dengan konteks yang diketahui ditolak; respons terlambat diabaikan.
- Respons nonfinite tidak ditampilkan sebagai hasil prediksi.
- Metadata menampilkan versi model, asal eksperimen, batch training/inferensi,
  status kecocokan dan status target. Tanggal P2 diberi label tanggal artefak,
  bukan timestamp training presisi yang belum dibuktikan.
- Label sintetis, peringatan model kalah dari naif/fitur di luar rentang, dan
  loading/error/empty state tetap tersedia. Data aktual masih dibatasi Tahap 2.

## File yang dibuat atau diubah pada Tahap 3

| File | Perubahan |
|---|---|
| `frontend/src/pages/PrediksiTekananDarah.jsx` | Input origin, pembersihan konteks, metadata dan integrasi grafik |
| `frontend/src/components/prediction/PredictionCharts.jsx` | Grafik historis dan perbandingan dua nilai agregat; helper penyaringan riwayat |
| `backend/app/model_service.py` | Tambahan riwayat dari window inferensi pada respons; rumus fitur dan prediksi tetap sama |
| `backend/tests/test_prediction_history.py` | Paritas riwayat/fitur/origin dan pembatasan aktual |
| `frontend/tests/dashboard.test.mjs` | Tes grafik, origin, response usang dan ketidakcocokan model |
| `frontend/tests/browser/prediction_visuals.spec.js` | Pemeriksaan visual desktop/ponsel terhadap API pengujian |
| `docs/MODEL_INTEGRATION_CONTRACT.md` | Catatan status implementasi Tahap 3 |
| `docs/HUGO_STAGE3_REPORT.md` | Laporan ini |

Perubahan Tahap 2 yang sudah ada di working tree tetap dipertahankan. Tidak ada
pengubahan model aktif, notebook/ETL CP2, konfigurasi, `.env`, database utama atau
halaman anggota lain. Tidak ada training/promosi model baru untuk visualisasi ini.

## Pengujian yang dijalankan

| Pengujian | Hasil |
|---|---|
| Backend terarah: histori, registry dan API model P2 | **51 lulus**, 0 gagal |
| Frontend `npm test` | **22 lulus**, 0 gagal |
| Production build | **Berhasil**, 1.602 modul ditransformasi |
| Browser halaman Prediksi | **3 lulus**, 0 gagal, Microsoft Edge headless |
| Visual desktop dan ponsel | Screenshot diperiksa; tidak ada overflow horizontal pada uji 390 px |

Browser memakai FastAPI lokal dan SQLite sementara terpisah yang berisi dua CSV
sintetis (19 profil, 570 ID-tanggal, 1.140 sesi), bukan PostgreSQL aktif. Backend
test juga memakai SQLite di memori. Tidak ada pemuatan data ke warehouse utama.

Tes mencocokkan nilai grafik dengan respons API, memastikan riwayat tidak melewati
origin, menolak histori kurang, dan menghapus grafik lama ketika ID/tanggal berubah.
Frontend unit tests juga memeriksa respons terlambat saat model/data berubah.

Seluruh backend suite dan seluruh delapan halaman browser tidak dijalankan ulang
pada Tahap 3; suite penuh backend pada Tahap 2 adalah bukti historis terpisah.
Peringatan bundle Plotly besar dan deprecation TestClient Starlette/httpx tetap ada,
bukan kegagalan tes/build. Ini belum uji penerimaan keseluruhan Tahap 4.

## Bukti dan cara menjalankan

- [Hasil backend](../reports/hugo_stage3/backend-tests.xml)
- [Hasil browser](../reports/hugo_stage3/browser-results.json)
- [Prediksi desktop](../reports/hugo_stage3/screenshots/prediction-desktop.png)
- [Prediksi ponsel](../reports/hugo_stage3/screenshots/prediction-mobile.png)
- [Detail grafik ponsel](../reports/hugo_stage3/screenshots/prediction-mobile-history.png)
- Ringkasan pemeriksaan: `reports/hugo_stage3/verification.json`.

Untuk melihat implementasi, backend dan frontend harus menjalankan source terbaru.
Preview browser tadi menggunakan build terbaru dengan proxy ke backend uji sementara;
tidak melakukan rebuild/deployment stack utama `8080`.

Regresi backend terarah:

```powershell
$env:CP2_TEST_DATABASE_URL='sqlite://'
$env:OMP_NUM_THREADS='1'
.\.venv\Scripts\python.exe -m pytest backend/tests/test_prediction_history.py backend/tests/test_model_registry.py backend/tests/test_p2_model_api.py -q -p no:cacheprovider
```

Frontend: jalankan `npm test` dan `npm run build` di folder `frontend/`.
Browser test `prediction_visuals.spec.js` memerlukan API sintetis yang disiapkan
secara eksplisit pada lingkungan uji; tidak memuat data atau memulai ETL otomatis.

## Checkpoint

**Tahap 3 selesai.** Review kontrak tim, data aktual, paket rilis final, serta uji
penerimaan lintas fitur masih memiliki dependensi masing-masing. Tahap 4 belum
dimulai dan menunggu konfirmasi baru Hugo. Tidak ada commit, push atau merge otomatis.
