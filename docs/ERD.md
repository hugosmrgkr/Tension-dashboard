# ERD / model dimensional — CP2 Data Readiness

```mermaid
erDiagram
    dim_participant_v2 ||--o{ fact_bp_session_v2 : measures
    dim_date_v2 ||--o{ fact_bp_session_v2 : at_date
    dim_session_v2 ||--o{ fact_bp_session_v2 : at_session
    dim_participant_v2 ||--o{ fact_daily_behavior_v2 : reports
    dim_date_v2 ||--o{ fact_daily_behavior_v2 : on_date
    dim_participant_v2 {
        integer id PK
        string respondent_id UK
        integer age
        string gender
        string province
        string city
        float height_cm
        float weight_kg
        float bmi
        integer active_days_week
        text conditions_json
    }
    dim_date_v2 {
        integer id PK
        date date UK
        integer year
        integer month
        integer day
    }
    dim_session_v2 {
        integer id PK
        string name UK "Pagi/Malam"
    }
    fact_bp_session_v2 {
        integer id PK
        integer participant_id FK
        integer date_id FK
        integer session_id FK
        string measured_at
        float sbp1
        float dbp1
        float sbp2
        float dbp2
        float sbp_mean
        float dbp_mean
        integer valid_sbp_count
        integer valid_dbp_count
    }
    fact_daily_behavior_v2 {
        integer id PK
        integer participant_id FK
        integer date_id FK
        integer activity_minutes
        integer heavy_minutes
        float sleep_hours
        string sitting
        string salty_food
        string fruit
        string vegetable
        string caffeine
        string smoked
        integer smoke_count
        string medication
        integer stress
    }
```

**Grain:** `fact_bp_session_v2`: satu orang × satu tanggal × satu sesi. `fact_daily_behavior_v2`: satu orang × satu tanggal. 3 dimensi: peserta, tanggal, sesi. Penyimpanan perilaku per hari mencegah penggandaan aktivitas dan tidur ketika satu hari memiliki dua sesi. Kolom `province/city` berasal dari formulir; tidak ada kecamatan fiktif.

Database v2 memakai nama tabel baru agar volume PostgreSQL lama dapat dipertahankan tanpa `DROP TABLE`. Ini versi checkpoint: migrasi produksi final dan kontrol akses masih diperlukan.

## Kunci, grain, dan metadata

| Tabel | PK | Natural key / keunikan | FK / relasi | Baris fixture |
| --- | --- | --- | --- | ---: |
| dim_participant_v2 | id | respondent_id (unique index) | Satu profil ke banyak sesi/harian | 19 |
| dim_date_v2 | id | date (unique index) | Satu tanggal ke banyak sesi/harian | 30 |
| dim_session_v2 | id | name (unique) | Satu jenis sesi ke banyak pengukuran | 2 |
| fact_bp_session_v2 | id | participant_id + date_id + session_id (unique constraint) | Tiga FK ke dimensi | 1140 |
| fact_daily_behavior_v2 | id | participant_id + date_id (unique constraint) | Dua FK ke dimensi | 570 |
| dataset_state_v2 | id (singleton 1) | Metadata batch, bukan dimensi tambahan | Sumber, jenis data, jumlah harian, quality_json | 1 |

Diagram menampilkan kolom utama; implementasi lengkap juga menyimpan pekerjaan, pendidikan, aktivitas umum dan konteks sebelum pengukuran. Tidak ada kolom nama/kontak di warehouse. `conditions_json` memuat sebelas jawaban riwayat, bukan identitas. FK non-null, sementara sel pengukuran/perilaku dapat null; validitas sesi dihitung dari jumlah pembacaan.

PK surrogate tidak harus tetap sama setelah reload. Idempotensi didefinisikan sebagai kesamaan natural key, nilai, jumlah baris, dan hash isi natural setelah input yang sama dimuat ulang. Warehouse audit memeriksa PK, FK, unique constraints **dan unique indexes**, orphan, serta hash tanpa nama.

`load_warehouse()` hanya mengganti tabel v2 dalam transaksi. Pada kegagalan, seluruh penggantian di-rollback. Tabel lama di luar daftar v2 tidak disentuh. Pemeriksaan CP2 yang mengubah isi dilakukan pada PostgreSQL sementara `toba_cp2_test`; database aktif diperiksa hanya melalui transaksi READ ONLY, tidak di-reload.

Jalankan `python -m etl.verify_warehouse` dengan `DATABASE_URL` yang sengaja dipilih untuk inspeksi SELECT-only. Tidak ada `create_all`, seed, atau commit pada perintah tersebut. Bukti eksekusi tersedia di `docs/CP2_DATA_READINESS.md` dan `reports/cp2/`.
