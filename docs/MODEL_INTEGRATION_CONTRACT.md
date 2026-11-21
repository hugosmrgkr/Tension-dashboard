# Draf kontrak integrasi data model dan dashboard

Project: **Toba Health Insight**  
Penanggung jawab draf: **Hugo**  
Tahap: **1 dari 4 pekerjaan integrasi Hugo**  
Tanggal pemeriksaan: **17 November 2026**  
Versi dokumen: **0.1 draft**  
Basis kode lokal: **`e956bb7`**

**Status: DRAF UNTUK REVIEW.** Dokumen ini belum menjadi kesepakatan Aldi/Nahesson.
Tahap 1 hanya menyusun dokumen. Implementasi terbatas Tahap 2 yang kemudian
dikonfirmasi Hugo dicatat pada bagian 14; usulan rilis/aktual lainnya belum diaktifkan.

## 1 Tujuan dalam bahasa sederhana

Kontrak ini menyepakati tiga hal:

1. **Aldi menyediakan data beserta identitas versi dan status kualitasnya.**
2. **Nahesson menyediakan model beserta fitur, hasil evaluasi dan manifest rilisnya.**
3. **Hugo memastikan API dan React memakai pasangan data/model yang sesuai**, atau
   menampilkan alasan yang jelas ketika prediksi belum dapat diberikan.

Dokumen mengacu pada implementasi yang ada dan memberi usulan tambahan minimal.
Label **SUDAH ADA** berarti diperiksa pada source/artefak, bukan diuji ulang hari ini.
Label **USULAN** berarti masih perlu review dan implementasi pada tahap selanjutnya.

## 2 Batas pekerjaan dan pemilik

| Bagian | Pemilik | Yang diserahkan untuk integrasi |
|---|---|---|
| Formulir, cleaning, quality gate dan warehouse | Aldi | Kontrak kolom/grain, metadata batch, laporan kualitas dan kelayakan riwayat |
| Eksperimen, fitur dan rilis model | Nahesson | Artefak terverifikasi, manifest, definisi fitur/target dan metrik berscope jelas |
| Loader, otorisasi, API dan halaman Prediksi | Hugo | Pemeriksaan kompatibilitas, respons yang konsisten dan visualisasi hasil |
| Staging, backup/restore dan pengujian deployment | Ruben | Bukti alur integrasi pada lingkungan terisolasi dan deployment |
| Konsistensi hasil dan naskah | Kasih | Tabel/gambar/narasi yang menyebut sumber, versi dan batas hasil secara tepat |

Tahap 1 hanya menyusun draf. Tahap 2 adalah loader dan pemeriksaan kompatibilitas;
Tahap 3 adalah visualisasi Prediksi; Tahap 4 adalah tes integrasi/bukti penerimaan.
**Setiap tahap berikutnya menunggu konfirmasi Hugo melalui percakapan.** Konfirmasi
Hugo untuk melanjutkan bukan bukti bahwa Aldi/Nahesson atau dosen sudah menyetujui
seluruh isi kontrak.

## 3 Kondisi kode yang sudah ada

| Area | SUDAH ADA | Yang belum diselesaikan |
|---|---|---|
| Metadata sumber | `/api/meta` memberi `source_kind`, `data_version`, tanggal dan jumlah data | Belum ada versi schema fitur dan status kelayakan integrasi yang eksplisit |
| Akses aktual | Sumber non-sintetis dibatasi oleh `source_summary` dan endpoint | Token yang valid saat ini tidak otomatis membuka sumber aktual |
| Artefak serving | `models/experiments/comparison_manifest.json` dan metrik/model P2 | Belum ada registry/pemilihan rilis baru |
| Integritas | Hash teks UTF-8/LF dan hash binary joblib; nama fitur diperiksa loader | Aturan sumber dan kontrak rilis perlu dipertegas |
| Prediksi | `GET /api/model/predict`, ID dan `asof_date`, hasil mmHg, naif dan metadata | Endpoint khusus sintetis; belum menggunakan paket rilis aktual |
| React | Input ID, pembatalan request, hasil angka, metadata dan penanganan error | Grafik riwayat/estimasi serta status sumber/rilis baru belum dibuat |

`models/tuning_week10/` adalah eksperimen terpisah. Jangan menyalin model tuning
ke folder serving atau mengganti metrik P2 hanya agar tampilan terlihat terbaru.

## 4 Definisi data fitur dan target

### 4.1 Grain dan waktu

- Profil: satu ID responden pseudonim.
- Perilaku harian: satu ID-tanggal.
- Sesi tekanan darah: satu ID-tanggal-sesi Pagi/Malam, dengan dua pembacaan menurut
  kontrak CP2 dan gate pasangan BP yang berlaku.
- Origin `t`: akhir hari pengamatan yang dipilih; bukan tanggal komputer atau
  timestamp pengiriman formulir.
- Histori: `t-6` sampai `t`, tujuh hari kalender berturut-turut dengan SBP harian
  yang tersedia sesuai pipeline saat ini.
- Target: `future_7d_mean_sbp`, rerata SBP harian `t+1` sampai `t+7`, satuan mmHg.
- SBP harian berasal dari rerata sesi yang lolos kebijakan BP; rerata target memakai
  bobot hari yang sama. Rincian gate mengikuti kode/dictionary, tidak ditetapkan ulang di sini.

**Penting:** inferensi membutuhkan histori tujuh hari; tidak membutuhkan tujuh hari
masa depan. Training/evaluasi membutuhkan keduanya agar nilai target diketahui.
Missing target tidak diimputasi. Batas klinis, aturan tidur aktual, inklusi dan
koreksi anomali tetap memerlukan keputusan yang dicatat oleh pemiliknya.

Untuk perencanaan, target dianggap sesuai mengikuti instruksi Hugo sebelumnya.
Artefak yang diperiksa masih memuat `target_approved=false`; draf ini tidak mengubah
flag itu. Perubahan status persetujuan rilis baru harus memiliki catatan keputusan
yang nyata, bukan disimpulkan dari nama file atau percakapan asumsi.

### 4.2 Urutan fitur yang sedang dipakai

| Urutan | Nama fitur | Makna dan satuan |
|---|---|---|
| 1 | `past_7d_sbp` | Rerata SBP harian dalam histori, mmHg |
| 2 | `past_7d_dbp` | Rerata DBP harian dalam histori, mmHg |
| 3 | `past_7d_sbp_std` | Standar deviasi SBP harian histori, `ddof=0`, mmHg |
| 4 | `age` | Usia dari profil, tahun |
| 5 | `bmi` | BMI turunan tinggi/berat, kg/m2 |
| 6 | `past_7d_activity` | Rerata menit aktivitas harian yang tersedia |
| 7 | `past_7d_sleep` | Rerata durasi tidur harian yang tersedia, jam |
| 8 | `past_7d_stress` | Rerata stres harian yang tersedia, skala jawaban 1-5 |

SUDAH ADA: missing fitur direpresentasikan kosong dan diimputasi pipeline model
dengan statistik training; fitur yang diimputasi/di luar rentang dilaporkan.
**USULAN:** tandai kontrak ini dengan `feature_schema_version=cp3-history7-v1`.
Nama versi belum diimplementasikan. Mengubah nama, urutan, unit, agregasi atau
penanganan missing harus menghasilkan versi fitur baru dan uji paritas ulang.

Profil statis saat ini diasumsikan diketahui pada origin. Jika data aktual berisi
profil terlambat masuk/berubah, Aldi dan Nahesson perlu menetapkan kebijakan
ketersediaannya agar tidak memakai informasi masa depan.

## 5 Kontrak metadata dataset untuk Aldi dan Hugo

Field tambahan berikut adalah **USULAN**, bukan kolom database baru atau respons
yang sudah tersedia. Implementasi nanti sebaiknya menambah metadata melalui adapter,
tanpa merombak schema warehouse bila tidak diperlukan.

| Field | Kondisi sekarang atau usulan | Ketentuan |
|---|---|---|
| `source_kind` | SUDAH ADA | `synthetic`/`actual`; `empty`/`unknown` harus ditangani aman |
| `data_version` | SUDAH ADA | Fingerprint prepared batch pada kualitas ETL; jangan ganti dengan nomor buatan |
| `min_date`, `max_date` | SUDAH ADA | Cakupan tanggal pengamatan, bukan waktu impor |
| `participants`, `daily_records`, `session_records` | SUDAH ADA | Jumlah sesuai grain; sumber terbatas tidak mengekspos detail tanpa izin |
| `etl_audit_version` | SUDAH ADA | Versi audit ETL yang menghasilkan batch |
| `access_restricted` | SUDAH ADA | React menghormati pembatasan; tidak digunakan sebagai pengganti pemeriksaan server |
| `dataset_schema_version` | USULAN | Versi kontrak kolom/unit/grain yang disepakati |
| `feature_schema_version` | USULAN | Kompatibilitas dengan kontrak fitur model |
| `quality_status` | USULAN | `passed`, `pending_review`, `failed`, `unknown`; arti setiap status disepakati Aldi |
| `eligibility` | USULAN | Ringkasan bisa/tidak bisa dianalisis/diprediksi beserta alasan; bukan satu flag global untuk semua ID |
| `imported_at` | USULAN | Waktu impor jika ada bukti; null bila belum tercatat. Jangan memakai tanggal pengamatan sebagai waktu impor |

Sumber sintetis dan aktual tidak digabungkan. Metadata/profil tidak memuat nama,
kontak, alamat rinci atau identitas langsung. Kelayakan setiap ID/origin tetap
diperiksa server saat prediksi; status kualitas batch saja tidak menjamin histori lengkap.

## 6 Kontrak paket rilis untuk Nahesson dan Hugo

### 6.1 Isi paket yang diusulkan

Lokasi usulan: `models/releases/<release_id>/`. Lokasi ini belum dibuat/diaktifkan.
Paket minimal berisi model pipeline, metrik, manifest dan model card. Nama file
boleh disepakati, tetapi loader tidak boleh menebak atau memilih file terbaru sendiri.

| Metadata rilis | Persyaratan draf |
|---|---|
| `contract_version`, `release_id`, `run_id` | Versi schema rilis, identitas rilis dan eksperimen; jangan mengubah arti `schema_version` artefak lama |
| `source_kind` | Sumber training dinyatakan eksplisit; bukan ditebak dari ID/file |
| `training_data_version` | Fingerprint batch training; terpisah dari batch inferensi aktif |
| `dataset_schema_version`, `feature_schema_version` | Kompatibilitas yang disepakati dengan Aldi/Hugo |
| `target`, `history_days`, `horizon_days` | Target/riwayat/horizon eksplisit dan cocok dengan rumus server |
| `features` | Daftar berurutan; sama dengan model dan adapter inferensi |
| `algorithm`, `trained_on` | Algoritma dan waktu training yang benar-benar tercatat; jangan mengarang waktu dari `as_of` |
| `model_file`, `model_sha256` | File di dalam folder rilis dan hash byte persis |
| `metrics_file`, `metrics_sha256`, `metrics_hash_mode` | File metrik terverifikasi; teks memakai normalisasi UTF-8 LF yang sama pada Windows/Linux |
| `metrics_scope`, `selection`, `sample_sizes` | Validasi/test/historis/aktual, aturan pemilihan dan jumlah ID/window dinyatakan jelas |
| `target_approval`, `release_status` | Bukti/status review; usulan status rilis `candidate`/`approved`/`blocked` |
| `feature_ranges`, `limitations` | Rentang training dan batas penggunaan/kelayakan yang bisa ditampilkan |
| `versions` | Versi dependency numerik/model untuk pemeriksaan kompatibilitas |

**USULAN pemilihan rilis:** daftar/path rilis yang diizinkan dipilih eksplisit oleh
pengelola, lalu divalidasi server. Tidak ada promosi otomatis karena skor lebih baik,
timestamp terbaru, atau nama file mengandung kata `final`. Hash membuktikan konsistensi
file, bukan kepercayaan penerbit; joblib hanya dimuat dari paket tim yang dipercaya.
Path manifest harus dibatasi pada folder rilis, tanpa traversal ke file lain.

Rilis aktual tidak boleh dibuat dengan mengganti label model sintetis. Kebutuhan
minimal sampel dan protokol validasi aktual adalah keputusan Nahesson/tim, bukan
angka baru yang ditentukan draf integrasi ini.

### 6.2 Contoh nyata sumber sintetis yang sudah tersedia

Ringkasan ini disalin dari artefak P2 di repository; **bukan manifest rilis baru**,
respons API live, training baru atau hasil penelitian aktual:

```json
{
  "source_kind": "synthetic",
  "run_id": "d43ac5c17c70cead67c7",
  "selected_model": "Linear Regression",
  "target": "future_7d_mean_sbp",
  "model_file": "linear_regression_synthetic.joblib",
  "metrics_hash_mode": "utf8-lf-v1",
  "rows_training": 60,
  "rows_test": 7,
  "target_approved": false,
  "beats_naive_on_validation": false
}
```

Nilai metrik tersimpan LR: MAE validasi sekitar 2,180, RMSE validasi 2,759;
MAE test historis sekitar 2,575 dan RMSE 3,114 mmHg. R2 test sekitar 0,709.
Test lama sudah pernah diperiksa, bukan holdout baru. Inner validasi memisahkan ID,
tetapi kalender dapat beririsan. Jangan menyebut nilai ini akurasi persen atau bukti klinis.
Field `as_of=2026-11-10` ada pada artefak; itu tidak membuktikan waktu training presisi.

## 7 Pemeriksaan kompatibilitas sebelum prediksi

Tabel berikut adalah **USULAN perilaku loader baru**; pengaman yang sudah ada tetap
berlaku sampai perubahan berikutnya diimplementasikan dan diuji.

| Pemeriksaan | Hasil bila tidak cocok |
|---|---|
| Autentikasi/otorisasi dan izin penggunaan dataset | Tolak akses; jangan memuat/menampilkan data aktual |
| Rilis dipilih eksplisit, dipercaya dan lolos review yang disyaratkan | Prediksi tidak tersedia; jangan fallback diam-diam ke rilis lain |
| Hash model/metrik, schema dan path manifest | Tolak artefak; jangan mematikan pemeriksaan hash |
| Jenis sumber training dan inferensi | Sintetis ke aktual atau sebaliknya ditolak dalam jalur ini |
| Target, horizon, versi fitur dan urutan fitur model | Tolak kompatibilitas; perlu adapter/rilis yang disepakati dan dites |
| ID dan tanggal origin | Tolak ID tidak dikenal atau tanggal/riwayat yang tidak layak |
| Riwayat tujuh hari dan ketersediaan fitur | Terapkan aturan pipeline; jangan mengisi target/riwayat SBP palsu |
| Fitur diimputasi/di luar rentang training | Laporkan sesuai model; peringatan bukan alasan mengarang hasil atau memotong nilai |
| Prediksi tidak finite atau inferensi gagal | Kembalikan kegagalan, tanpa hasil contoh |

### Bila batch data bertambah

`training_data_version` dan `data_version` inferensi tidak harus selalu identik.
Contohnya, dataset dapat bertambah hari pengamatan setelah model dilatih. Perbedaan
fingerprint **tidak otomatis berarti model salah**, tetapi juga tidak boleh diabaikan.

**USULAN konservatif untuk direview:** batch berbeda hanya dapat dipakai bila jenis
sumber, schema/fitur, quality/eligibility dan kebijakan penggunaan tetap cocok. API
melaporkan kedua versi, `batch_match=false` dan peringatan; metrik tetap milik batch
training/evaluasi tersimpan, bukan evaluasi ulang data aktif. Perubahan sumber/unit/
schema, quality yang belum diketahui atau kebijakan yang belum disetujui harus
memblokir prediksi. Perubahan distribusi besar perlu review model, bukan retraining otomatis.

## 8 Kontrak API dan kompatibilitas React

### 8.1 Endpoint yang dipertahankan

| Endpoint saat ini | Fungsi | Ketentuan draf |
|---|---|---|
| `GET /api/meta` | Metadata dataset/filter | Pertahankan field lama; tambahan metadata bersifat additive |
| `GET /api/analytics` | Analitik PostgreSQL sesuai filter | Tidak berubah menjadi endpoint training/inferensi |
| `GET /api/model/comparison` | Metrik eksperimen tersimpan | Tambahkan asal rilis/scope di adapter nanti; jangan mengisi hasil palsu |
| `GET /api/model/predict` | Inferensi satu ID dan origin | Pertahankan ID, `asof_date` dan field hasil lama |
| `/api/model/baseline`, `/api/model/predict-baseline` | Kompatibilitas baseline CP3 | Pertahankan sebagai jalur historis yang jelas, tidak disulap menjadi hasil aktual |

Request yang sudah didukung:

```http
GET /api/model/predict?respondent_id=SIM001&asof_date=2026-09-30
```

Ini contoh format request sintetis, **bukan bukti request berhasil dijalankan**.
Jika `asof_date` tidak dikirim, server saat ini memakai tanggal terakhir dengan SBP
yang tersedia untuk ID. Jika dikirim, tanggal itu harus mempunyai pengamatan yang
layak; tidak boleh diam-diam bergeser ke tanggal lain.

Prediksi adalah lingkup ID/origin yang dipilih, bukan rerata kelompok filter global.
Metrik eksperimen tidak dihitung ulang oleh filter. Aturan ini harus dijelaskan UI;
filter analitik tidak otomatis mengubah model atau target.

### 8.2 Respons sukses

Field yang **SUDAH ADA** harus dipertahankan: `respondent_id`, `last_date`,
`history_start`, `forecast_start`, `forecast_end`, `prediction_mmHg`,
`reference_naive_mmHg`, `features_used`, `features_imputed`,
`features_out_of_range`, `notes`, `model`, `is_synthetic`, `is_diagnosis`,
`target_approved` dan `status`.

`model` saat ini menyertakan algoritma, versi/run, target/horizon, urutan fitur,
asal data, hash dan status terhadap baseline. Adapter rilis baru harus menjaga
makna field; misalnya jangan mengganti `model.version` menjadi versi dataset.

**USULAN tambahan:** `contract_version`, `source_kind`, `data_version`,
`training_data_version`, `feature_schema_version`, `batch_match`, `metrics_scope`,
`release_status`, serta informasi riwayat yang berizin untuk grafik. Tentukan apakah
riwayat dimuat lewat analitik yang sudah ada atau endpoint khusus sebelum implementasi;
jangan menambah endpoint yang menduplikasi data tanpa kebutuhan.

### 8.3 Respons gagal

| Kondisi | HTTP saat ini | Usulan kode stabil tambahan |
|---|---|---|
| Token tidak ada/tidak valid pada mode token | 401 | `AUTH_REQUIRED` |
| Tidak berwenang/sumber aktual masih dibatasi | 403 atau guard sumber prediksi 409 | `ACCESS_DENIED` atau `SOURCE_RESTRICTED`, diselaraskan saat implementasi |
| ID tidak tersedia/tidak memiliki BP valid | 404 | `RESPONDENT_UNAVAILABLE` |
| Artefak belum tersedia/rusak/fitur tidak cocok | 409 | `MODEL_UNAVAILABLE` atau `MODEL_INCOMPATIBLE` |
| Query/tanggal invalid atau riwayat tidak cukup | 422 | `INVALID_INPUT` atau `INSUFFICIENT_HISTORY` |
| Rate limit | 429 | `RATE_LIMITED` |
| Inferensi gagal/hasil tidak finite | 503 | `PREDICTION_FAILED` |

Pertahankan pesan `detail` yang dapat dibaca helper API sekarang. Kode mesin di atas
baru usulan field tambahan `error_code`, bukan bentuk respons yang sudah berjalan.
FastAPI dapat memberi `detail` berupa daftar error validasi; adapter tidak boleh
merusak penanganan yang sudah tersedia. Jangan kirim stack trace, token, kredensial
atau path sensitif kepada pengguna.

Endpoint metadata model saat ini dapat mengembalikan HTTP 200 dengan `available=false`.
Itu tetap status tidak tersedia, bukan respons prediksi sukses. Prediksi gagal tidak
boleh mengembalikan angka `0`, angka contoh, atau rilis fallback tanpa penjelasan.

## 9 Otorisasi dan batas data aktual

SUDAH ADA: token Bearer, peran viewer/admin, rate limit dan pagar staging/production.
Token React disimpan per tab melalui `sessionStorage`. Detail kualitas dan ekspor
memerlukan admin pada mode token. Sumber aktual tetap dibatasi walau token valid.

**USULAN untuk review:** akses aktual memerlukan mode token yang aman, izin dataset
yang tercatat dan pemeriksaan role pada server. Viewer hanya memperoleh analitik/
prediksi pseudonim sesuai izin; admin mendapat fungsi tambahan yang disetujui.
Jangan menambah akses aktual anonim hanya karena berjalan di development.

Kebijakan ini perlu dikonfirmasi Aldi/tim dan diuji pada tahap implementasi. Dokumen
ini tidak membuka endpoint aktual, tidak menerbitkan data dan tidak mengubah `.env`.

## 10 Ketentuan visual halaman Prediksi

- Tampilkan ID pseudonim dan origin yang sedang digunakan, bukan identitas pribadi.
- Grafik riwayat menunjukkan SBP/DBP dalam mmHg dari pengamatan yang layak; missing
  tidak diisi nol. Jelaskan apakah data merupakan sesi atau rerata harian.
- Output model adalah **satu estimasi rerata SBP untuk rentang tujuh hari**.
  Tampilkan sebagai ringkasan/elemen rentang berlabel, bukan tujuh titik harian palsu.
- Tampilkan pembanding rerata SBP tujuh hari histori, versi/rilis model, sumber,
  periode estimasi dan peringatan fitur/imputasi yang relevan.
- Bedakan riwayat dan estimasi secara visual; jangan membuat prediksi DBP karena
  model saat ini hanya menargetkan SBP.
- Jangan menggambar confidence interval tanpa metode dan artefak evaluasi yang mendukung.
- Saat ID/model/sumber berubah, hasil lama harus dibersihkan dan request usang dibatalkan.
  Pertahankan loading/error/empty state; tidak ada hasil sementara yang dibuat manual.
- Label sintetis berlaku bagi model/data sintetis; hasil aktual nantinya tetap
  menyebut batas penelitian dan bukan diagnosis. Jangan hardcode label aktual.

## 11 Rencana tes penerimaan untuk tahap berikutnya

Daftar ini **belum dijalankan untuk kontrak baru** dan bukan implementasi Tahap 1.

- [ ] Adapter artefak P2 mempertahankan prediksi, fitur dan metadata yang sama.
- [ ] Hash model/metrik rusak ditolak; LF/CRLF teks kompatibel, binary tetap ketat.
- [ ] Path manifest di luar rilis, sumber/fitur/horizon tidak cocok dan rilis tak
      disetujui gagal tertutup tanpa memuat file sembarang.
- [ ] Batch baru yang kompatibel mengikuti kebijakan eksplisit dan menampilkan dua
      provenance; batch dengan source/schema berubah tidak diterima diam-diam.
- [ ] ID/tanggal invalid, riwayat kurang, missing fitur dan hasil nonfinite ditangani.
- [ ] Autentikasi saja tidak melewati izin aktual; uji viewer/admin/anonim.
- [ ] Paritas feature engineering training/inferensi dan batas origin tetap terjaga.
- [ ] React menampilkan satu output rerata, tidak membuat deret prediksi palsu,
      membatalkan request usang dan membersihkan hasil ketika konteks berubah.
- [ ] Metrik/sumber/versi pada API, React dan laporan konsisten; filter tidak melatih model.
- [ ] Frontend tests/build, backend tests terkait dan browser bila lingkungan mendukung.

## 12 Review dan keputusan yang belum selesai

| Review | Penanggung jawab | Status |
|---|---|---|
| Metadata schema/batch, status quality/eligibility dan waktu impor | Aldi | PENDING REVIEW |
| Format manifest/fitur, scope metrik dan paket rilis | Nahesson | PENDING REVIEW |
| Kebijakan batch inferensi berbeda, izin aktual dan model rilis | Hugo bersama Aldi/Nahesson | PENDING REVIEW |
| Bukti keputusan target/protokol ilmiah yang diperlukan | Tim/dosen melalui pemilik tugas | PENDING DOCUMENTATION |
| Draf Tahap 1 dipahami dan boleh dilanjutkan ke Tahap 2 | Hugo melalui percakapan | DIKONFIRMASI 17 November 2026; review tim tetap pending |

Jangan mengisi nama reviewer, tanggal persetujuan atau status approved secara
otomatis. Hugo dapat melanjutkan kerangka sintetis setelah mengonfirmasi tahap
berikutnya; itu tidak mengaktifkan data aktual atau menyatakan review tim selesai.

## 13 Pemeriksaan Tahap 1 dan sumber kode

Yang dilakukan: membaca source/artefak, mencocokkan nama field, urutan fitur,
status source guard, endpoint dan respons, lalu menyusun draf ini. Tidak menjalankan
ETL/training, tes aplikasi, build, request ke database atau perubahan runtime.

Sumber lokal:

- `backend/app/analytics_v2.py`: `source_summary`, `metadata_payload`, `frames`.
- `backend/app/main.py`: endpoint model, validasi request dan pemetaan HTTP error.
- `backend/app/model_service.py`: loader, `inference_features`, respons prediksi.
- `backend/app/baseline.py`: `FEATURES`, `TARGET`, `daily_bp`, `make_training`.
- `backend/app/model_comparison.py`: penulisan/pembacaan manifest P2.
- `backend/app/security.py`: token, role dan pagar konfigurasi.
- `frontend/src/App.jsx`, `lib/api.js`, `pages/PrediksiTekananDarah.jsx`.
- `models/experiments/comparison_metrics.json` dan `comparison_manifest.json`.
- [Tugas Hugo](TUGAS_HUGO.md), [laporan tuning](WEEK10_TUNING_REPORT.md),
  [batas evaluasi historis](WEEK10_EVALUATION_REPORT.md).

**Checkpoint awal:** penyusunan draf Tahap 1 selesai. Hugo kemudian mengonfirmasi
kelanjutan Tahap 2 pada percakapan 17 November 2026. Review Aldi/Nahesson tetap pending.

## 14 Catatan implementasi Tahap 2

Implementasi terbatas pada adapter `p2-comparison-v1` untuk artefak sintetis P2
yang sudah ada, bukan persetujuan seluruh format rilis baru pada dokumen ini.
Tidak ada aktivasi aktual, promosi model tuning, atau pembuatan grafik Tahap 3.

- `model_registry.py` membaca folder P2 yang dipilih konfigurasi; tidak memindai
  folder rilis atau memilih model terbaru secara otomatis.
- Nama/path model, manifest, hash teks/binary, sumber, fitur, target/horizon,
  provenance dan metadata metrik diverifikasi sebelum inferensi. Metadata evaluasi
  tidak mengeksekusi joblib; model dideserialisasi hanya untuk inferensi dari byte
  yang sudah diperiksa hash-nya.
- `feature_schema_version=cp3-history7-v1` adalah identitas adapter untuk kontrak
  fitur CP3 yang diketahui, bukan field yang diam-diam ditambahkan ke artefak lama.
- **Kebijakan sementara:** fingerprint diketahui berbeda diblokir dengan
  `DATASET_MISMATCH`. Kebijakan menerima pertambahan batch yang kompatibel pada
  bagian 7 tetap usulan yang perlu review. Tidak ada override otomatis.
- **Kompatibilitas legacy sintetis:** jika fingerprint tidak tercatat, respons
  diberi `batch_unverified`, `warehouse_batch_match=null` dan peringatan pada
  prediksi. Ini bukan bukti batch cocok dan tidak berlaku sebagai izin aktual.
- Data aktual/unknown/empty tetap ditolak adapter. Guard sumber aktual API tidak
  dihapus; status persetujuan target dan model aktif tidak diubah.
- `metrics_scope=synthetic_historical_test` menandai asal skor test tersimpan;
  tabel validasi tetap berisi skor OOF sintetis, bukan evaluasi ulang warehouse.

Laporan implementasi dan bukti tes: [HUGO_STAGE2_REPORT.md](HUGO_STAGE2_REPORT.md).
Tahap 3 tetap menunggu konfirmasi baru dari Hugo.

## 15 Catatan implementasi Tahap 3

Hugo kemudian mengonfirmasi kelanjutan Tahap 3 pada 17 November 2026. Halaman
Prediksi kini memuat grafik riwayat harian SBP/DBP dari window inferensi yang sama
dan perbandingan satu estimasi rerata SBP dengan baseline naif. Tambahan respons
API adalah `history_daily` dan `history_grain=respondent-date`, tanpa mengubah
nilai/rangkaian fitur model.

Pilihan origin, metadata provenance dan penolakan respons usang diperiksa lewat
tes frontend/backend serta browser desktop/ponsel. Tidak ada prediksi harian palsu,
prediksi DBP, interval keyakinan buatan atau pembukaan data aktual. Format rilis
final dan review Aldi/Nahesson tetap pending.

Laporan: [HUGO_STAGE3_REPORT.md](HUGO_STAGE3_REPORT.md). Tahap 3 selesai; Tahap 4
menunggu konfirmasi baru Hugo.

## 16 Catatan penerimaan Tahap 4

Setelah konfirmasi lanjutan Hugo, integrasi dua CSV → PostgreSQL sementara → API
→ model P2 → React diuji pada 17 November 2026. Seluruh backend lulus pada SQLite
dan PostgreSQL (masing-masing 232 passed, 1 skipped); frontend 22 passed, browser
21 passed dan production build berhasil. Seluruh tujuh origin test historis cocok
dengan artefak; fitur training/inferensi, window histori, filter dan CSV sesuai.

Cluster/API pengujian terpisah telah dihentikan. Warehouse aktif, dataset/model,
Compose dan `.env` tidak diubah. Docker daemon tidak tersedia; tidak mengklaim
verifikasi Docker/Linux atau deployment utama. Draf rilis final, review
Aldi/Nahesson, aktivasi aktual dan keputusan ilmiah tetap pending.

Laporan dan cara mengulang: [HUGO_STAGE4_REPORT.md](HUGO_STAGE4_REPORT.md).
Empat tahap teknis Hugo selesai pada data sintetis; tidak otomatis melanjutkan
pekerjaan berikutnya atau membuat commit/push.
