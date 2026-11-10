# Ringkasan Perbaikan P0/P1 dan Panduan Instalasi — Toba Health Insight

Dokumen ini dibuat **10 November 2026** sebagai jawaban langsung atas pertanyaan: *apa saja yang sudah diperbaiki, apakah semua P0/P1 sudah selesai, dan apa yang perlu diinstal untuk melanjutkan proyek ini.* Formatnya sengaja dibuat mirip dokumen audit (`Daftar_yang_harus_diperbaiki.pdf`) yang Anda kirimkan sebelumnya, supaya mudah dibandingkan baris-per-baris.

**Jawaban singkat untuk pertanyaan utama Anda: apakah semua P0/P1 sudah dikerjakan? Secara teknis, hampir semua — 10 dari 15 item 100% selesai dan teruji. Tapi TIDAK semua bisa berstatus "selesai final"**, karena 4 item memang secara sengaja menunggu **keputusan akademik dari dosen** (bukan keputusan teknis), dan 1 item menunggu **contoh data formulir asli** dari Anda. Saya jelaskan persis kenapa di bagian bawah, dan apa yang saya butuhkan dari Anda supaya item-item itu bisa benar-benar ditutup — bukan sekadar saya "mengarang" bahwa itu sudah selesai, karena itu justru dilarang keras dalam instruksi awal Anda sendiri (jangan membuat persetujuan dosen fiktif).

---

## Bagian A — Status Prioritas P0 (menghalangi integrasi data penelitian)

| ID | Masalah sebelumnya (dari audit lama) | Perbaikan yang sudah diterapkan dan diverifikasi | Status akhir |
|---|---|---|---|
| **P0-01** — Data contract dua sumber | Sistem lama hanya menerima satu file, satu skema. Data profil awal dan catatan harian belum dipisah/dihubungkan via ID. | `etl/import_data.py` dan `backend/app/pipeline.py` kini membaca **dua file terpisah** (profil 24 kolom, harian 28 kolom), memvalidasi nama kolom & tipe data masing-masing, lalu menghubungkan via `respondent_id`. Baris tanpa ID atau ID tidak cocok **ditolak/dikarantina dengan alasan jelas**, bukan digabung mentah. Mode dry-run tersedia dan sudah saya uji ulang: 19/19 profil & 570/570 harian diterima, 0 dikarantina. | **SEBAGIAN SELESAI.** Jalur teknisnya benar dan teruji penuh di atas data sintetis. **Belum bisa 100% karena saya belum pernah melihat contoh ekspor Google Forms asli Anda** — bisa saja kolom asli punya nama/urutan/format tanggal sedikit berbeda dari asumsi di kode. Lihat "Yang saya butuhkan dari Anda" di bawah. |
| **P0-02** — Grain pengukuran tekanan darah | Satu baris hanya mewakili satu partisipan-satu tanggal; tidak menampung sesi pagi/malam atau dua pembacaan per sesi. | Grain baru `partisipan_id + tanggal + sesi` diterapkan di `backend/app/models.py`. Satu sesi menyimpan 4 nilai mentah (SBP1/DBP1/SBP2/DBP2) terpisah; rata-rata sesi dihitung hanya jika pasangan bernomor sama lengkap; pasangan silang/parsial ditandai `pending_review`, tidak dihapus dan tidak dipaksa jadi rata-rata palsu. Saya jalankan ulang 73 test (termasuk kasus pasangan silang dan SBP≤DBP) pada SQLite **dan** PostgreSQL asli: semua lulus. | **SELESAI secara teknis. BUTUH KEPUTUSAN DOSEN** untuk satu hal saja: jumlah pembacaan minimum yang dianggap "sesi valid" untuk keperluan skripsi/laporan akhir (kode saat ini tidak memaksakan angka ini, dan sengaja tidak boleh saya tentukan sendiri). |
| **P0-03** — Pemisahan atribut profil vs harian | `jam_tidur`, `tingkat_stres`, `merokok`, `pola_makan` diperlakukan sebagai atribut tetap satu orang. | Profil (demografi, tinggi/berat, lokasi) dan perilaku harian kini disimpan di tabel/dimensi terpisah; tidak ada lagi aturan "harus konsisten antarhari". | **SELESAI.** |
| **P0-04** — Satuan jam tidur | Data sintetis lama pakai pecahan hari (0,20–0,39), bukan jam. | Jam tidur disimpan sebagai angka jam asli (`7.5` = 7,5 jam) pada fixture sintetis yang baru; label di dashboard sudah menampilkan satuan jam. | **SELESAI untuk data sintetis. BUTUH KEPUTUSAN** untuk data **aktual**: formulir asli Anda mungkin menanyakan tidur dengan cara lain (jam mulai–jam bangun, bukan durasi). Kode **sengaja menahan nilai sebagai NA + flag** untuk data aktual sampai format pertanyaan dikonfirmasi — ini mencegah saya "menebak" makna jawaban orang, sesuai larangan di instruksi Anda. |
| **P0-05** — Validasi ID responden | Sistem bisa membuat ID baru otomatis kalau ID tidak ditemukan. | ID wajib berasal dari formulir; baris tanpa ID ditolak/dikarantina; tidak ada pembuatan ID otomatis. Saya jalankan ulang test kasus ID kosong dan ID tidak cocok: lulus. | **SELESAI.** |
| **P0-06** — Skema lokasi & pola konsumsi | Backend lama meminta `kecamatan` dan satu kolom `pola_makan` umum yang tidak sesuai formulir. | Jalur kode yang aktif dipakai (`main.py`, `App.jsx`) memakai provinsi, kabupaten/kota, dan variabel konsumsi terpisah (asin/buah/sayur/kafein) — saya cek langsung lewat `/api/meta` dan memang tidak ada field kecamatan. | **SELESAI pada jalur aktif.** *Catatan jujur:* ada file lama (`service.py`, `OtherPages.jsx`, dll.) yang masih menyebut `kecamatan` — tapi saya pastikan file-file itu **tidak pernah dipanggil** oleh aplikasi yang berjalan, jadi bukan bug aktif, hanya kode lama yang belum dibersihkan. Beri tahu saya jika Anda ingin saya hapus file-file itu sekalian supaya repo lebih rapi. |
| **P0-07** — Target prediksi | UI/endpoint lama mengarah ke klasifikasi "diagnosis hipertensi"; seharusnya regresi `future_7d_mean_sbp`. | Halaman Prediksi & Evaluasi sekarang menampilkan angka mmHg (bukan kelas/label diagnosis), metrik regresi (MAE/RMSE/R²), dan secara eksplisit field `target_approved:false`. Saya tes langsung endpointnya: hasilnya numerik dan non-diagnosis, sesuai yang diminta. | **SELESAI secara teknis. BUTUH KEPUTUSAN DOSEN** — ini target usulan, bukan final. Statusnya akan **tetap** `false` sampai Anda bilang dosen sudah setuju. |

## Bagian B — Status Prioritas P1 (kualitas analisis & konsistensi fitur)

| ID | Masalah sebelumnya | Perbaikan yang sudah diterapkan dan diverifikasi | Status akhir |
|---|---|---|---|
| **P1-01** — Skala stres | Backend lama pakai 0–10; formulir pakai 1–5. | Integer 1–5 eksplisit; nilai di luar rentang jadi NA+flag. | **SELESAI.** |
| **P1-02** — Panjang kolom merokok | Kolom terlalu pendek untuk opsi "Tidak berlaku karena saya tidak merokok". | Kategori panjang penuh diterima; missing tidak disamakan dengan "tidak merokok". | **SELESAI.** |
| **P1-03** — Agregasi variabel harian | Pakai `first` untuk semua variabel, termasuk yang berubah tiap hari. | Agregasi dipilih sesuai jenis variabel (mean/median/count); BP dirata-rata di level sesi dulu sebelum digabung ke ringkasan harian. | **SELESAI pada jalur aktif.** |
| **P1-04** — Upload, missing value, CRUD | Satu file bisa mengganti seluruh dataset aktif; audit minim. | Impor profil & harian dipisah; mode dry-run default; commit butuh konfirmasi hash eksplisit; dicatat diterima/ditolak/dikarantina + alasan; tidak ada endpoint upload publik di API (hanya baca). | **SELESAI.** |
| **P1-05** — Perhitungan BMI | Backend minta BMI langsung, padahal formulir cuma kumpulkan tinggi/berat. | BMI dihitung otomatis dari `berat_kg / (tinggi_cm/100)²`; tinggi/berat asli tetap tersimpan; BMI tidak dihitung kalau input tidak valid. | **SELESAI.** |
| **P1-06** — Visualisasi faktor risiko | Grafik pakai kategori umum yang tidak sesuai formulir. | Grafik di jalur aktif memakai variabel aktual (asin, buah, sayur, kafein, stres 1–5, merokok, aktivitas, tidur), dengan jumlah sampel dan missing dijelaskan. | **SELESAI pada jalur aktif.** |
| **P1-07** — Konsistensi klasifikasi BP | Aturan klasifikasi tersebar di banyak tempat, berisiko tidak konsisten. | Satu modul pusat (`bp_policy.py`) dipakai bersama oleh ETL, API, dan model; jalur aktif tidak menghitung "kelas hipertensi" sama sekali, hanya angka mmHg + peringatan non-diagnosis. | **SELESAI untuk konsistensi teknis.** Kalau nanti Anda/dosen ingin menambahkan kategori (normal/tinggi/dst.) untuk visualisasi, aturan ambangnya **harus disetujui dulu** sebelum saya kodekan — ini memang pending by design, bukan kelupaan. |
| **P1-08** — Audit kualitas data | Belum ada laporan kualitas data (duplikasi, outlier, missing, konflik) sebelum/sesudah ETL. | Konflik multi-versi dikarantina (tidak otomatis pilih data pertama/terakhir); outlier ditandai (metode IQR) tanpa dihapus otomatis; laporan kualitas mencatat diterima/ditolak/alasan/missing/duplikasi/cakupan ID. | **SELESAI secara teknis. BUTUH KEPUTUSAN DOSEN** — soal apa yang dilakukan terhadap anomali **data aktual** nantinya (dikoreksi? dikeluarkan? ditandai saja?) adalah keputusan metodologi penelitian, bukan sesuatu yang boleh saya putuskan sendiri. |

---

## Bagian C — Yang masih butuh keputusan Anda (bukan sesuatu yang bisa saya "selesaikan" sendiri)

Saya ingin jujur di sini: kalau saya memaksakan status "SELESAI" pada 5 item di bawah tanpa info tambahan dari Anda, itu artinya saya **mengarang keputusan akademik atau menebak format data** yang justru dilarang tegas di instruksi awal Anda ("Jangan membuat persetujuan dosen atau izin penelitian fiktif", "Jangan otomatis menganggap angka dari formulir aktual sebagai jam..."). Jadi berikut persisnya apa yang saya butuhkan dari Anda untuk tiap item — begitu Anda kasih jawabannya, saya bisa langsung kodekan:

1. **P0-01 (kontrak data dua sumber):** Kirimkan **satu contoh ekspor CSV/XLSX asli** dari Google Forms profil awal dan catatan harian (boleh dikosongkan/disamarkan datanya, yang penting **struktur kolom dan nama header**-nya asli). Saya akan cocokkan ke kontrak yang ada dan perbaiki kalau ada perbedaan nama/urutan kolom.
2. **P0-02 (protokol pembacaan BP):** Berapa jumlah pembacaan minimum per sesi yang dianggap sah untuk laporan Anda — 1 pasang cukup, atau wajib 2 pasang? Ini keputusan protokol penelitian dari dosen.
3. **P0-04 (semantik jam tidur aktual):** Bagaimana persis pertanyaan tidur di formulir asli ditanyakan — "berapa jam Anda tidur semalam" (angka langsung) atau "jam berapa tidur – jam berapa bangun" (perlu dihitung selisihnya)?
4. **P0-07 (persetujuan target model):** Apakah dosen sudah menyetujui `future_7d_mean_sbp` sebagai target resmi? Kalau sudah, saya ubah `target_approved` jadi `true` dan buka klaim hasil model sebagai "hasil eksperimen resmi" (bukan hanya demo teknis).
5. **P1-08 (aturan anomali data aktual):** Untuk data aktual nanti, outlier/duplikat/konflik mau dikarantina+ditinjau manual terus (seperti sekarang), atau ada aturan koreksi otomatis yang disetujui dosen?

Begitu Anda jawab salah satu atau semua poin di atas, kirim saja ke saya dan saya langsung terapkan ke kode — tidak perlu menunggu siklus perbaikan besar lagi.

---

## Bagian D — Panduan instalasi: apa yang perlu Anda download/install

Repository ini dipakai dengan dua jalur: **(1) jalur resmi via Docker** (paling gampang, dipakai untuk demo ke dosen) dan **(2) jalur development tanpa Docker** (untuk Anda ngoding/ngetes sendiri di komputer, seperti yang saya lakukan untuk verifikasi kemarin). Anda tidak wajib install keduanya — pilih sesuai kebutuhan.

### D.1 — Yang wajib diinstal untuk jalur resmi (Docker) — **paling direkomendasikan**

| Yang diinstal | Versi | Link unduh |
|---|---|---|
| Docker Desktop | versi terbaru | https://www.docker.com/products/docker-desktop/ |

Itu saja. PostgreSQL, backend Python, dan frontend akan berjalan otomatis **di dalam container** — Anda tidak perlu install Python/Node/PostgreSQL secara manual untuk jalur ini.

**Langkah menjalankan:**
```powershell
# dari folder root project
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
# PENTING: buka .env, ganti POSTGRES_PASSWORD dari "change-me-local-only" ke password sendiri
# sebelum pertama kali membuat volume database baru

docker compose up --build -d
docker compose ps
```
- Frontend: http://localhost:8080
- Swagger API: http://localhost:8080/api/docs
- Matikan tanpa menghapus data: `docker compose down` (**JANGAN** pakai `docker compose down -v`, itu menghapus seluruh data PostgreSQL).

### D.2 — Yang perlu diinstal untuk jalur development/testing tanpa Docker

Ini jalur yang saya pakai sendiri untuk memverifikasi kemarin. Perlu tiga hal:

#### 1) Python

| Yang diinstal | Versi | Catatan |
|---|---|---|
| Python | **3.12 atau 3.13** | Proyek ini dikembangkan dan diuji di kedua versi. Image Docker resmi pakai `python:3.12-slim`. Unduh di https://www.python.org/downloads/ |

Setelah Python terinstal, dari folder root project:
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r backend/requirements-dev.txt
```

**Catatan penting soal reproducibility** (saya temukan sendiri waktu verifikasi): kalau Anda ingin hasil model (`run_id`, hash artefak) **persis sama** dengan yang sudah diaudit — misalnya untuk keperluan verifikasi ulang baseline ML — pakai file pin versi eksak, bukan `requirements-dev.txt` biasa:
```powershell
pip install -r backend/requirements-cp3.txt
```
File ini mengunci `numpy==2.5.4`, `pandas==3.0.6`, `scikit-learn==1.9.1`, `joblib==1.6.0`, `scipy==1.18.1` — versi persis yang dipakai saat artefak `models/baseline_metrics.json` resmi dibuat. Kalau pakai `requirements-dev.txt` biasa, pip akan mengambil versi pandas terbaru yang tersedia saat itu (bisa beda), dan **angka metrik tetap sama persis**, tapi `run_id`/fingerprint-nya akan berbeda karena provenance ikut mencatat versi library. Ini bukan bug — ini memang desain untuk mendeteksi perbedaan lingkungan, hanya perlu diketahui supaya tidak bingung.

#### 2) Node.js

| Yang diinstal | Versi | Catatan |
|---|---|---|
| Node.js | **v22 (LTS)** | Image Docker resmi pakai `node:22-alpine`. Unduh di https://nodejs.org/ |

```powershell
cd frontend
npm install
npm test        # jalankan test
npm run build    # build production
npm run dev      # jalankan mode development, buka http://localhost:5173
```

#### 3) PostgreSQL (hanya jika Anda ingin jalankan backend/test **tanpa** Docker)

Kalau Anda sudah pakai jalur D.1 (Docker), **lewati bagian ini** — PostgreSQL sudah otomatis jalan di dalam container.

Kalau Anda ingin menjalankan backend langsung di komputer (bukan di container) atau menjalankan test integrasi PostgreSQL (`pytest`), Anda perlu PostgreSQL terinstal secara native:

| Yang diinstal | Versi | Link unduh |
|---|---|---|
| PostgreSQL | **16** (sesuai `postgres:16-alpine` yang dipakai Docker Compose) | https://www.postgresql.org/download/ (Windows: installer EDB; bisa juga lewat `choco install postgresql16` kalau pakai Chocolatey) |

**Setelah PostgreSQL 16 terinstal**, buat database sesuai yang dipakai `compose.yaml` (kalau mau backend lokal terhubung ke setup yang identik dengan Docker):
```sql
CREATE USER toba WITH PASSWORD 'password_pilihan_anda';
CREATE DATABASE toba_health OWNER toba;
```
Lalu set environment variable sebelum menjalankan backend:
```powershell
$env:DATABASE_URL = "postgresql+psycopg://toba:password_pilihan_anda@127.0.0.1:5432/toba_health"
cd backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

**Khusus untuk menjalankan test suite PostgreSQL** (`pytest backend/tests`), proyek ini **sengaja mewajibkan** nama database persis `toba_cp2_test` di `127.0.0.1`/`localhost` — ini pagar keamanan supaya test tidak bisa tidak sengaja menyentuh database aktif:
```sql
CREATE DATABASE toba_cp2_test OWNER toba;
```
```powershell
$env:CP2_TEST_DATABASE_URL = "postgresql+psycopg://toba:password_pilihan_anda@127.0.0.1:5432/toba_cp2_test"
.\.venv\Scripts\python.exe -m pytest backend/tests -q -p no:cacheprovider
```
Kalau `CP2_TEST_DATABASE_URL` tidak diset sama sekali, test tetap jalan otomatis pakai **SQLite in-memory** (tidak perlu install apa pun) — jadi PostgreSQL native ini sifatnya opsional, hanya untuk memastikan kode juga benar di PostgreSQL sungguhan, bukan cuma SQLite.

### D.3 — Ringkasan cepat: apa yang baru perlu Anda download dibanding sebelumnya?

Tidak ada dependency BARU yang ditambahkan oleh perbaikan P0/P1 ini — semua perbaikan memakai library yang sudah ada di `backend/requirements.txt` dan `frontend/package.json` sebelumnya. Jadi kalau project Anda sebelumnya sudah bisa jalan dengan Docker, **Anda tidak perlu install apa pun yang baru** untuk memakai hasil perbaikan ini — cukup `docker compose up --build -d` seperti biasa supaya image di-build ulang dengan kode terbaru.

Yang perlu diinstal **hanya kalau Anda belum punya sebelumnya**:
- Docker Desktop (jalur resmi), ATAU
- Python 3.12/3.13 + Node.js 22 + (opsional) PostgreSQL 16 native (jalur development manual seperti yang saya pakai untuk verifikasi).
