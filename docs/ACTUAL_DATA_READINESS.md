# Panduan kesiapan data aktual — tugas Aldi

## Status sumber

Kontrak parser saat ini mengharapkan dua ekspor CSV terpisah:
- Form Awal Responden: 24 kolom, urutan header eksplisit.
- Form Catatan Harian: 28 kolom, urutan header eksplisit.

BOM, spasi, kapitalisasi, dan CRLF dinormalisasi saat pemeriksaan header. Kolom hilang,
kolom tambahan, perubahan teks pertanyaan, atau perubahan urutan ditolak. Tidak ada
pemetaan berdasarkan posisi yang ditebak. Karena ekspor aktual belum disertakan dalam
checkout ini, kompatibilitas aktual **belum terverifikasi**. Jangan menyatakan dataset
aktual telah lolos validasi sampai ekspor dari Google Forms diperiksa.

## Penyimpanan privat

Simpan salinan ekspor mentah hanya pada `data/private/incoming/` (folder ini diabaikan
Git). Jangan mengubah file sumber. Jangan menaruh CSV aktual, nama, nomor kontak, token,
atau laporan baris-level di `data/sample/`, `reports/`, dokumentasi publik, issue, atau PR.

Contoh nama file lokal:
- `data/private/incoming/form_awal.csv`
- `data/private/incoming/catatan_harian.csv`

## Dry-run aktual

Dari root repository di PowerShell:

```powershell
python -m etl.import_data `
  --profile data/private/incoming/form_awal.csv `
  --daily data/private/incoming/catatan_harian.csv `
  --source-kind actual `
  --dry-run `
  --report-dir data/private/readiness/batch-YYYYMMDD
```

Perintah ini memvalidasi dua sumber dan menulis laporan privat. Tidak menjalankan commit
database. Jika header tidak cocok atau batch tidak memiliki data valid, proses berhenti
dan database tidak berubah. Periksa `quality.json`, `completeness_before.csv`,
`completeness_after.csv`, `issues.csv`, `pressure_anomalies.csv`, dan `batch_error.json`
jika batch ditolak. Laporan tersebut dapat memuat nomor baris sumber; jangan commit.

## Makna status

- `accepted`: baris yang memenuhi aturan teknis saat ini.
- `quarantined/rejected`: baris ditahan; bukan berarti data sumber boleh dihapus.
- `pending_review`: sesi BP tidak digunakan untuk rerata/fitur model sampai keputusan
  protokol terdokumentasi.
- `IQR flag`: pencilan statistik untuk review, bukan diagnosis dan bukan alasan otomatis
  menghapus nilai.
- `future_7d_mean_sbp`: target regresi usulan; window 7 hari histori + 7 hari target
  dihitung hanya jika seluruh tanggal memiliki sesi BP valid. Jumlah window bukan bukti
  kelayakan ilmiah, independensi observasi, atau persetujuan dosen.

Koreksi sumber harus berupa ekspor ulang/batch versi baru dengan catatan keputusan.
Jangan memilih versi pertama/terakhir pada konflik. Konflik profil atau ID-tanggal
mengarantina semua versi konflik. Duplikat identik hanya dapat diperlakukan sesuai aturan
parser yang terdokumentasi dan tetap harus muncul pada audit.

## Commit

Tidak ada commit otomatis dari web. Jangan menjalankan `--commit` pada database aktif
sebelum backup, pemeriksaan target, persetujuan dosen/tim, dan persetujuan pengelola.
Jika warehouse sudah terisi, CLI mewajibkan hash konten target yang diverifikasi.
Pergantian sumber sintetis ke aktual memerlukan pengakuan eksplisit dan tidak pernah
menggabungkan dua jenis sumber. Gate aktual saat ini menolak isu, karantina, dan flag
BP yang belum diselesaikan; jangan melonggarkannya tanpa keputusan tertulis.

## Ringkasan readiness di aplikasi

Endpoint admin `/api/data-readiness` mengembalikan agregat kualitas, cakupan tanggal,
jumlah sesi valid, review, dan hitungan window ML. Tidak mengembalikan isi baris,
identitas langsung, atau alasan per baris. Endpoint ini termasuk rute admin pada
staging/production. Halaman Data Partisipan menghitung satu baris per ID profil,
menampilkan ID pseudonim, demografi, lokasi tingkat wilayah, BMI deskriptif, dan jumlah
hari tercatat; filter global berlaku pada profil yang ditampilkan.

## Batasan

Data sintetis hanya menguji perilaku teknis. Data aktual tidak dapat dinyatakan siap
untuk analisis atau ML sebelum header dipetakan/ditinjau, aturan satuan tidur dan
protokol pengukuran diputuskan, konflik dan isu kualitas diselesaikan, serta target
dan penggunaan data disetujui.
