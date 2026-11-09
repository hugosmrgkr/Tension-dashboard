# Laporan kualitas data CP2 — SIMULASI

Hasil dihitung ulang dari dua CSV yang hash SHA-256-nya dicatat pada `reports/cp2/source_manifest.json`. Data sintetis tidak memenuhi bukti data primer. Tidak ada data mentah ditimpa, nama disalin, atau missing diimputasi nol.

## Sumber dan hasil baris

| Sumber | Raw | Diterima / turunan | Dikarantina / tidak lengkap |
| --- | --- | --- | --- |
| Profil | 19 | 19 | 0 |
| Harian | 570 | 570 | 0 |
| Sesi | 2 × harian diterima | 1140 | 0 |

Karantina berupa nomor baris sumber dan alasan pada JSON/CSV. Baris pertama ID atau ID-tanggal dipertahankan; kemunculan berikutnya tidak menimpa data pertama. Semua sumber tetap tersedia untuk peninjauan koreksi. Kesalahan skema membatalkan seluruh batch sebelum load.

## Completeness dan validity sebelum–sesudah

Persentase menggunakan jumlah baris sumber/diterima masing-masing tabel. Missing dihitung terpisah dari invalid. Invalid menjadi NA berarti validity nilai teramati dapat meningkat sambil completeness menurun; ini bukan imputasi. Nama dikeluarkan, bukan dinilai sebagai missing baru. Tabel sesi memiliki grain berbeda sehingga tidak dibandingkan sebagai 28 kolom raw.

| Sumber | Kolom teknis | Raw n | Raw NA (%) | Raw invalid | Clean n | Clean NA (%) | Clean invalid |
| --- | --- | --- | --- | --- | --- | --- | --- |
| profiles | submitted_at | 19 | 0.0 | 0 | 19 | 0.0 | 0 |
| profiles | respondent_id | 19 | 0.0 | 0 | 19 | 0.0 | 0 |
| profiles | direct_identity | 19 | 0.0 | 0 | 19 | — | — |
| profiles | age | 19 | 0.0 | 0 | 19 | 0.0 | 0 |
| profiles | gender | 19 | 0.0 | 0 | 19 | 0.0 | 0 |
| profiles | province | 19 | 0.0 | 0 | 19 | 0.0 | 0 |
| profiles | city | 19 | 0.0 | 0 | 19 | 0.0 | 0 |
| profiles | occupation | 19 | 0.0 | 0 | 19 | 0.0 | 0 |
| profiles | education | 19 | 0.0 | 0 | 19 | 0.0 | 0 |
| profiles | diagnosed_bp | 19 | 0.0 | 0 | 19 | 0.0 | 0 |
| profiles | bp_medication | 19 | 0.0 | 0 | 19 | 0.0 | 0 |
| profiles | diabetes | 19 | 0.0 | 0 | 19 | 0.0 | 0 |
| profiles | kidney | 19 | 0.0 | 0 | 19 | 0.0 | 0 |
| profiles | cholesterol | 19 | 0.0 | 0 | 19 | 0.0 | 0 |
| profiles | heart | 19 | 0.0 | 0 | 19 | 0.0 | 0 |
| profiles | stroke | 19 | 0.0 | 0 | 19 | 0.0 | 0 |
| profiles | mother_bp | 19 | 0.0 | 0 | 19 | 0.0 | 0 |
| profiles | father_bp | 19 | 0.0 | 0 | 19 | 0.0 | 0 |
| profiles | family_diabetes | 19 | 0.0 | 0 | 19 | 0.0 | 0 |
| profiles | family_heart | 19 | 0.0 | 0 | 19 | 0.0 | 0 |
| profiles | height_cm | 19 | 0.0 | 0 | 19 | 0.0 | 0 |
| profiles | weight_kg | 19 | 0.0 | 0 | 19 | 0.0 | 0 |
| profiles | usual_activity | 19 | 0.0 | 0 | 19 | 0.0 | 0 |
| profiles | active_days_week | 19 | 0.0 | 0 | 19 | 0.0 | 0 |
| daily | submitted_at | 570 | 0.0 | 0 | 570 | 0.0 | 0 |
| daily | respondent_id | 570 | 0.0 | 0 | 570 | 0.0 | 0 |
| daily | date | 570 | 0.0 | 0 | 570 | 0.0 | 0 |
| daily | morning_time | 570 | 0.0 | 0 | 570 | 0.0 | 0 |
| daily | morning_sbp1 | 570 | 0.0 | 0 | 570 | 0.0 | 0 |
| daily | morning_dbp1 | 570 | 0.0 | 0 | 570 | 0.0 | 0 |
| daily | morning_sbp2 | 570 | 0.0 | 0 | 570 | 0.0 | 0 |
| daily | morning_dbp2 | 570 | 0.0 | 0 | 570 | 0.0 | 0 |
| daily | morning_context | 570 | 0.0 | 0 | 570 | 0.0 | 0 |
| daily | evening_time | 570 | 0.0 | 0 | 570 | 0.0 | 0 |
| daily | evening_sbp1 | 570 | 0.0 | 0 | 570 | 0.0 | 0 |
| daily | evening_dbp1 | 570 | 0.0 | 0 | 570 | 0.0 | 0 |
| daily | evening_sbp2 | 570 | 0.0 | 0 | 570 | 0.0 | 0 |
| daily | evening_dbp2 | 570 | 0.0 | 0 | 570 | 0.0 | 0 |
| daily | evening_context | 570 | 0.0 | 0 | 570 | 0.0 | 0 |
| daily | activity_type | 570 | 0.0 | 0 | 570 | 0.0 | 0 |
| daily | activity_minutes | 570 | 0.0 | 0 | 570 | 0.0 | 0 |
| daily | heavy_minutes | 570 | 0.0 | 0 | 570 | 0.0 | 0 |
| daily | sitting | 570 | 0.526 | 0 | 570 | 0.526 | 0 |
| daily | sleep_hours | 570 | 1.053 | 0 | 570 | 1.053 | 0 |
| daily | salty_food | 570 | 0.0 | 0 | 570 | 0.0 | 0 |
| daily | fruit | 570 | 0.0 | 0 | 570 | 0.0 | 0 |
| daily | vegetable | 570 | 0.0 | 0 | 570 | 0.0 | 0 |
| daily | caffeine | 570 | 0.0 | 0 | 570 | 0.0 | 0 |
| daily | smoked | 570 | 0.0 | 0 | 570 | 0.0 | 0 |
| daily | smoke_count | 570 | 96.491 | 0 | 570 | 96.491 | 0 |
| daily | medication | 570 | 0.0 | 0 | 570 | 0.0 | 0 |
| daily | stress | 570 | 0.0 | 0 | 570 | 0.0 | 0 |

## Consistency dan uniqueness

| Pemeriksaan | Sebelum | Sesudah |
| --- | --- | --- |
| Kelebihan ID profil duplikat | 0 | 0 |
| Kelebihan pasangan ID-tanggal | 0 | 0 |
| Harian tanpa profil diterima | 0 | 0 |

Satuan clean: tahun; cm; kg; mmHg; menit; hari/minggu; stres 1–5; tidur asumsi simulasi. Profil aktivitas mingguan memakai parser `hari` yang sesuai satuan, tidak lagi kehilangan seluruh nilai.

## Transformasi yang tercatat

| Kolom | Jumlah sel berubah representasi / normalisasi |
| --- | --- |
| active_days_week | 19 |
| evening_dbp1 | 570 |
| evening_dbp2 | 570 |
| evening_sbp1 | 570 |
| evening_sbp2 | 570 |
| evening_time | 570 |
| height_cm | 19 |
| morning_dbp1 | 570 |
| morning_dbp2 | 570 |
| morning_sbp1 | 570 |
| morning_sbp2 | 570 |
| morning_time | 570 |
| sleep_hours | 564 |
| stress | 570 |
| submitted_at | 589 |

Perubahan representasi termasuk parse tanggal/waktu, angka bersatuan dan label stres. Alias kategori duduk dengan karakter rusak hanya dipetakan bila ditemukan pada simulasi, sebagaimana dictionary; label valid tetap dipertahankan. Data aktual tidak diperbaiki dengan tebakan.

## Anomali tekanan darah

| Sesi | Variabel | n | Q1 | Q3 | Batas bawah IQR | Batas atas IQR | Ditandai |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Pagi | sbp_mean | 570 | 113.5 | 123.0 | 99.25 | 137.25 | 7 |
| Pagi | dbp_mean | 570 | 69.5 | 75.0 | 61.25 | 83.25 | 7 |
| Malam | sbp_mean | 570 | 114.0 | 123.0 | 100.5 | 136.5 | 11 |
| Malam | dbp_mean | 570 | 70.0 | 75.0 | 62.5 | 82.5 | 5 |

25 sesi memiliki sedikitnya satu flag IQR; 0 sel BP invalid. IQR dan SBP≤DBP tidak otomatis menghapus sesi. Pagar numerik teknis, nilai invalid, dan alasan dapat ditelusuri ke baris sumber. Batas tersebut bukan kriteria diagnosis.

## Issue dan keputusan

Tidak ditemukan issue tipe/rentang/konsistensi pada fixture ini; missing yang disengaja tetap dilaporkan.

Tanggal mencurigakan: 0. Rincian lengkap ada di `reports/cp2/quality.json` dan `issues.csv`.

## Batas kesiapan

Laporan ini membuktikan audit teknis fixture, bukan kelayakan penelitian aktual. Masih perlu keputusan dosen tentang semantik tidur, kriteria responden, minimum catatan/responden, izin data, serta aturan peninjauan nilai ekstrem. Registry wilayah dan pilihan lain di kuesioner aktual perlu diverifikasi sebelum kontrak diperluas.
