# Laporan Mingguan - Kelompok 02 - Minggu ke-11

Periode : 16/11 - 21/11/2026
Status : [Hijau / Kuning / Merah]

## 1. Target vs Capaian

| Target minggu ini | Status | Bukti |
|---|---|---|
| Integrasi model dengan aplikasi dan dashboard | Sebagian | PR #3 |
| Menampilkan hasil prediksi pada dashboard | Sebagian | PR #3 |
| Pengembangan visualisasi kualitas data | Selesai | PR #4 |
| Pemeriksaan perubahan kode anggota lain | Selesai | PR #3 |

## 2. Kontribusi Anggota

| Nama | Tugas | Tautan commit/PR/issue | Jam kerja |
|---|---|---|---|
| Aldi | [Diisi oleh Aldi] | [Tautan bukti] | [...] 
| Nahesson | [Diisi oleh Nahesson] | [Tautan bukti] | [...] |
| Hugo | Mengintegrasikan model P2 sintetis ke FastAPI dengan validasi manifest, hash, fitur, dan fingerprint batch; menampilkan riwayat SBP/DBP serta estimasi rerata SBP tujuh hari berikutnya dibanding baseline naif pada React; menambahkan pengujian integrasi dan dokumentasi. PR telah masuk main pada 21 November 2026; aktivasi data aktual masih pending. | [PR #3](https://github.com/hugosmrgkr/mental-health-dashboard/pull/3), [Issue #2](https://github.com/hugosmrgkr/mental-health-dashboard/issues/2), [2e01173](https://github.com/hugosmrgkr/mental-health-dashboard/commit/2e01173), [bf9d9da](https://github.com/hugosmrgkr/mental-health-dashboard/commit/bf9d9da), [b32ea37](https://github.com/hugosmrgkr/mental-health-dashboard/commit/b32ea37) | [Diisi Hugo sesuai catatan] |
| Ruben | [Diisi oleh Ruben] | [Tautan bukti] | [...] |
| Kasih | Mengembangkan visualisasi kualitas data pada halaman Laporan dan Ringkasan. Melakukan review PR anggota lain. | PR #4, Issue #9, PR #3 | [...] |

## 3. Metrik Minggu Ini

**- Kasih**
Commit terkait visualisasi : 3 commit.
PR yang di-merge : PR #4.
Review yang dilakukan: 1 review pada PR #3.

**- Hugo**
- Commit pekerjaan: **3 commit** (`2e01173`, `bf9d9da`, `b32ea37`), di luar merge commit.
- PR yang di-merge: **1**, [PR #3](https://github.com/hugosmrgkr/mental-health-dashboard/pull/3), merge `2376b02` pada 21 November 2026.
- Bukti pengujian 17 November pada branch integrasi: backend SQLite dan PostgreSQL terisolasi masing-masing **232 passed, 1 skipped**; frontend **22 passed**; browser **21 passed**; production build berhasil. Seluruh tujuh origin test historis sesuai artefak. Ini bukan pengujian ulang seluruh main setelah merge anggota lain.
- Dataset pengujian: **SINTETIS/SIMULASI**, 19 responden, 570 catatan harian, 1.140 sesi. Tidak melatih ulang atau mempromosikan model tuning.
- Laporan: [HUGO_STAGE4_REPORT.md](../../docs/HUGO_STAGE4_REPORT.md); [bukti verifikasi](../hugo_stage4/verification.json).


## 4. Progres Jurnal

| Bagian naskah | Penanggung jawab | Persentase selesai |
|---|---|---|
| Pendahuluan | [Nama anggota] | [...]% |
| Tinjauan pustaka | [Nama anggota] | [...]% |
| Metodologi | [Nama anggota] | [...]% |
| Hasil dan pembahasan | [Nama anggota] | [...]% |
| Kesimpulan | [Nama anggota] | [...]% |

## 5. Kendala dan Bantuan yang Dibutuhkan
- Kasih: -
- Hugo: review kontrak dataset/model bersama Aldi dan Nahesson, kesiapan data aktual serta paket rilis model masih menjadi dependensi. Docker daemon tidak tersedia pada pengujian integrasi 17 November sehingga Docker/Linux tidak diuji pada tahap itu; pengujian PostgreSQL menggunakan cluster lokal sementara yang terisolasi. Bukti persetujuan formal target belum disimpan pada artefak; status tersebut tidak diubah.

## 6. Rencana Minggu Depan

| Nama | Rencana tugas | Issue |
|---|---|---|
| Aldi | [Diisi oleh Aldi] | [Nomor issue] |
| Nahesson | [Diisi oleh Nahesson] | [Nomor issue] |
| Hugo | Menyepakati kontrak dataset/model bersama Aldi dan Nahesson, menyiapkan integrasi paket rilis setelah tersedia, serta berkoordinasi dengan Ruben untuk regresi main dan verifikasi Docker/deployment. Data aktual tetap diblokir sampai persyaratan siap. | [Issue tindak lanjut belum ditetapkan; tidak memakai ulang Issue #2 untuk cakupan baru] |
| Ruben | [Diisi oleh Ruben] | [Nomor issue] |
| Kasih | Melanjutkan penyempurnaan visualisasi, pemeriksaan kesesuaian data dengan API, dan pengujian usability dashboard. | [Nomor issue] |
