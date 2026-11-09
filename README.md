# Toba Health Insight — Dashboard Tekanan Darah (Checkpoint M6–M8)

**React + Vite + Plotly · FastAPI · PostgreSQL · Docker Compose**

Prototipe interaktif untuk eksplorasi pola pengukuran tekanan darah **pagi dan malam** serta faktor gaya hidup. Dashboard memakai **dua formulir sintetis**, bukan data penelitian aktual dan bukan alat diagnosis.

> **STATUS: DATA SINTETIS / SIMULASI.** Hasil tidak boleh dipakai sebagai kesimpulan kesehatan masyarakat maupun klaim performa pada pasien nyata.

## Jalankan di Windows / Docker Desktop

```powershell
# dari folder project
Copy-Item .env.example .env
# untuk volume lama, PERTAHANKAN password yang dipakai PostgreSQL lama
# untuk pemasangan baru, ubah password di .env sebelum pertama kali start

docker compose up --build -d
docker compose ps
```

- Frontend: **http://localhost:8080**
- Swagger FastAPI: **http://localhost:8080/api/docs**
- Health: **http://localhost:8080/health**
- Hentikan tanpa menghapus database: `docker compose down`

**Jika sudah pernah menjalankan versi Streamlit→React sebelumnya:** Compose v2 membuat tabel baru dengan suffix `_v2` dan tidak menghapus tabel lama. **Jangan gunakan `docker compose down -v`** karena menghapus data volume PostgreSQL. Jika perlu migrasi data lama, lakukan backup dan audit terlebih dahulu. Uji di lingkungan lokal, bukan di deployment publik.

### Teman satu kelompok

Clone repository, jalankan Docker Desktop, salin `.env.example` menjadi `.env`, atur password lokal, lalu `docker compose up --build -d`. Database tiap laptop terpisah dan disemai dengan dataset simulasi yang sama (19 profil, 570 catatan harian, 1.140 sesi). File asli responden tidak boleh di-commit.

Panduan layar demi layar: [`docs/PANDUAN_PENGGUNA.md`](docs/PANDUAN_PENGGUNA.md).

## Cara membaca dashboard (8 halaman)

| Halaman | Apa yang dilihat | Penjelasan |
|---|---|---|
| Dashboard | 4 KPI dan 4 grafik utama | Responden, catatan ID×tanggal, sesi, dan rerata sistolik. Garis Pagi/Malam tidak menghitung jumlah orang dua kali. |
| Data Partisipan | Profil anonim | ID pseudonim, demografi, BMI turunan dan jumlah hari pencatatan. |
| Analisis Faktor Risiko | Grafik gaya hidup | Tidur, stres 1–5, aktivitas menit, makanan asin, buah, sayur, kafein, dan treemap aktivitas. Hanya asosiasi. |
| Tren Tekanan Darah | Tren sesi dan bacaan mentah | Dua pembacaan tetap tersedia. Pilih satu ID untuk menelusuri sesi internal. |
| Prediksi Hipertensi | Baseline regresi | Tombol memilih ID dan menghitung **rata-rata SBP 7 hari sebelumnya** sebagai estimasi rata-rata 7 hari berikutnya. Bukan diagnosis hipertensi. |
| Evaluasi Model | Metrik awal | MAE/RMSE/R² baseline naif vs Linear Regression, group split berdasarkan responden, aktual-vs-prediksi dan residual. **Hanya simulasi.** |
| Laporan & Ringkasan | 5 poin deskriptif | Semua pernyataan berasal dari agregat filter aktif, bukan temuan populasi. |
| Kelola Data | Audit dan unduh | Sumber, kualitas data, ekspor tanpa nama, dan impor pasangan yang dinonaktifkan secara default. |

**Filter global:** periode tanggal, provinsi, kabupaten/kota, jenis kelamin, kelompok usia, sesi, pekerjaan. Filter hanya menampilkan variabel yang dikumpulkan dalam dua formulir; tidak ada kecamatan fiktif atau satu kolom `pola_makan` palsu.

## Data dan desain warehouse

- Form Awal: 19 profil / 24 kolom; `respondent_id` unik.
- Form Harian: 570 ID×tanggal / 28 kolom, dua sesi per hari; 1.140 fakta sesi.
- 3 dimensi: `dim_participant_v2`, `dim_date_v2`, `dim_session_v2`.
- 2 fakta: `fact_bp_session_v2` (ID×tanggal×sesi) dan `fact_daily_behavior_v2` (ID×tanggal).
- Sumber utama `data/sample/Data_Responden_Sintetis.csv` + `data/sample/Data_Harian_Sintetis.csv`, tidak digabung secara destruktif. Workbook gabungan hanya referensi alternatif.
- CSV sintetis tidur `06:31` diinterpretasi **6 jam 31 menit** untuk demo. Data aktual tidak dikonversi sampai semantik pertanyaan dikonfirmasi.
- Nama asli/teks `Nama lengkap` tidak masuk database analitik/API. ID digunakan untuk relasi.

Data dictionary: `docs/DATA_DICTIONARY.md`; ERD: `docs/ERD.md`; pencapaian checkpoint: `docs/CHECKPOINT_M6_M8.md`.

## Baseline model yang dapat diulang

Metrik di `models/baseline_metrics.json` dihasilkan oleh kode `backend/app/baseline.py`. Menyertakan model pembanding `models/linear_regression_synthetic.joblib`. Notebook `notebooks/01_baseline_regresi.ipynb` menyediakan eksperimen dan uraian langkahnya.

```powershell
# jika ingin menjalankan ulang eksperimen di Python lokal
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements-dev.txt
$env:PYTHONPATH = (Resolve-Path backend).Path
python -c "from app.baseline import run_experiment; print(run_experiment('data/sample/Data_Responden_Sintetis.csv','data/sample/Data_Harian_Sintetis.csv','models')['scores'])"
```

Model hanya untuk M6–M8; pemilihan target final, pelatihan tiga algoritma, tuning, dan penilaian atas data aktual masih bergantung pada kelayakan data/persetujuan dosen.

## ETL dan test

```powershell
$env:PYTHONPATH = (Resolve-Path backend).Path
python etl/import_data.py --synthetic --dry-run  # hanya memeriksa, tidak mengubah DB
python -m pytest backend/tests/test_api_v2.py -q
```

Dashboard tanpa login hanya melayani data **sintetis**. Jika source v2 diganti data non-sintetis, endpoint analitik dan ekspor menolak akses hingga autentikasi dibangun. Impor data melalui UI **nonaktif** secara default dan tidak boleh dibuka ke publik untuk data kesehatan. Untuk pengujian lokal dengan data yang benar-benar boleh diolah, set `ENABLE_IMPORT=true` dan `IMPORT_TOKEN` rahasia yang kuat di `.env`, kemudian build/restart backend; ini bukan autentikasi produksi. File `raw` yang mengandung identitas harus dikelola terpisah dalam penyimpanan privat yang disetujui. Tidak ada endpoint menghapus volume database.

## Hal yang belum selesai (jangan salah klaim)

- Data **primer/aktual** yang tervalidasi; dataset sintetis **tidak memenuhi** syarat minimal 500 baris data primer.
- Persetujuan dosen atas target `future_7d_mean_sbp`, protokol pengukuran, definisi tidur dan kriteria responden.
- Eksperimen **minimal tiga** algoritma beserta tuning, validasi pada data aktual, model card final dan deployment model produksi.
- Deployment publik dengan autentikasi, perlindungan data, uji usability, dan pengujian keamanan.
- Full checklist visualisasi advance/interaksi M9–M10, final storytelling berbasis data aktual, dokumen akhir dan jurnal.

## Keamanan dan kolaborasi

Jangan commit `.env`, data kesehatan asli, nama/kontak responden, atau data mentah privat. Jangan hapus volume Docker tanpa backup. Gunakan pull request dan logbook kontribusi; deklarasikan penggunaan AI sesuai brief dosen. Aplikasi publik harus dibatasi pada agregasi yang tidak mengidentifikasi individu.
