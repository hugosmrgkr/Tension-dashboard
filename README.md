# Toba Health Insight — React + FastAPI + PostgreSQL

Migrasi kode Streamlit asli `mental-health-dashboard-main.zip` ke aplikasi web terpisah. **Mempertahankan 8 halaman, palet warna, sidebar Danau Toba, grafik Plotly, rumus agregasi partisipan, batas status tekanan darah, serta generator dataset demo asli.** Visual diimplementasikan ulang di React/CSS sehingga tampilannya mendekati desain lama, tidak menjamin pixel-perfect.

> **Status:** prototipe dashboard yang dapat dijalankan. Evaluasi ML dan prediksi model masih demo; **jangan digunakan untuk diagnosis**. Sumber data bawaan adalah sintetis, bukan penelitian lapangan.

## A. Cara menjalankan — Docker Compose (direkomendasikan, menggunakan PostgreSQL)

Prasyarat: Docker Desktop + Compose.

```bash
cp .env.example .env
# ubah POSTGRES_PASSWORD di .env sesuai kebutuhan

docker compose up --build -d
```

- Website: **http://localhost:8080**
- Status backend: **http://localhost:8080/health**
- Database: PostgreSQL 16 (service `db`); data persisten di Docker volume `postgres_data`.

Untuk berhenti: `docker compose down`. Jangan menggunakan `docker compose down -v` jika ingin mempertahankan data.

Backend otomatis membuat skema database **1 tabel fakta + 3 dimensi** dan mengisi 25 partisipan × 30 tanggal = 750 baris sintetis ketika database pertama kali kosong.

## B. Cara menjalankan manual (tanpa Docker)

Prasyarat: Python 3.11+, Node.js 20.19+ atau 22.12+, npm. Untuk PostgreSQL manual, buat database `toba_health`, lalu pasang `psycopg` dari requirements.

Terminal 1:

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
# Windows PowerShell: $env:DATABASE_URL='postgresql+psycopg://user:pass@localhost:5432/toba_health'
# Linux/macOS: export DATABASE_URL='postgresql+psycopg://user:pass@localhost:5432/toba_health'
uvicorn app.main:app --reload --port 8000
```

Tanpa `DATABASE_URL`, backend menggunakan **SQLite lokal hanya untuk pengembangan**, bukan PostgreSQL. Ini memudahkan smoke test; untuk memenuhi stack yang dipilih gunakan Compose atau set variabel PostgreSQL.

Terminal 2:

```bash
cd frontend
npm install
npm run dev
```

- React dev: http://localhost:5173
- Swagger API dev: http://localhost:8000/docs
- Vite mem-proxy `/api` ke FastAPI di port 8000.

## Arsitektur

```text
React (Vite, Plotly.js, lucide-react)
    │  GET /api/analytics, GET /api/measurements, POST /api/predict/demo
    ▼
FastAPI (Pandas: agregasi, filtering, klasifikasi ambang)
    │  SQLAlchemy
    ▼
PostgreSQL star schema
    ├─ dim_partisipan  (demografi + faktor risiko)
    ├─ dim_tanggal     (tanggal, bulan, tahun)
    ├─ dim_kecamatan  (wilayah)
    └─ fact_pengukuran (sistolik, diastolik, status)
```

## 8 halaman hasil migrasi

| Halaman | Fitur |
|---|---|
| Dashboard | 4 kartu KPI, tren tekanan darah, donut distribusi, usia, korelasi heatmap, metrik ML **contoh**, 5 sampel |
| Data Partisipan | Tabel paginasi, pencarian/filter global |
| Analisis Faktor Risiko | BMI box plot, grafik aktivitas, pola makan, box merokok, scatter tidur |
| Tren Tekanan Darah | Mean/min/max harian dan tabel agregasi |
| Prediksi Hipertensi | Input usia/BMI/sistolik/diastolik dan output **klasifikasi aturan** |
| Evaluasi Model | Tabel/batang perbandingan empat model **placeholder** |
| Laporan & Ringkasan | Ringkasan filter, distribusi, insight deskriptif, ekspor TXT |
| Kelola Data | Upload CSV/XLSX, reset demo, tambah/edit/hapus data, ekspor CSV/Excel/TXT |

Filter global tersedia pada semua halaman (pada dashboard berada di panel kanan). Alur API memanggil agregasi Pandas dari data warehouse, bukan dari kode frontend yang hardcoded. Data edit disimpan ke database.

## Endpoint API

| Endpoint | Kegunaan |
|---|---|
| `GET /api/meta` | Metadata sumber, tanggal, wilayah, partisipan |
| `GET /api/analytics` | Data agregasi grafik dan KPI, menerima filter opsional |
| `GET /api/measurements` | Data tabular berhalaman (`page`, `page_size`) |
| `POST /api/predict/demo` | Hasil aturan ambang, bukan inference ML |
| `GET /api/model/demo` | Angka evaluasi contoh (`is_placeholder: true`) |
| `POST /api/data/upload` | Impor CSV/XLSX mengganti data aktif |
| `POST /api/data/reset` | Kembali ke data sintetis bawaan |
| `POST /api/measurements` | Tambah pengukuran |
| `PUT /api/measurements/{id}` | Sunting pengukuran |
| `DELETE /api/measurements/{id}` | Hapus pengukuran |
| `GET /api/data/export?format=csv/xlsx/txt` | Download dataset/filter |

Filter query: `awal`, `akhir`, `kecamatan`, `jenis_kelamin`, `kelompok_usia`, `id_partisipan`.

## Logika dipertahankan dari Streamlit

- `klasifikasi_tekanan`: >= 160 atau >= 100 = Tahap 2; >= 140 atau >= 90 = Tahap 1; >= 130 atau >= 80 = Pra-hipertensi; sisanya Normal. **Batas proyek prototipe**, tidak disajikan sebagai pedoman klinis.
- `ringkas_per_partisipan`: agregasi tekanan darah **rata-rata per ID** lalu klasifikasi ulang. Jumlah kasus di atas rentang normal termasuk pra-hipertensi seperti rancangan lama; label KPI diperjelas agar tidak disebut kasus hipertensi definitif.
- Demo seed `rng(42)`: 25 partisipan × 30 tanggal (1–30 Oktober 2025). Distribusi status **rata-rata partisipan** = 17 normal, 5 pra-hipertensi, 3 tahap 1.
- Nilai model 85,3% dan confusion matrix 112/18/12/58 dalam ZIP Streamlit asli adalah **contoh desain**, tidak dilatih di sini.

## Perbedaan sengaja dari Streamlit

- State upload tidak lagi hanya di sesi browser; data tersimpan di PostgreSQL.
- Untuk mutu dan konsistensi dimensi, `id_partisipan + tanggal` harus unik. Atribut tetap satu partisipan harus konsisten; perubahan BMI/usia/gaya hidup melalui satu baris akan diterapkan pada seluruh riwayat partisipan tersebut agar dimensi tetap konsisten. Status dari data upload **dihitung ulang** berdasarkan sistolik/diastolik.
- Edit/hapus pada web dikerjakan sebagai **rebuild dataset kecil** untuk menjaga integritas dimensional. Saat dataset besar, ganti dengan incremental ETL/UPDATE transaksi yang lebih efisien.
- `kelompok_usia` mengikuti 5 bucket asli 15–24 hingga 55–64. Upload dibatasi usia 15–64 pada prototipe ini.
- Tidak ada fitur autentikasi/otorisasi. Untuk data kesehatan asli, **wajib** menambahkan auth, logging audit, keamanan transport, retensi dan pemenuhan ketentuan privasi sebelum dipublikasikan.

## Kesesuaian dengan dokumen dosen

Sudah ada: kerangka satu aplikasi dengan dua modul, dataset tabular, visualisasi Plotly, filter global, 1 fact + 3 dimension, ETL yang dapat diulang, endpoint API, dan delapan halaman.

**Belum selesai (bukan disembunyikan):** dataset penelitian sah sesuai minimum (>= 500 data primer atau >= 5.000 data publik, >= 10 atribut, bukan Kaggle), data dictionary/kualitas sebelum-sesudah, EDA 5 insight berbasis data penelitian, ≥ 5 jenis visual advance dan drill-down/cross-filter sempurna, model ML sungguhan (>= 3 algoritma, split valid, tuning, metrik, ROC dan analisis kesalahan), model card, deployment publik, jurnal, dan laporan akhir. Jangan menggunakan data sintetis/matriks contoh sebagai klaim pemenuhan rubric.

## Testing

```bash
cd backend
pip install -r requirements.txt pytest httpx
python -m pytest -q
```

Uji backend dengan SQLite sementara. Uji PostgreSQL melalui Docker Compose bila Docker tersedia. Untuk deployment publik, siapkan domain HTTPS, konfigurasi CORS, autentikasi, dan secret yang aman.

## Catatan penggunaan AI

Migration scaffold, React UI, FastAPI API, dan dokumentasi dibuat dengan bantuan AI atas permintaan pemilik project; seluruh fungsi perlu diuji, dipahami, diverifikasi, dan dinyatakan sesuai aturan dosen.
