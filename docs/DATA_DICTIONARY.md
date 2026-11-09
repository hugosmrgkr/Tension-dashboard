# Data dictionary lengkap — CP2

**SIMULASI.** Kontrak fixture terdiri dari 24 kolom Form Awal dan 28 kolom Form Harian. Header harus cocok setelah normalisasi BOM/spasi/kapital, dengan urutan yang sama. Penambahan atau pemindahan kolom memerlukan pembaruan kontrak; tidak dipetakan secara tebakan.

Relasi: satu `respondent_id` pada profil → banyak ID-tanggal pada harian → dua sesi Pagi/Malam. Setiap sesi menyimpan dua pembacaan sistolik dan diastolik. Usia/BMI berasal dari profil; perilaku dan stres berasal dari hari pengamatan.

Missing kosong/NaN/None/NaT tetap NA; tidak diimputasi nol. ID atau tanggal tidak valid, ID tanpa profil dikarantina; duplikat identik disisakan satu dan konflik seluruh versinya dikarantina. Sel non-kunci invalid menjadi NA dengan issue. Timestamp hanya metadata audit; nama dikeluarkan.

## Form Awal

| No. | Nama asli | Nama teknis | Sumber | Tipe | Satuan | Kategori | Missing | Validasi / catatan | Transformasi |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Timestamp | submitted_at | Form Awal | timestamp | — | Teks sumber / numerik sesuai tipe | NA; catat bila tidak valid | Metadata audit; bukan tanggal pengamatan; tidak dimuat ke dimensi. | Parse sesuai definisi tipe |
| 2 | 1. ID Responden | respondent_id | Form Awal | id | — | Teks sumber / numerik sesuai tipe | Karantina baris bila kosong/invalid | Maksimum 40 karakter. Wajib; tidak membuat ID otomatis atau mengubah digit ID. | Parse sesuai definisi tipe |
| 3 | 2. Nama lengkap | direct_identity | Form Awal | excluded | — | Teks sumber / numerik sesuai tipe | Tidak dimuat (identitas) | Nama tidak dimuat, tidak disalin ke laporan atau dataset analitik. | Parse sesuai definisi tipe |
| 4 | 3. Berapa usia anda saat ini (Contoh: 22 tahun) | age | Form Awal | integer | tahun | Teks sumber / numerik sesuai tipe | NA; catat bila tidak valid | Rentang teknis 0–120. Rentang teknis; kriteria inklusi penelitian belum final. | Parse numerik; terima sufiks hanya sesuai satuan |
| 5 | 4. Apa jenis kelamin anda? | gender | Form Awal | category | — | Laki-laki; Perempuan | NA; catat bila tidak valid | Maksimum 35 karakter.  | Normalisasi spasi/kapital ke label enum |
| 6 | 5. Di provinsi mana Anda tinggal saat ini? (Contoh: Sumatera Utara) | province | Form Awal | text | — | Teks sumber / numerik sesuai tipe | NA; catat bila tidak valid | Maksimum 100 karakter. Teks lokasi; belum ada registry wilayah untuk verifikasi geografis. | Parse sesuai definisi tipe |
| 7 | 6. Di kabupaten atau kota mana Anda tinggal saat ini? (Contoh: Toba Samosir) | city | Form Awal | text | — | Teks sumber / numerik sesuai tipe | NA; catat bila tidak valid | Maksimum 100 karakter. Kabupaten/kota, bukan kecamatan; ejaan tidak ditebak. | Parse sesuai definisi tipe |
| 8 | 7. Apa pekerjaan atau kegiatan utama Anda saat ini? | occupation | Form Awal | text | — | Teks sumber / numerik sesuai tipe | NA; catat bila tidak valid | Maksimum 220 karakter. Pilihan/teks lain dari formulir; dipertahankan, bukan enum tebakan. | Parse sesuai definisi tipe |
| 9 | 9. Apa pendidikan terakhir yang telah Anda selesaikan? | education | Form Awal | text | — | Teks sumber / numerik sesuai tipe | NA; catat bila tidak valid | Maksimum 150 karakter. Pilihan/teks lain dari formulir; dipertahankan. | Parse sesuai definisi tipe |
| 10 | 10. Apakah Anda pernah didiagnosis memiliki tekanan darah tinggi oleh tenaga kesehatan? | diagnosed_bp | Form Awal | category | — | Ya; Tidak | NA; catat bila tidak valid | Disimpan sebagai kunci conditions_json; kosong bukan Tidak. | Normalisasi spasi/kapital ke label enum |
| 11 | 11. Apakah saat ini Anda menggunakan obat yang diresepkan untuk tekanan darah tinggi? | bp_medication | Form Awal | category | — | Ya; Tidak | NA; catat bila tidak valid | Disimpan sebagai kunci conditions_json; kosong bukan Tidak. | Normalisasi spasi/kapital ke label enum |
| 12 | 12. Apakah Anda pernah didiagnosis diabetes oleh tenaga kesehatan? | diabetes | Form Awal | category | — | Ya; Tidak | NA; catat bila tidak valid | Disimpan sebagai kunci conditions_json; kosong bukan Tidak. | Normalisasi spasi/kapital ke label enum |
| 13 | 13. Apakah Anda pernah didiagnosis penyakit ginjal oleh tenaga kesehatan? | kidney | Form Awal | category | — | Ya; Tidak | NA; catat bila tidak valid | Disimpan sebagai kunci conditions_json; kosong bukan Tidak. | Normalisasi spasi/kapital ke label enum |
| 14 | 14. Apakah Anda pernah didiagnosis kolesterol tinggi atau gangguan lemak darah oleh tenaga kesehatan? | cholesterol | Form Awal | category | — | Ya; Tidak | NA; catat bila tidak valid | Disimpan sebagai kunci conditions_json; kosong bukan Tidak. | Normalisasi spasi/kapital ke label enum |
| 15 | 15. Apakah Anda pernah didiagnosis penyakit jantung oleh tenaga kesehatan? | heart | Form Awal | category | — | Ya; Tidak | NA; catat bila tidak valid | Disimpan sebagai kunci conditions_json; kosong bukan Tidak. | Normalisasi spasi/kapital ke label enum |
| 16 | 16. Apakah Anda pernah didiagnosis mengalami stroke oleh tenaga kesehatan? | stroke | Form Awal | category | — | Ya; Tidak | NA; catat bila tidak valid | Disimpan sebagai kunci conditions_json; kosong bukan Tidak. | Normalisasi spasi/kapital ke label enum |
| 17 | 17. Apakah ibu kandung Anda pernah didiagnosis memiliki tekanan darah tinggi? | mother_bp | Form Awal | category | — | Ya; Tidak | NA; catat bila tidak valid | Disimpan sebagai kunci conditions_json; kosong bukan Tidak. | Normalisasi spasi/kapital ke label enum |
| 18 | 18. Apakah ayah kandung Anda pernah didiagnosis memiliki tekanan darah tinggi? | father_bp | Form Awal | category | — | Ya; Tidak | NA; catat bila tidak valid | Disimpan sebagai kunci conditions_json; kosong bukan Tidak. | Normalisasi spasi/kapital ke label enum |
| 19 | 20. Apakah orang tua kandung atau saudara kandung Anda pernah didiagnosis diabetes? | family_diabetes | Form Awal | category | — | Ya; Tidak | NA; catat bila tidak valid | Disimpan sebagai kunci conditions_json; kosong bukan Tidak. | Normalisasi spasi/kapital ke label enum |
| 20 | 21. Apakah orang tua kandung atau saudara kandung Anda pernah didiagnosis penyakit jantung atau mengalami stroke? | family_heart | Form Awal | category | — | Ya; Tidak | NA; catat bila tidak valid | Disimpan sebagai kunci conditions_json; kosong bukan Tidak. | Normalisasi spasi/kapital ke label enum |
| 21 | 22. Berapa tinggi badan Anda? (Masukkan dalam sentimeter (cm), misalnya 165 cm) | height_cm | Form Awal | number | cm | Teks sumber / numerik sesuai tipe | NA; catat bila tidak valid | Rentang teknis 80–250.  | Parse numerik; terima sufiks hanya sesuai satuan |
| 22 | 23. Berapa berat badan Anda? (Masukkan dalam kilogram misalnya 45 kg) | weight_kg | Form Awal | number | kg | Teks sumber / numerik sesuai tipe | NA; catat bila tidak valid | Rentang teknis 15–300.  | Parse numerik; terima sufiks hanya sesuai satuan |
| 23 | 24. Aktivitas fisik atau olahraga apa yang biasanya Anda lakukan? (boleh memilih lebih dari satu) | usual_activity | Form Awal | text | — | Teks sumber / numerik sesuai tipe | NA; catat bila tidak valid | Multi-pilihan utuh; jangan split koma karena label juga mengandung koma. | Parse sesuai definisi tipe |
| 24 | 25. Dalam satu minggu biasa, berapa hari Anda melakukan aktivitas fisik yang membuat napas atau denyut jantung sedikit lebih cepat? | active_days_week | Form Awal | integer | hari/minggu | Teks sumber / numerik sesuai tipe | NA; catat bila tidak valid | Rentang teknis 0–7.  | Parse numerik; terima sufiks hanya sesuai satuan |

## Form Harian

| No. | Nama asli | Nama teknis | Sumber | Tipe | Satuan | Kategori | Missing | Validasi / catatan | Transformasi |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Timestamp | submitted_at | Form Harian | timestamp | — | Teks sumber / numerik sesuai tipe | NA; catat bila tidak valid | Metadata audit saja; tidak menggantikan tanggal pengamatan. | Parse sesuai definisi tipe |
| 2 | 1. ID Responden | respondent_id | Form Harian | id | — | Teks sumber / numerik sesuai tipe | Karantina baris bila kosong/invalid | Maksimum 40 karakter. Wajib cocok dengan profil diterima. | Parse sesuai definisi tipe |
| 3 | 2. Tanggal pengamatan | date | Form Harian | date | — | Teks sumber / numerik sesuai tipe | Karantina baris bila kosong/invalid | Tanggal ISO atau DD/MM/YYYY eksplisit; pasangan ID-tanggal unik. | Parse sesuai definisi tipe |
| 4 | 3. Pukul berapa Anda mengukur tekanan darah pagi ini? | morning_time | Form Harian | time | HH:MM[:SS] | Teks sumber / numerik sesuai tipe | NA; catat bila tidak valid | Waktu lokal pengukuran; tidak disamakan dengan durasi. | Parse sesuai definisi tipe |
| 5 | 4. Berapa angka atas (sistolik) pada pembacaan pertama? | morning_sbp1 | Form Harian | number | mmHg | Teks sumber / numerik sesuai tipe | NA; catat bila tidak valid | Rentang teknis 60–260.  | Parse numerik; terima sufiks hanya sesuai satuan |
| 6 | 6. Berapa angka bawah (diastolik) pada pembacaan pertama? | morning_dbp1 | Form Harian | number | mmHg | Teks sumber / numerik sesuai tipe | NA; catat bila tidak valid | Rentang teknis 35–170.  | Parse numerik; terima sufiks hanya sesuai satuan |
| 7 | 7. Berapa angka atas (sistolik) pada pembacaan kedua? | morning_sbp2 | Form Harian | number | mmHg | Teks sumber / numerik sesuai tipe | NA; catat bila tidak valid | Rentang teknis 60–260.  | Parse numerik; terima sufiks hanya sesuai satuan |
| 8 | 8. Berapa angka bawah (diastolik) pada pembacaan kedua? | morning_dbp2 | Form Harian | number | mmHg | Teks sumber / numerik sesuai tipe | NA; catat bila tidak valid | Rentang teknis 35–170.  | Parse numerik; terima sufiks hanya sesuai satuan |
| 9 | 9. Dalam 30 menit sebelum pengukuran pagi, apakah Anda melakukan salah satu kegiatan berikut? | morning_context | Form Harian | open_category | — | Berolahraga; Tidak ada kegiatan di atas; Minum kopi, teh, atau minuman berkafein; Merokok | NA; catat bila tidak valid | Maksimum 220 karakter.  | Normalisasi spasi/kapital ke label enum |
| 10 | 10. Pukul berapa Anda mengukur tekanan darah malam ini? | evening_time | Form Harian | time | HH:MM[:SS] | Teks sumber / numerik sesuai tipe | NA; catat bila tidak valid | Waktu lokal pengukuran; tidak disamakan dengan durasi. | Parse sesuai definisi tipe |
| 11 | 11. Berapa angka atas (sistolik) pada pembacaan pertama? | evening_sbp1 | Form Harian | number | mmHg | Teks sumber / numerik sesuai tipe | NA; catat bila tidak valid | Rentang teknis 60–260.  | Parse numerik; terima sufiks hanya sesuai satuan |
| 12 | 12. Berapa angka bawah (diastolik) pada pembacaan pertama? | evening_dbp1 | Form Harian | number | mmHg | Teks sumber / numerik sesuai tipe | NA; catat bila tidak valid | Rentang teknis 35–170.  | Parse numerik; terima sufiks hanya sesuai satuan |
| 13 | 13. Berapa angka atas (sistolik) pada pembacaan kedua? | evening_sbp2 | Form Harian | number | mmHg | Teks sumber / numerik sesuai tipe | NA; catat bila tidak valid | Rentang teknis 60–260.  | Parse numerik; terima sufiks hanya sesuai satuan |
| 14 | 14. Berapa angka bawah (diastolik) pada pembacaan kedua? | evening_dbp2 | Form Harian | number | mmHg | Teks sumber / numerik sesuai tipe | NA; catat bila tidak valid | Rentang teknis 35–170.  | Parse numerik; terima sufiks hanya sesuai satuan |
| 15 | 15. Dalam 30 menit sebelum pengukuran malam, apakah Anda melakukan salah satu kegiatan berikut? | evening_context | Form Harian | open_category | — | Berolahraga; Tidak ada kegiatan di atas; Minum kopi, teh, atau minuman berkafein; Merokok | NA; catat bila tidak valid | Maksimum 220 karakter.  | Normalisasi spasi/kapital ke label enum |
| 16 | 16. Aktivitas fisik atau olahraga apa yang Anda lakukan hari ini? | activity_type | Form Harian | open_category | — | Tidak melakukan aktivitas fisik atau olahraga hari ini; Jalan kaki untuk pergi bekerja, sekolah, berbelanja, atau keperluan lain; Pekerjaan fisik, seperti bertani, mengangkat barang, atau pekerjaan lapangan; Latihan kekuatan atau angkat beban; Pekerjaan rumah atau berkebun, seperti menyapu, mengepel, atau mencangkul; Jalan kaki untuk olahraga; Jogging atau lari; Senam atau aerobik; Olahraga permainan, seperti bulu tangkis, sepak bola, atau bola voli; Bersepeda; Aktivitas lainnya | NA; catat bila tidak valid |  | Normalisasi spasi/kapital ke label enum |
| 17 | 17. Berapa total menit yang Anda gunakan untuk aktivitas fisik hari ini? <br>Contoh: Jalan cepat atau kegiatan yang membuat napas sedikit lebih cepat, tetapi Anda masih bisa berbicara. Hitung total waktu dan jangan menghitung menit yang sama dua kali. Jika tidak ada, isi 0. | activity_minutes | Form Harian | integer | menit | Teks sumber / numerik sesuai tipe | NA; catat bila tidak valid | Rentang teknis 0–1440.  | Parse numerik; terima sufiks hanya sesuai satuan |
| 18 | 18. Berapa total menit yang Anda gunakan untuk aktivitas fisik berat hari ini?<br>(contoh: lari cepat atau aktivitas fisik yang membuat napas jauh lebih cepat dan membuat Anda sulit berbicara panjang. Jika tidak ada, isi 0. Jika tidak tahu, jangan mengira-ngira.) | heavy_minutes | Form Harian | integer | menit | Teks sumber / numerik sesuai tipe | NA; catat bila tidak valid | Rentang teknis 0–1440.  | Parse numerik; terima sufiks hanya sesuai satuan |
| 19 | 19. Kira-kira berapa lama total Anda duduk atau hanya sedikit bergerak hari ini, di luar waktu tidur? | sitting | Form Harian | category | — | Kurang dari 4 jam; 4–7 jam; 8–10 jam; Lebih dari 10 jam | NA; catat bila tidak valid | Maksimum 90 karakter.  | Normalisasi spasi/kapital ke label enum |
| 20 | 20. Berapa jam Anda tidur tadi malam? | sleep_hours | Form Harian | sleep | jam | Teks sumber / numerik sesuai tipe | NA; catat bila tidak valid | Rentang teknis 0–18. HH:MM sebagai durasi hanya untuk simulasi. Data aktual tetap NA sampai definisi disetujui. | Parse sesuai definisi tipe |
| 21 | 21. Hari ini, berapa kali Anda makan makanan asin atau makanan olahan? | salty_food | Form Harian | category | — | Tidak sama sekali; 1 kali; 2 kali; 3 kali atau lebih | NA; catat bila tidak valid | Maksimum 90 karakter.  | Normalisasi spasi/kapital ke label enum |
| 22 | 22. Hari ini, berapa porsi buah yang Anda makan? | fruit | Form Harian | category | — | Tidak mengonsumsi buah; 1 porsi; 2 porsi; 3 porsi atau lebih | NA; catat bila tidak valid | Maksimum 90 karakter.  | Normalisasi spasi/kapital ke label enum |
| 23 | 23. Hari ini, berapa porsi sayur yang Anda makan? | vegetable | Form Harian | category | — | Tidak mengonsumsi sayur; 1 porsi; 2 porsi; 3 porsi atau lebih | NA; catat bila tidak valid | Maksimum 90 karakter.  | Normalisasi spasi/kapital ke label enum |
| 24 | 24. Hari ini, berapa gelas atau cangkir minuman berkafein yang Anda konsumsi?<br>Contoh: kopi, teh, atau minuman energi. | caffeine | Form Harian | category | — | Tidak mengonsumsi; 1 gelas; 2 gelas; 3 gelas atau lebih | NA; catat bila tidak valid | Maksimum 90 karakter.  | Normalisasi spasi/kapital ke label enum |
| 25 | 25. Apakah anda merokok hari ini? | smoked | Form Harian | category | — | Ya; Tidak; Tidak berlaku karena saya tidak merokok | NA; catat bila tidak valid | Maksimum 110 karakter.  | Normalisasi spasi/kapital ke label enum |
| 26 | Berapa kali anda merokok hari ini? | smoke_count | Form Harian | integer | kali/hari (sesuai pertanyaan, bukan otomatis batang) | Teks sumber / numerik sesuai tipe | NA; catat bila tidak valid | Rentang teknis 0–100. Kosong tetap NA, termasuk tidak berlaku; tidak diisi nol otomatis. | Parse numerik; terima sufiks hanya sesuai satuan |
| 27 | 26. Jika Anda menggunakan obat yang diresepkan untuk tekanan darah, apakah Anda minum obat sesuai petunjuk hari ini? | medication | Form Harian | category | — | Ya; Tidak; Saya tidak menggunakan obat tekanan darah | NA; catat bila tidak valid | Maksimum 180 karakter.  | Normalisasi spasi/kapital ke label enum |
| 28 | 27. Seberapa besar stres yang Anda rasakan hari ini? | stress | Form Harian | stress | skor | Teks sumber / numerik sesuai tipe | NA; catat bila tidak valid | Rentang teknis 1–5. Terima integer 1–5 atau label persis formulir. | Parse sesuai definisi tipe |

## Kolom turunan dan penyimpanan

| Kolom | Rumus / asal | Grain / perlakuan |
| --- | --- | --- |
| bmi | weight_kg / (height_cm/100)^2, dibulatkan 3 desimal | Profil; NA jika tinggi/berat tidak valid |
| conditions_json | 11 kunci riwayat pada Form Awal kolom 10–20 | Profil; setiap jawaban kosong tetap null |
| sbp_mean / dbp_mean | Rerata pasangan nomor pembacaan sama yang lolos gate teknis | Sesi ambigu, parsial atau tidak konsisten: NA pending_review; raw dipertahankan |
| valid_sbp_count / valid_dbp_count | Jumlah komponen numerik 0-2; bukan status sesi | is_valid memakai bp_policy, bukan sekadar kedua hitungan > 0 |
| session | Pagi/Malam dari pasangan kolom sumber | Bukan pertanyaan baru; pemisahan struktur wide → long |
| year/month/day | Komponen tanggal pengamatan | Dimensi tanggal |
| ID surrogate / FK | Dibuat database, bukan ID responden baru | PK teknis, berbeda dari respondent_id sumber |
| future_7d_mean_sbp | Usulan target tahap modelling | Di luar CP2; tidak dibuat/diubah oleh pekerjaan ini |

## Aturan format dan kategori

- Integer menerima angka bulat saja; `3 hari`, `45 menit`, `21 tahun`, `165 cm`, `60,5 kg` hanya diterima pada kolom dengan satuan yang sesuai. `3.5 hari` tidak dibulatkan diam-diam.
- Tanggal menerima ISO `YYYY-MM-DD`/datetime ISO atau `DD/MM/YYYY` eksplisit; waktu menerima `HH:MM[:SS]`. Nomor serial Excel dan teks tanggal ambigu ditahan, bukan ditebak.
- Kategori tertutup yang tidak dikenal menjadi NA dengan issue. Kategori aktivitas/konteks terbuka dipertahankan dengan flag review. Pekerjaan, pendidikan, provinsi dan kota bukan enum geografis yang telah diverifikasi.
- Multi-pilihan aktivitas umum tidak dipisahkan dengan koma: label pilihan juga mengandung koma.
- Mapping khusus fixture sintetis: `4�7 jam`/`4-7 jam` → `4–7 jam`; `8�10 jam`/`8-10 jam` → `8–10 jam`. Raw tidak diubah. Mapping karakter rusak ini tidak diterapkan otomatis pada data aktual.
- Tidur sintetis `06:30` → 6,5 jam. Pecahan 0<x<1 ditandai ambigu (dapat berupa pecahan hari Excel), tidak dikali 24 atau dianggap jam otomatis. Data aktual seluruhnya menunggu keputusan semantik.
- Rentang BP 60–260 sistolik, 35–170 diastolik adalah pagar teknis proyek, bukan pedoman diagnosis. Nilai di luar pagar menjadi NA dengan alasan; sumber mentah tetap ada. SBP≤DBP ditahan pending_review; IQR tetap flag deskriptif pada simulasi.
- Tidak ada kriteria inklusi usia final yang dipaksakan. Usia teknis 0–120; kelayakan responden ditentukan terpisah bersama dosen.
- Semua perubahan kategori/satuan dapat ditelusuri lewat laporan normalisasi dan hash sumber. Tidak ada identitas langsung dalam keluaran analitik.

## Klarifikasi final P0/P1 - mengikat API, ETL dan baseline

- Gate `paired-reading-review-v1` adalah gate teknis sementara, bukan aturan klinis. Pasangan harus pada nomor yang sama; komponen silang/parsial, nilai di luar pagar teknis lama, SBP<=DBP, atau derived NA dari review tidak masuk rerata/model. Nilai mentah sumber tetap ada; keputusan minimum bacaan dan protokol penelitian menunggu dosen.
- `review_status` API: ready / incomplete / pending_review; `review_reasons`, `valid_pair_count`, `is_valid` dihitung saat serving. Tidak ada migrasi/penghapusan DB aktif.
- Responden aktif = ID dengan sedikitnya satu catatan harian diterima ETL pada filter; `respondents_with_valid_bp` berbeda. Catatan tanpa BP tetap aktif harian; mean BP NA dan grafik kosong, bukan dummy.
- Duplikat identik: satu dipakai, pengulangan diaudit. Konflik jawaban pada kunci sama: semua versi dikarantina, tanpa memilih first/last/timestamp. Koreksi perlu input bersih berversi + decision log; raw tidak ditimpa.
- Tanggal mencurigakan menurut pagar teknis lama 2024-2030 atau sesudah timestamp pengiriman dikarantina, bukan diperbaiki/ditebak. Batas tersebut bukan kriteria ilmiah baru.
- IQR pada sumber sintetis tetap flag deskriptif; bukan diagnosis dan tidak otomatis dihapus. Commit aktual dengan issues/karantina/IQR belum diselesaikan ditolak quality gate. Arti tidur aktual masih pending.
- Header dikenali secara eksplisit: BOM/spasi/kapital/CRLF aman; urutan/pertanyaan baru atau kolom hilang ditolak. Ekspor aktual belum tersedia untuk membuktikan mapping final; jangan mengira pemetaan bebas berdasarkan posisi.
- Ekspor CSV mengawali teks berpotensi formula spreadsheet dengan apostrof. Ini pelindung ekspor, bukan pengubahan nilai database.
