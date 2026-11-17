# Hugo Tahap 2 Loader dan pemeriksaan kompatibilitas

Tanggal: 17 November 2026. Tahap ini dikerjakan setelah Hugo mengonfirmasi Tahap 1.

## Hasil yang bisa dipahami tanpa membaca kode

Model P2 sintetis yang sudah ada tetap dipakai. Sebelum memberikan prediksi, API
kini memeriksa bahwa file, hash, fitur, target, horizon dan metadata sumber cocok.
Jika tidak cocok, API memberi alasan dan tidak membuat hasil pengganti.

Tidak ada pemilihan otomatis model terbaru, pelatihan ulang eksperimen aktif,
promosi model tuning, aktivasi data aktual atau perubahan visualisasi React.
Tahap 3 masih menunggu konfirmasi Hugo.

## Yang diimplementasikan

| Komponen | Perubahan |
|---|---|
| `backend/app/model_registry.py` | Adapter eksplisit `p2-comparison-v1`; memverifikasi folder/manifest/model/metrik dan kontrak |
| `backend/app/model_service.py` | Loader lama tetap menjadi entry point kompatibel, tetapi delegasi ke registry; tambahan metadata provenance dan peringatan batch belum terverifikasi |
| `backend/app/main.py` | Prediksi dan metadata perbandingan memakai registry yang sama dan fingerprint dari `SourceState.quality_json` |
| `backend/tests/test_model_registry.py` | Tes kontrak, hash, path traversal, source, metadata batch, paritas prediksi dan guard API |
| `docs/MODEL_INTEGRATION_CONTRACT.md` | Catatan implementasi terbatas Tahap 2 dan bagian yang tetap pending review |

## Pemeriksaan loader

- Sumber harus sintetis. Actual, empty dan unknown tidak diterima adapter.
- Manifest P2 dan mode hash harus didukung; nama file/path tidak boleh keluar dari
  folder yang dipilih konfigurasi, termasuk path Windows/Linux yang tidak aman.
- Hash metrik diverifikasi setelah normalisasi CRLF ke LF; hash binary joblib
  memakai byte persis. Tidak ada hash yang diubah manual pada artefak aktif.
- Identitas run, nama/hash model dalam manifest dan metrik harus konsisten.
- Target, horizon tujuh hari, urutan delapan fitur, versi fitur yang dinyatakan,
  serta status sintetis/non-diagnosis harus cocok dengan adapter CP3.
- Provenance, konfigurasi pemilihan, rentang fitur dan nilai metrik diperiksa.
- Metadata evaluasi memeriksa hash binary tanpa mengeksekusi joblib. Untuk
  inferensi, objek model juga diperiksa nama/jumlah fitur dan kemampuan predict.
- Inferensi memuat byte binary yang sama dengan byte yang telah diperiksa hash,
  bukan membaca ulang path model setelah pemeriksaan.

Joblib tetap hanya untuk artefak tim yang dipercaya. Hash adalah bukti konsistensi
konten, bukan tanda tangan penerbit atau sandbox untuk file tak dipercaya.

## Kebijakan batch sementara

| Kondisi | Hasil |
|---|---|
| Fingerprint warehouse sama dengan training | `compatibility_status=matched`, `warehouse_batch_match=true` |
| Fingerprint diketahui berbeda | Prediksi 409 `DATASET_MISMATCH`; comparison memberi `available=false` |
| Fingerprint berbentuk salah/quality JSON rusak | Ditolak dengan `DATASET_METADATA_INVALID` |
| Fingerprint tidak tercatat pada metadata legacy sintetis | Kompatibilitas lama dipertahankan dengan `batch_unverified`, nilai match null dan peringatan pada prediksi |

Menerima batch berbeda yang secara schema tetap kompatibel masih merupakan
kebijakan usulan dalam kontrak, bukan persetujuan yang sudah dibuat. Tidak ada
override untuk otomatis menerima perubahan data. Jika fingerprint tidak diketahui,
respons tidak boleh disebut cocok; pengecualian legacy ini hanya untuk sintetis.

## Kompatibilitas API

Field hasil prediksi lama dipertahankan, termasuk nilai prediksi, naif dan metadata
model. Tambahan: sumber, versi data training/inferensi, versi fitur, status kecocokan
dan scope test historis sintetis. Nilai prediksi model yang sama diuji identik.

Pada kegagalan loader, `/api/model/predict` tetap mengembalikan HTTP 409 dengan
pesan `detail`, ditambah `error_code`. `/api/model/comparison` mempertahankan pola
HTTP 200 dengan `available=false` untuk model tidak tersedia. Guard sumber aktual
yang sudah ada tetap berlaku. Endpoint baseline CP3 tidak diubah.

`metrics_scope=synthetic_historical_test` menandai asal hasil test lama. Nilai
validasi tetap skor OOF dan bukan pengukuran ulang data warehouse aktif.
Field tanggal legacy `model.trained_on` tetap kompatibel dengan adapter P2;
sumbernya `as_of` artefak lama, bukan waktu training presisi yang baru dibuktikan.

## Pengujian dan bukti

- Tes terarah loader/API: **48 lulus**, 0 gagal.
- Frontend tests: **17 lulus**, 0 gagal.
- Production build: **berhasil**; bundle frontend tetap memakai aset yang sama
  karena tidak ada perubahan kode React/CSS.
- Regresi backend menyeluruh: **225 lulus, 1 dilewati**, 0 gagal. Hasilnya pada
  `reports/hugo_stage2/backend-tests.xml` dan `verification.json`.
  Yang dilewati adalah modul API v1 historis yang sudah dipensiunkan oleh repository.
- Peringatan build ukuran bundle Plotly di atas 500 kB masih ada, bukan error.
- TestClient memberi peringatan deprecation Starlette/httpx; tidak mengubah hasil tes.
- Browser, PostgreSQL/Docker dan dataset aktual tidak diuji pada tahap ini.

Tes backend memakai **SQLite di memori** (`CP2_TEST_DATABASE_URL=sqlite://`),
salinan artefak pada direktori sementara dan fixture sintetis. Tes lama dapat
melatih model sementara untuk regresi; itu tidak melatih ulang/menimpa model aktif.
Tidak ada akses atau reset database aktif.

Bukti disimpan di `reports/hugo_stage2/`:

- `targeted-tests.xml`: tes loader dan API P2.
- `backend-tests.xml`: regresi backend menyeluruh.
- `protected_models_before.json`, `protected_models_after.json`: hash dua belas
  file artefak model sebelum/sesudah pekerjaan.
- `verification.json`: ringkasan hasil dan pemeriksaan perubahan yang dilindungi.

## Reproduksi pengujian

Dari root project dengan environment Python yang sama:

```powershell
$env:CP2_TEST_DATABASE_URL='sqlite://'
$env:OMP_NUM_THREADS='1'
$env:OPENBLAS_NUM_THREADS='1'
.\.venv\Scripts\python.exe -m pytest backend/tests/test_model_registry.py backend/tests/test_p2_model_api.py -q -p no:cacheprovider
```

Regresi menyeluruh memakai `python -m pytest backend/tests -q -p no:cacheprovider`.
Frontend diperiksa melalui `npm test` dan `npm run build` dari folder `frontend/`.
Environment di atas hanya berlaku pada terminal pengujian, tidak mengubah `.env`.

## Yang belum menjadi bagian tahap ini

- Format rilis final bersama Aldi/Nahesson dan pembukaan akses data aktual.
- Pemilihan/promosi model tuning atau training eksperimen aktual.
- Perubahan grafik riwayat/estimasi Prediksi yang merupakan Tahap 3.
- Uji browser penerimaan rilis dan deployment terintegrasi tahap berikutnya.

Dokumen kontrak tetap draft untuk review tim. Saat ini pekerjaan berada pada
branch `main` yang sudah dipilih pengguna; tidak ada branch, commit, push atau merge
otomatis. Sebelum pekerjaan Tahap 3 dimulai, tunggu konfirmasi baru dari Hugo.
