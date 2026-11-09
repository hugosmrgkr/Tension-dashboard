# CP3 Tahap 2 - Penyempurnaan Dashboard Toba Health Insight

Status: **dashboard v1 CP3 selesai diimplementasikan dan diuji pada workspace**. Dataset yang diperiksa adalah **DATA SINTETIS / SIMULASI**, bukan hasil pengumpulan responden asli. Service Compose aktif belum diganti dengan kode baru. Tidak ada ETL commit, reset database, penghapusan volume, perubahan `.env`, training model, commit atau push.

## 1. Audit dan acuan

Audit membaca alur aktif `App.jsx -> pages/Pages.jsx -> components/Visuals.jsx / Common.jsx`, API `main.py / analytics_v2.py`, laporan CP2, CP3 Tahap 1, serta kedua PDF di direktori induk workspace:

| Acuan | Bagian yang diperiksa | Cara memakai acuan |
|---|---|---|
| `Deskripsi_Proyek_DA_DS.pdf` | Hal. 4: visualisasi/interaksi/KPI/storytelling; hal. 6: timeline M6-M8 dan CP3 | Brief resmi: CP3 adalah dashboard v1 dengan warehouse dan laporan baseline/rencana eksperimen. Tiga algoritma, tuning, integrasi final dan deployment memiliki tahap lanjutan. |
| `Panduan_Utama_Proyek_Tekanan_Darah_DALIS_DASI.pdf` | Hal. 10-12: Bab 5-6, variabel, grain, privasi, interaksi dan jalur sintetis/aktual; hal. 15-16: keputusan terbuka/timeline; hal. 20: matriks ketentuan | Dokumen kerja versi 1.0, 2 November 2026. Contoh halaman/visual adalah usulan, bukan bukti persetujuan atau kondisi kode terkini. |
| `docs/CP2_DATA_READINESS.md`, `docs/CP3_STAGE1.md` | Kontrak dua formulir, validitas, missing, ETL manual, API, hasil tes dan status warehouse aktif | Fondasi dipertahankan; kode serving diperluas tanpa mengubah pipeline atau skema tabel. |

Tidak ditemukan PDF terpisah bernama daftar perbaikan dashboard pada workspace. Matriks kesesuaian di bawah memetakan dua PDF yang benar-benar tersedia dan daftar perbaikan pada permintaan Tahap 2. Penyebutan CSV dalam pekerjaan ini mengikuti sumber CP2 dan instruksi pengguna saat ini; tidak mengganti sumber menjadi contoh workbook dalam dokumen kerja lama.

Temuan awal: profil hanya berupa tabel; merokok, kepatuhan obat dan waktu duduk belum mendapat grafik yang memadai; beberapa grafik kurang penjelasan sampel/empty state; interaksi chart belum terhubung ke filter global; baseline perlu pemisahan konteks eksperimen yang lebih jelas. Pemeriksaan browser juga menemukan logo SVG tanpa namespace, label MAE terpotong, dan filter ponsel terlalu panjang di atas KPI. Semua ditangani pada tahap ini.

## 2. Perubahan per halaman

| Halaman | Perubahan | Definisi dan batasan |
|---|---|---|
| Dashboard | Empat KPI beserta definisi dan selisih absolut terhadap periode sebelumnya bila tersedia; panel kualitas; tren SBP/DBP, boxplot dan heatmap dengan klik tanggal-sesi | Responden aktif = ID dengan sesi valid; catatan harian valid = ID-tanggal diterima ETL, bukan semua kolom lengkap; sesi valid = SBP dan DBP tersedia; SBP = rerata seluruh sesi valid. Pembanding berperiode sama panjang dan filter non-tanggal sama. Tidak mengisi pembanding fiktif. |
| Data Partisipan | Histogram usia/BMI; komposisi jenis kelamin; pendidikan, pekerjaan, provinsi, kota dan kelompok usia; pencarian tabel; tombol telusuri ID | Satu profil = satu ID. Pencarian hanya menyaring tabel dan diberi keterangan. Grafik memakai filter global. Tanpa nama, kontak atau alamat pribadi. BMI deskriptif, tanpa kategori diagnosis. |
| Analisis Faktor Risiko | Tidur, stres, aktivitas, makanan asin, buah, sayur, kafein, jenis aktivitas, merokok, jumlah merokok, obat, duduk dan tren usia; tabel Pearson r | Perilaku = satu ID-tanggal, tidak digandakan untuk dua sesi. Tooltip kategori memuat n hari dan ID unik; pasangan numerik memakai complete cases per variabel. Tidak menggunakan obat berbeda dari tidak patuh. Missing jumlah merokok berbeda dari nol. Seluruh interpretasi adalah asosiasi. |
| Tren Tekanan Darah | Perincian ID terhubung ke filter global; SBP/DBP Pagi/Malam; distribusi, heatmap; tabel dua bacaan, rerata dan jumlah bacaan valid | Semua sesi mentah tetap dapat ditelusuri melalui pagination. Grafik memakai sesi valid, tabel mempertahankan pembacaan tidak lengkap. Tanggal formulir dibedakan dari waktu kirim. |
| Prediksi Hipertensi | Input ID, syarat riwayat tujuh hari berturut-turut, output estimasi mmHg, metode dan akhir riwayat; loading/error yang jelas; pembatalan respons lama saat ID berganti | Algoritma/endpoint baseline dipertahankan. Baseline lama memakai SBP tersedia untuk rerata harian; syarat ini dijelaskan secara jujur, berbeda dari syarat analitik SBP+DBP. Tidak ada hasil contoh, diagnosis atau interval keyakinan buatan. |
| Evaluasi Model | Jumlah train/test, split ID, tabel MAE/RMSE/R2, MAE bar, aktual-prediksi dan residual dengan sampel/satuan/interpretasi | Metrik diambil via API dari artefak lama, bukan evaluasi ulang filter atau data aktual. Tidak ada akurasi persen. Garis ideal/residual nol memakai rentang hasil tersimpan, bukan batas BP hardcoded. |
| Laporan & Ringkasan | Lima narasi dari API: cakupan, rerata, selisih sesi, missing dan keputusan kerja; grafik dengan judul berbasis ukuran sampel aktif; tautan penelusuran | Selisih Malam-Pagi adalah perbandingan agregat, bukan estimasi berpasangan atau efek waktu. Rekomendasi terbatas pada verifikasi kualitas/penelusuran, bukan tindakan medis. |
| Kelola Data | Sumber dan jumlah seluruh warehouse, kualitas filter aktif, snapshot batch ETL, ekspor sesuai filter, contoh perintah dry-run | Tidak ada upload atau tombol load. Ekspor dinonaktifkan saat data analitik belum tersedia. Snapshot ETL lama tidak disajikan sebagai hasil filter. Peringatan audit CP2 belum dimuat tetap dipertahankan. |

## 3. Katalog visualisasi

Jumlah panel pada sumber berisi data: **34 panel**, termasuk pengulangan tren/distribusi untuk konteks halaman. Small multiples dihitung sebagai satu panel, bukan satu visual untuk setiap kelompok usia. Prediksi berupa output numerik dan kualitas berupa ringkasan, tidak ikut dihitung sebagai grafik.

| Halaman | Panel tersedia | Jenis / satuan |
|---|---|---|
| Dashboard (4) | Tren SBP, tren DBP, distribusi SBP sesi, heatmap SBP | Deret waktu; boxplot; heatmap. mmHg, tanggal, sesi dan n sesi. |
| Partisipan (8) | Usia, jenis kelamin, pendidikan, pekerjaan, provinsi, kabupaten/kota, BMI, kelompok usia | Histogram; donut; bar. Tahun, kg/m2, jumlah/persentase profil. |
| Faktor Risiko (14) | Tidur-SBP, stres-SBP, aktivitas-SBP, DBP-usia, asin-SBP, buah, sayur, jenis aktivitas, kafein-SBP, merokok-SBP, jumlah merokok-SBP, obat-SBP, duduk-SBP, tren usia | Scatter; boxplot; violin; horizontal bar; donut; treemap; small multiples. mmHg, jam, menit/hari, kali/hari, kategori formulir, n ID-tanggal/ID. |
| Tren (4) | SBP, DBP, distribusi SBP, heatmap | Deret waktu; boxplot; heatmap dengan detail sesi. |
| Evaluasi (3) | Perbandingan MAE, aktual-prediksi, residual | Bar dan scatter/garis referensi. MAE/residual mmHg; bukan accuracy. |
| Laporan (1) | Tren SBP yang mendukung narasi | Deret waktu mmHg dengan cakupan sampel aktif. |

Setiap panel memiliki judul, keterangan sampel, satuan pada sumbu/tooltip atau keterangan komposisi, serta interpretasi singkat. Grafik tanpa nilai valid berubah menjadi pesan kosong. Missing tidak menjadi nol. Batas 12 kategori yang sebelumnya memotong grafik kategori dihapus. Small multiples memakai rentang SBP bersama agar perbandingan antarpanel adil.

Keluarga visual lanjutan yang sudah ada: **heatmap, treemap, small multiples, violin/boxplot**. Violin dan boxplot diperlakukan konservatif sebagai satu keluarga pada penghitungan syarat final. Deret waktu saat ini belum beranotasi; tidak diklaim sebagai jenis advance kelima. Tidak memaksakan Sankey/peta tanpa kebutuhan/atribut yang tepat hanya untuk menaikkan jumlah jenis.

## 4. Interaksi dan konsistensi data

Alur tetap: `dua formulir CP2 -> ETL manual -> warehouse PostgreSQL v2 -> FastAPI -> React/Plotly dan ekspor`. Kode serving tidak membaca raw CSV. Penambahan backend bersifat kompatibel: `demographics`, `correlations`, kategori obat, n ID kategori, opsi pendidikan, dan hierarki provinsi-kota. Tidak ada perubahan tabel atau pipeline.

- Filter global: ID, tanggal, provinsi, kota, jenis kelamin, usia, sesi, pekerjaan dan pendidikan. Chip aktif dapat dihapus satu per satu; reset mengembalikan seluruh pilihan.
- Pintasan 7/30 hari memakai tanggal terakhir yang **tersedia pada sumber**, bukan tanggal komputer. Validasi tanggal terbalik tidak mengirim request analitik atau mempertahankan KPI lama.
- Klik titik tren/sel heatmap memilih tanggal dan Pagi/Malam; klik scatter memilih ID-tanggal; pilihan ini berlaku pada grafik lain, tabel dan ekspor.
- Klik grafik profil menerapkan jenis kelamin/pendidikan/pekerjaan/usia/wilayah. Provinsi dapat diperinci ke kota; mengganti provinsi menghapus kota lama dan membatasi opsi kota ke provinsi tersebut.
- Pilihan grafik memiliki alternatif pada filter/select/tombol tabel. Klik chart bukan satu-satunya cara memperinci data.
- Di ponsel, filter awalnya diringkas dan bisa dibuka; chip aktif tetap terlihat. Sidebar dapat ditutup dengan tombol, backdrop, pilihan halaman atau Escape. Fokus keyboard, ukuran teks dan reduced motion ditangani.
- Dua halaman baseline memperlihatkan konteks artefak terpisah. Filter analitik tidak disajikan sebagai pelatihan/evaluasi ulang model.

Pearson r dihitung per pasangan lengkap ID-tanggal, hanya bila n >= 3 dan kedua variabel bervariasi. Nilai konstan/kurang data menghasilkan `null`, bukan angka nol buatan. r tidak memiliki p-value/uji inferensi, dan pengukuran berulang tidak dianggap independen. Jumlah ID dan n pasangan ditampilkan.

## 5. Hasil pengujian

| Pengujian | Hasil dan bukti |
|---|---|
| Backend/API/CP2/CP3 | **51 lulus, 1 modul API v1 usang dilewati**. SQLite in-memory terisolasi; tidak diarahkan ke DB aktif. Penambahan tes memeriksa hitungan profil, filter pendidikan/ekspor, grain risiko, Pearson vs query SQL, variabel konstan, metadata lokasi dan database kosong. |
| React component tests | **9 lulus**. Angka arbitrary API, navigasi 8 halaman, pagination, missing, error, cross-filter, validasi tanggal dan variabel risiko. Renderer Plotly saja diganti probe. |
| Production build | **Lulus**, Vite 6.4.5. Plotly asli masuk build; bukan renderer probe. |
| Browser Microsoft Edge / Playwright | **6 skenario lulus**. Desktop 1440x1000 dan mobile 390x844; semua 8 halaman; grafik asli; baseline GET menghasilkan estimasi nyata; klik titik; provinsi-kota; filter ID/Pagi-Malam/tanggal; CSV benar-benar terunduh; empty/error state. Tidak ada page error JavaScript pada lintasan 8 halaman desktop. |
| Pembandingan aktif sebelum/sesudah | Transaksi READ ONLY dan fingerprint natural/count diperiksa. Koneksi API preview juga dipaksa `transaction_read_only=on`; startup DDL dimatikan. Tidak ada ETL commit atau penulisan dataset aktif. |
| Berkas terlindungi | Hash `.env`/ketiadaan file, pipeline/skema/audit CP2, CLI ETL, baseline, notebook, model dan dua CSV diperiksa terhadap awal Tahap 2. |

Bukti mesin: [verification.json](../reports/cp3_stage2/verification.json), [browser-results.json](../reports/cp3_stage2/browser-results.json), serta [screenshots](../reports/cp3_stage2/screenshots/). Screenshot `desktop-1` sampai `desktop-8` dan `mobile-1` sampai `mobile-8` mengikuti urutan halaman pada sidebar; `empty.png` untuk kondisi kosong, `mobile-viewport.png` untuk tampilan awal ponsel.

Browser memakai API preview dari kode terbaru yang hanya membaca PostgreSQL aktif sintetis. Kode frontend disajikan dari build produksi melalui Vite preview dengan proxy lokal. Kondisi warehouse kosong dan API gagal **disimulasikan pada respons jaringan browser**, tidak dengan mengosongkan/mematikan DB aktif. Empty warehouse sungguhan juga dicakup suite backend in-memory. Uji unduhan memeriksa berkas yang disimpan browser, bukan mengandalkan salinan response body pada event jaringan.

Peringatan yang tersisa: bundle Plotly sekitar **4,91 MB / 1,49 MB gzip**, peringatan ukuran chunk Vite, serta deprecation Starlette/httpx pada suite backend. Tidak menghambat kelulusan tes; pemecahan bundle/migrasi dependensi tidak dipaksakan pada CP3. Pemeriksaan ini bukan audit aksesibilitas/keamanan menyeluruh atau uji usability dengan pengguna akhir.

## 6. Status kesesuaian PDF / daftar perbaikan

| Ketentuan / perbaikan | Status sampai CP3 | Bukti / yang masih kurang |
|---|---|---|
| Dashboard v1 berjalan dengan warehouse (brief hal. 6, M8) | Siap secara teknis pada workspace dan preview | API/React/browser lulus; service Compose lama belum diperbarui. |
| Empat KPI dan pembanding (brief hal. 4; panduan hal. 10) | Tersedia secara kondisional | Periode sebelumnya sama panjang; bila tidak ada data, pesan eksplisit, tanpa target buatan. |
| Data profil anonim dan grain dua formulir (panduan Bab 4-6) | Tersedia pada sumber sintetis | Profil, ID-tanggal dan sesi dibedakan; data aktual/consent/kelayakan belum dinyatakan selesai. |
| Variabel gaya hidup asli dan asosiasi (panduan hal. 11) | Tersedia | Semua variabel pada permintaan Tahap 2 terwakili. Kategori obat/merokok dan missing dijelaskan. |
| Minimal 10 visual (brief hal. 4) | Tersedia | 34 panel, termasuk pengulangan konteks; katalog menjelaskan jenis dan grain, bukan menyamakan jumlah panel dengan jumlah jenis. |
| Minimal 5 jenis advance (persyaratan final) | Belum diklaim penuh | Empat keluarga konservatif tersedia. Pemilihan jenis kelima yang relevan dan penyempurnaan advance merupakan M9/dashboard v2. |
| Filter, drill-down, cross-filter, tooltip | Tersedia pada lingkup v1 | Klik chart teruji; wilayah provinsi-kota; opsi global/ekspor konsisten. Belum analisis hierarki waktu multilevel yang kompleks. |
| Storytelling dan temuan untuk keputusan | Tersedia sebagai simulasi | Lima narasi dan grafik berasal dari pilihan aktif. Keputusan terbatas pada verifikasi data; pertanyaan pengguna final dan temuan penelitian aktual masih perlu disahkan. |
| Responsif, loading/error/empty state | Teruji pada dua viewport | Tidak ada overflow halaman; tabel dapat digulir di dalam kontainer. Belum audit seluruh browser/perangkat dan uji usability 3-5 calon pengguna. |
| Baseline + pembanding dan metrik awal M7-M8 | Dipertahankan dan diperjelas | Naive 7-day mean dan Linear Regression tersimpan; tidak ada perubahan training/artefak. Target sementara masih memerlukan persetujuan dosen. |
| Tiga algoritma, tuning, evaluasi aktual/model card | Tahap berikutnya | Sesuai M9-M10, tidak dipalsukan atau dipaksakan ke pekerjaan UI ini. |
| Dataset primer minimum, sumber/izin, identitas | Belum terpenuhi oleh simulasi | 570 ID-tanggal dari 19 ID sintetis bukan bukti 500 baris data primer aktual atau 570 individu independen. |
| Deployment publik dan pengujian pengguna | Belum | CP4/CP5: autentikasi/akses data kesehatan, URL publik, input model final dan uji pengguna. |

Matriks ini adalah penilaian teknis terhadap kode dan dokumen yang tersedia, bukan pernyataan persetujuan dosen atau nilai checkpoint. Status lama dalam knowledge base tidak digunakan untuk menghapus bukti implementasi baru; keputusan yang ditandai terbuka tetap terbuka.

## 7. File yang berubah pada Tahap 2

- `backend/app/analytics_v2.py`: agregat profil, n ID kategori, variabel obat/merokok, asosiasi numerik dan hierarki lokasi.
- `backend/app/main.py`: parameter filter pendidikan; blok endpoint baseline tidak diubah.
- `backend/tests/test_cp3_stage2.py`: tes ekstensi API dengan fixture terisolasi.
- `frontend/src/App.jsx`: penghubung cross-filter, model loading dan validasi tanggal.
- `frontend/src/pages/Pages.jsx`: penyempurnaan delapan halaman beserta narasi/quality/sample/UX baseline.
- `frontend/src/components/Visuals.jsx`: grafik demografi, interaksi, tooltip, empty state dan range berbasis data.
- `frontend/src/components/Common.jsx`, `FilterBar.jsx`: sidebar, fokus/loading/empty state, filter ringkas, pendidikan, lokasi dan chip.
- `frontend/src/styles.css`, `frontend/public/logo.svg`: tema navy, responsivitas, keterbacaan, SVG namespace dan perbaikan hasil tinjauan browser.
- `frontend/package.json`, `package-lock.json`, `vite.config.js`, `playwright.config.js`, `tests/dashboard.test.mjs`, `tests/browser/dashboard.spec.js`: tooling, proxy preview dan tes.
- `README.md`, `docs/CP3_STAGE2.md`, `reports/cp3_stage2/*`: panduan dan bukti.

Perubahan CP2/Tahap 1 yang sudah ada pada working tree dipertahankan. Jangan menganggap semua isi `git diff` sebagai perubahan baru Tahap 2.

## 8. Menjalankan dan pekerjaan tersisa

Dari root project:

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests -q -p no:cacheprovider
Push-Location frontend
npm ci --no-audit --no-fund
npm test
npm run build
# Untuk pengembangan: arahkan proxy ke backend kode terbaru yang dipilih.
$env:TOBA_API_PROXY_TARGET = 'http://127.0.0.1:8000'
npm run dev
Pop-Location
```

`TOBA_API_PROXY_TARGET` hanya variabel proses untuk Vite dev/preview; bukan perubahan `.env` atau konfigurasi database. Preview produksi dapat dijalankan melalui `npm run preview`. Untuk mengulang tes browser, setelah build, atur proxy ke API terbaru yang melayani fixture sintetis yang sama dan jalankan `npm run test:browser`. Microsoft Edge dipakai pada Windows; sistem lain memerlukan browser Playwright yang dipasang terpisah. Tes browser mengharapkan fixture SIM001 dengan tanggal September 2026. Jangan mengganti/memuat dataset aktif hanya untuk memenuhi tes browser.

Container preview berlabel Tahap 2 dibuat terpisah, hanya membaca database, dan dihentikan setelah pemeriksaan. Tidak ada restart service Compose aktif. Penerapan operasional perlu membangun frontend **dan** backend yang cocok; backend lama belum mengirim agregat demografi/obat/pendidikan baru. Panduan ETL tetap merujuk [CP3_STAGE1.md](CP3_STAGE1.md); tidak ada perintah commit ETL yang dijalankan pada Tahap 2.

Prioritas tersisa untuk demo CP3: tinjau laporan/screenshot, terapkan pasangan kode backend-frontend bila dijadwalkan, dan pisahkan keputusan pemuatan CP2 terbaru dari deployment kode. Warehouse aktif masih memiliki hasil ETL lama, termasuk 19 profil dengan `active_days_week` kosong; dashboard menyajikan keadaan itu secara jujur. Pemuatan ulang CP2 tidak dikerjakan karena dilarang pada tahap ini.

Untuk tahap berikutnya: selesaikan keputusan dosen tentang target, protokol tidur, kriteria/izin responden dan kecukupan data primer; lanjutkan data aktual; baru lakukan eksperimen lanjutan, jenis advance yang relevan, model card, kontrol akses, deployment publik dan usability. Pekerjaan berhenti setelah CP3 Tahap 2 ini.
