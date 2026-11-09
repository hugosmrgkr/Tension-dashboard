# Data dictionary ringkas — Toba Health Insight (M6–M8)

Sumber utama: `data/sample/Data_Responden_Sintetis.csv` (24 kolom) dan `data/sample/Data_Harian_Sintetis.csv` (28 kolom). Pemrosesan memakai indeks/urutan header asal yang diverifikasi, bukan asumsi kolom lama `kecamatan` atau `pola_makan`.

| Kolom warehouse | Sumber / definisi | Grain dan satuan |
| --- | --- | --- |
| respondent_id | ID Responden pada kedua form | Profil / kunci pseudonim |
| age, gender | Form awal Q3/Q4 | Per responden; tahun / kategori |
| province, city | Form awal Q5/Q6 | Per responden; bukan kecamatan |
| occupation, education | Form awal Q7/Q9 | Per responden |
| height_cm, weight_kg | Form awal Q22/Q23 | Per responden; cm dan kg |
| bmi | `weight_kg/(height_cm/100)^2` | Per responden; turunan |
| usual_activity, active_days_week | Form awal Q24/Q25 | Per responden; deskripsi dan 0–7 hari |
| date | Form harian Q2 | ID × tanggal; **bukan timestamp pengiriman** |
| session | Struktur pagi / malam | ID × tanggal × sesi |
| sbp1,dbp1,sbp2,dbp2 | Form harian Q4/Q6/Q7/Q8 dan Q11–Q14 | mmHg; nilai mentah valid yang tidak diganti |
| sbp_mean,dbp_mean | Rata-rata pembacaan valid per sesi | mmHg; data turunan; `valid_*_count` disimpan |
| activity_minutes, heavy_minutes | Form harian Q17/Q18 | ID × tanggal; menit |
| sitting | Q19 | ID × tanggal; kategori |
| sleep_hours | Q20; HH:MM simulasi → jam desimal | ID × tanggal; **asumsi hanya untuk data sintetis** |
| salty_food,fruit,vegetable,caffeine | Q21–Q24 | ID × tanggal; kategori terpisah |
| smoked,smoke_count,medication | Q25, tak bernomor, Q26 | ID × tanggal; kategori/jumlah (NA bukan otomatis 0) |
| stress | Q27 `1 = ...` → integer 1–5 | ID × tanggal; tidak boleh 0–10 |
| future_7d_mean_sbp | Rata-rata SBP harian 7 hari setelah t | Target model numerik, **bukan** pertanyaan form |

## Aturan kualitas minimum

- `respondent_id` wajib dari Form Awal, tidak boleh membuat ID otomatis.
- Duplikasi `(respondent_id,date)` ditahan dan dicatat, bukan diam-diam ditimpa.
- Angka BP yang tidak valid disimpan sebagai NA pada *clean table*, sumber mentah tetap ada di file sumber.
- Sesi dianggap valid bila terdapat ≥1 SBP dan ≥1 DBP yang lolos pemeriksaan.
- Kolom harian tidak dipaksakan tetap di seluruh tanggal untuk satu orang.
- Kategori asli boleh dinormalisasi terpisah bila ada mapping eksplisit; jangan menambah variabel yang tidak ditanya.
- Foto, nama lengkap, NIK, kontak responden tidak boleh diekspor atau di-commit.
