# Kekurangan CP3 dan panduan melanjutkan pekerjaan

> **Status lanjutan 10 November 2026:** jalur utama 8080 sudah dikonsolidasikan, warehouse sintetis diperbarui secara terbatas dan diuji, serta startup/demo diarahkan ke satu stack permanen. CP3-K02 teknis ditindaklanjuti melalui [CP3_MAIN_CONSOLIDATION_REPORT.md](CP3_MAIN_CONSOLIDATION_REPORT.md); usulan 8081 di dokumen ini adalah riwayat. Keputusan dosen, data aktual, logbook dan kontribusi tidak dianggap selesai oleh konsolidasi tersebut.

Tanggal: 9 November 2026. Proyek: **Toba Health Insight**.

Dokumen ini merupakan serah terima pekerjaan sampai **Demo Tengah / CP3 / Minggu 8**, berdasarkan pemeriksaan terakhir. Status di sini bukan penilaian atau persetujuan dosen. Saat membuat dokumen ini tidak dilakukan perubahan kode aplikasi, pemuatan database, ataupun pengujian ulang seluruh suite.

## 1. Kesimpulan kondisi proyek

Dashboard v1, ETL dua sumber, warehouse PostgreSQL, API, baseline naive dan Linear Regression sudah memiliki implementasi serta bukti pengujian pada **DATA SINTETIS / SIMULASI**. Pekerjaan berikutnya terutama menyelaraskan dokumentasi, menyiapkan demo yang konsisten, melengkapi bukti kerja kelompok, dan mengonfirmasi keputusan akademik.

Jangan mengulang implementasi dari nol atau menganggap semua kode bermasalah. Sebaliknya, jangan menganggap data aktual dan persetujuan penelitian sudah selesai hanya karena tes teknis lulus.

Menurut `Deskripsi_Proyek_DA_DS.pdf` halaman 6:

- Minggu 6: dashboard draf, feature engineering dan split data.
- Minggu 7: baseline + satu algoritma pembanding, notebook dan metrik awal.
- Minggu 8: dashboard v1 berjalan dengan warehouse, laporan baseline, rencana eksperimen, demo tengah dan laporan kemajuan.

Dokumen resmi berada di direktori induk repository. Panduan kerja dan rekomendasi perbaikan harus dibedakan dari persetujuan dosen yang benar-benar tercatat.

## 2. Bekal yang sudah tersedia

| Komponen | Bukti yang perlu dibaca | Batas klaim |
| --- | --- | --- |
| Audit teknis terbaru | [P0_P1_FINAL_AUDIT.md](P0_P1_FINAL_AUDIT.md) | Menggantikan definisi teknis lama yang bertentangan; bukan persetujuan akademik. |
| Hasil tes terbaru | [verification-summary.json](../reports/p0_p1_audit/verification-summary.json) | Bukti eksekusi audit sebelumnya; bukan hasil tes baru setiap kali dokumen dibuka. |
| Dataset pengujian | `data/sample/Data_Responden_Sintetis.csv` dan `data/sample/Data_Harian_Sintetis.csv` | 19 responden sintetis, 570 ID–tanggal, 1.140 sesi; bukan 570 orang atau data primer penelitian. |
| Kontrak data dan warehouse | [DATA_DICTIONARY.md](DATA_DICTIONARY.md), [ERD.md](ERD.md) | Profil, perilaku harian dan BP sesi mempunyai grain berbeda. |
| Baseline terbaru | [CP3_BASELINE_REPORT.md](CP3_BASELINE_REPORT.md), [baseline_metrics.json](../models/baseline_metrics.json), notebook 03 | Target usulan `future_7d_mean_sbp`; `target_approved=false`; bukan diagnosis. |
| Materi demo dan laporan | [CP3_DEMO_SCRIPT.md](CP3_DEMO_SCRIPT.md), [CP3_PROGRESS_REPORT.md](CP3_PROGRESS_REPORT.md), [CP3_FINAL_REPORT.md](CP3_FINAL_REPORT.md) | Sebagian isi masih historis dan perlu diselaraskan dengan audit terbaru. |

Hasil terakhir yang tercatat: backend Windows **73 lulus / 1 legacy dilewati**, backend Linux + PostgreSQL **73 lulus / 1 legacy dilewati**, frontend **10 lulus**, browser **7 lulus**, dan production build berhasil. Browser mencakup delapan halaman, desktop/mobile, filter, prediksi/evaluasi dan empty/error state. Bukti XML/JSON/screenshot tersedia pada `reports/p0_p1_audit/`.

## 3. Daftar pekerjaan yang masih kurang

Nama penanggung jawab sengaja belum diisi. Kolom peran adalah saran pembagian kerja, bukan catatan kontribusi yang sudah terjadi.

| ID | Pekerjaan | Prioritas | Status saat serah terima | Peran yang disarankan | Kriteria selesai |
| --- | --- | --- | --- | --- | --- |
| CP3-K01 | Selaraskan laporan CP3 dengan audit terbaru | Tinggi | BELUM diselaraskan menyeluruh | Dokumentasi + backend/ML | Tidak ada pertentangan run ID, definisi BP/KPI, hasil tes dan sumber bukti; laporan historis diberi penanda jelas. |
| CP3-K02 | Tetapkan satu jalur demo dan lakukan gladi bersih | Tinggi | PERLU dijalankan kembali | Full-stack / QA | Satu URL dan script persiapan yang disepakati; seluruh alur demo berhasil pada kode terbaru dan database demo terisolasi. |
| CP3-K03 | Konfirmasi target, protokol BP, tidur dan KPI | Tinggi | BUTUH KEPUTUSAN dosen/tim | Ketua + penanggung jawab data/ML | Ada catatan keputusan atau daftar pending eksplisit beserta dampaknya; tidak mengubah aturan ilmiah tanpa persetujuan. |
| CP3-K04 | Laporkan progres data aktual dan status izin | Tinggi | Kecukupan aktual BELUM dibuktikan | Data engineer + ketua | Jumlah aktual terverifikasi, sumber/izin dan kendala tercatat secara privat; penerimaan demo sintetis untuk CP3 dikonfirmasi. |
| CP3-K05 | Tegaskan pengguna, pertanyaan analitik dan tujuan | Sedang | Bukti final belum ditemukan | Data analyst + ketua | Ada ringkasan pengguna utama, pertanyaan keputusan, KPI dan tujuan model; status persetujuan proposal jelas. |
| CP3-K06 | Lengkapi logbook, asistensi, kontribusi dan deklarasi AI | Sedang | Bukti lengkap belum ditemukan di berkas yang diperiksa | Seluruh anggota | Riwayat faktual tersedia; pembagian presentasi sesuai kontribusi; penggunaan AI dijelaskan. |

### CP3-K01 — Sinkronisasi dokumentasi

File yang perlu ditinjau:

- [CP3_FINAL_REPORT.md](CP3_FINAL_REPORT.md): masih mencantumkan run lama `242a4f84499a00fc1028` dan hasil 59 tes backend / 9 frontend. Artefak audit terbaru memakai run `5d3bed0d6591cd2bc09d`, dengan hasil tes pada bagian 2 di atas. Skor fixture bersih tidak berubah, tetapi provenance/run berubah.
- [CP3_PROGRESS_REPORT.md](CP3_PROGRESS_REPORT.md): masih menyatakan aturan sesi baseline dibedakan dari sesi analitik. Jalur terbaru memakai gate pasangan pembacaan bersama pada ETL, API dan baseline.
- [CP3_CHECKLIST.md](CP3_CHECKLIST.md): beberapa bukti menunjuk hasil CP3 lama. Bedakan bukti historis dengan regression tests setelah audit P0/P1.
- [CP3_DEMO_SCRIPT.md](CP3_DEMO_SCRIPT.md) dan [README.md](../README.md): pastikan URL, script, definisi dan bukti terbaru sejalan dengan jalur demo yang dipilih.

Definisi yang harus konsisten:

1. Responden aktif = ID unik dengan sedikitnya satu catatan harian diterima ETL pada filter aktif. Bukan hanya ID dengan BP valid.
2. Catatan harian diterima tidak berarti semua kolom terisi. Missing non-kunci tetap NA dan dilaporkan.
3. Sesi valid sementara memakai pasangan SBP/DBP bernomor sama. Pasangan silang, komponen parsial atau tidak konsisten ditahan dari derived BP sebagai pending review.
4. Gate tersebut bersifat teknis sementara, bukan protokol klinis final. Tidak mengklaim klasifikasi atau diagnosis hipertensi.
5. Evaluasi model memakai artefak eksperimen, bukan menghitung ulang skor dari filter dashboard.

Jika laporan dibuat generator, periksa juga [build_cp3_final_report.py](../etl/build_cp3_final_report.py) agar regenerasi tidak mengembalikan keterangan usang. Jangan mengganti angka secara manual tanpa membaca artefak dan hasil tes yang dirujuk. Simpan hasil pengujian lama sebagai histori; jangan menimpa bukti lama lalu menyebutnya pengujian baru.

### CP3-K02 — Kesiapan demo

Ada dua lingkungan terisolasi:

| Lingkungan | Konfigurasi | Port frontend/API | Kegunaan |
| --- | --- | --- | --- |
| Demo CP3 | [compose.cp3-demo.yaml](../compose.cp3-demo.yaml), [start_cp3_demo.ps1](../scripts/start_cp3_demo.ps1) | 8081 / 8001 | Jalur yang dijelaskan dalam naskah demo dan README. |
| Audit P0/P1 | [compose.p0-p1-audit.yaml](../compose.p0-p1-audit.yaml) | 8082 / 8002 | Lingkungan bukti browser dan integrasi audit terbaru. |

Pada pemeriksaan terakhir sebelum serah terima, endpoint 8080/8081/8082 tidak merespons dan Docker daemon tidak tersedia. Ini kondisi lingkungan saat diperiksa, bukan bukti bug baru aplikasi. Jangan menganggap demo otomatis sedang aktif karena pernah berhasil diuji.

Rekomendasi: pertahankan **8081 sebagai jalur presentasi** karena sudah memiliki script persiapan, tetapi build dan verifikasi ulang dengan kode terbaru. 8082 tetap menjadi lingkungan audit. Jika tim memilih jalur berbeda, selaraskan seluruh petunjuk dan URL secara eksplisit.

Urutan persiapan dari root project, setelah Docker Desktop aktif:

```powershell
# Script ini membangun stack demo terpisah dan dapat memuat fixture
# HANYA ke database demo toba_cp3_demo jika database tersebut kosong.
# Baca script dan pastikan nama project/target tetap sesuai sebelum menjalankan.
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start_cp3_demo.ps1

# Pemeriksaan HTTP read-only setelah stack demo siap.
.venv\Scripts\python.exe -m etl.verify_cp3_demo --url http://127.0.0.1:8081
```

Perhatian: verifier HTTP mempunyai default output laporan. Tentukan `--output` ke folder bukti baru bila ingin mempertahankan seluruh bukti sebelumnya. Script start bukan perintah read-only: ia memang melakukan initial load pada DB demo kosong. Jangan mengganti targetnya menjadi warehouse aktif.

Gladi bersih wajib mencakup:

- [ ] Label **DATA SINTETIS / SIMULASI** terlihat; 19 profil / 570 harian / 1.140 sesi sesuai fixture.
- [ ] Delapan halaman terbuka tanpa error browser/API.
- [ ] KPI, filter tanggal/ID/Pagi–Malam, cross-filter, reset dan ekspor konsisten.
- [ ] Pembanding periode ditunjukkan pada rentang yang benar-benar mempunyai data pembanding.
- [ ] Prediksi menampilkan output mmHg, histori/horizon, status target usulan dan batasan.
- [ ] Evaluasi menampilkan artefak tersedia, run ID yang sesuai dan kecocokan batch warehouse.
- [ ] Empty/error state tidak mengisi angka/grafik palsu; gunakan tes terisolasi atau simulasi response browser, bukan mengosongkan database aktif.
- [ ] Notebook 03, laporan dan screenshot asli tersedia sebagai cadangan; cadangan tidak diklaim sebagai demo live.
- [ ] Semua anggota mampu menjelaskan bagian yang dibawakan dalam alur 5–10 menit.

Jika perubahan dilakukan, jalankan pemeriksaan yang sesuai dan catat hasil nyata. Perintah dasar:

```powershell
.venv\Scripts\python.exe -m pytest backend/tests -q -p no:cacheprovider
.venv\Scripts\python.exe -m etl.import_data --synthetic --dry-run --summary
Push-Location frontend
npm test
npm run build
$env:CP3_BROWSER_BASE_URL='http://127.0.0.1:8081'
$env:CP3_REPORT_DIR='../reports/cp3_handoff_verification'
npm run test:browser
Pop-Location
```

Backend default di atas memakai SQLite in-memory. Jangan menyebutnya pengujian PostgreSQL baru. Jika mengulang integrasi PostgreSQL, gunakan database khusus `toba_cp2_test` sesuai guard di [conftest.py](../backend/tests/conftest.py), bukan database aktif. Tidak perlu mengulang training atau seluruh tes hanya untuk perubahan redaksional; jalankan tes relevan bila kode/artefak/integrasi berubah, serta smoke check saat menyiapkan demo.

### CP3-K03 — Keputusan yang harus dibawa ke dosen

| Pertanyaan | Kondisi sekarang | Dampak keputusan |
| --- | --- | --- |
| Apakah target `future_7d_mean_sbp` disetujui? | Usulan, `target_approved=false`. Histori t−6 sampai t; target t+1 sampai t+7; origin akhir hari t. | Menentukan framing, horizon, kebutuhan data dan evaluasi. |
| Berapa minimum pasangan BP dan hari valid? | Gate teknis sementara; kasus ambigu ditahan. | Mengubah coverage, KPI valid, jumlah window dan sampel model. |
| Apa arti jawaban tidur aktual? | Konversi durasi hanya untuk fixture sintetis; aktual menunggu klarifikasi. | Menghindari salah tafsir waktu tidur sebagai jumlah jam atau pecahan hari. |
| Bagaimana review anomali, tanggal dan koreksi duplikat? | Konflik dikarantina, raw dipertahankan; tidak memilih first/last otomatis. | Memerlukan reviewer, alasan, versi koreksi dan aturan analisis. |
| Apakah KPI/pengguna/judul sudah final? | Arah kerja tersedia; bukti pengesahan belum ditemukan. | Menentukan cerita demo dan manfaat dashboard. |
| Apakah demo sintetis diterima pada CP3 saat data primer dikumpulkan? | Belum ditemukan bukti penerimaan khusus. | Membedakan kesiapan prototipe dari pemenuhan akademik data readiness. |

Catat tanggal, pihak yang menyetujui, keputusan, alasan dan file terdampak. Bila belum ada jawaban, tulis **pending**, bukan membuat persetujuan atau keputusan ilmiah atas nama dosen.

### CP3-K04 — Status pengumpulan data aktual

Siapkan ringkasan faktual: tanggal pembaruan, jumlah ID unik, jumlah catatan ID–tanggal, jumlah sesi, cakupan tanggal, kendala missing/duplikasi, status consent/izin dan rencana pengumpulan selanjutnya. Angka harus berasal dari pemeriksaan sumber aktual yang berwenang; dokumen ini tidak menyediakan angka tersebut karena belum dibuktikan.

Brief mensyaratkan minimal 500 baris untuk data primer. **570 catatan sintetis bukan pemenuhan syarat data primer**, dan catatan berulang tidak sama dengan individu independen. Konfirmasikan interpretasi person-day serta kecukupan jumlah responden kepada dosen.

Jangan mempublikasikan nama, kontak, daftar identitas, jawaban kesehatan mentah atau file aktual dalam repository/laporan publik. Data aktual dan laporan rinci harus berada di penyimpanan privat yang sesuai; jangan digabung dengan sintetis atau dibuka melalui API publik. Handoff analisis tidak memberikan otorisasi memuat ulang data aktual/warehouse aktif.

### CP3-K05 dan CP3-K06 — Materi kelompok

Yang perlu disiapkan atau ditautkan jika sebenarnya tersimpan di luar repository:

- Ringkasan pengguna utama, minimal beberapa pertanyaan keputusan dan pemetaan ke KPI/grafik. Jumlah pertanyaan tidak diperlakukan sebagai minimum baru dari dosen.
- Proposal/feedback/asistensi yang membuktikan status persetujuan judul, tujuan dan target.
- Logbook mingguan dan bukti asistensi. PDF halaman 9 menyebut minimal asistensi sekali per dua minggu dan pembaruan logbook setiap minggu.
- Kontribusi masing-masing anggota pada DALIS dan DASI serta pembagian demo sesuai pekerjaan sebenarnya.
- Pernyataan penggunaan AI: alat, kegunaan dan bagian yang diverifikasi manusia. Jangan mengarang kontribusi, riwayat rapat atau verifikasi.

Tidak ditemukan dalam pemeriksaan repository bukan berarti bukti tersebut pasti tidak ada. Ketua perlu mengecek dokumen bersama, LMS atau catatan kelompok sebelum membuat ulang.

## 4. Urutan kerja yang disarankan

1. **Dokumentasi dan QA:** baca audit final serta artefak, lalu kerjakan CP3-K01. Tidak perlu menambah fitur.
2. **Full-stack dan QA:** kerjakan CP3-K02, kumpulkan bukti gladi bersih pada folder baru dan catat lingkungan/versinya.
3. **Ketua dan penanggung jawab data:** jalankan CP3-K03/04 secara paralel tanpa mengubah aturan ilmiah atau data aktif.
4. **Seluruh anggota:** lengkapi CP3-K05/06, kemudian latihan presentasi dan tanya jawab.
5. Tutup handoff dengan catatan hasil, file berubah, tes yang benar-benar dijalankan, masalah tersisa dan keputusan pending.

## 5. Batas pekerjaan

Untuk penutupan CP3 ini, jangan memaksakan tiga algoritma final, tuning lengkap, lima jenis visual advance final, model terbaik final, deployment publik atau uji pengguna formal. Itu bagian tahap berikutnya menurut timeline, bukan alasan melakukan perubahan besar sekarang. Rencana pekerjaan lanjut tetap tersedia di [CP3_NEXT_STEPS.md](CP3_NEXT_STEPS.md).

Tetap berlaku: jangan reset/hapus DB atau volume aktif, jangan ETL commit ke warehouse aktif tanpa persetujuan, jangan mengubah `.env` atau raw aktual, jangan menonaktifkan hash ML, jangan mengarang metrik/screenshot, dan jangan commit/push otomatis. Folder privat yang diabaikan Git tidak otomatis menghapus data sensitif yang sudah terlanjur masuk histori.

## 6. Checklist serah terima selesai

- [ ] CP3-K01 selesai: laporan, definisi dan bukti terbaru konsisten.
- [ ] CP3-K02 selesai: demo terbaru berhasil di satu jalur yang disepakati, dengan bukti dan cadangan.
- [ ] CP3-K03 dicatat: keputusan dosen tersedia atau pending dinyatakan jelas beserta dampaknya.
- [ ] CP3-K04 tersedia: progres data aktual dan status izin dilaporkan faktual; status penerimaan sintetis untuk CP3 jelas.
- [ ] CP3-K05/06 tersedia: pengguna/tujuan, proposal/feedback, logbook, kontribusi dan penggunaan AI dapat ditunjukkan.
- [ ] Tidak ada klaim data aktual, validitas klinis, persetujuan atau hasil tes tanpa bukti.

Penutupan teknis prototipe sintetis dan kelengkapan akademik harus dilaporkan terpisah. Tim tidak dapat menandai keputusan dosen selesai hanya dengan mengubah kode atau checklist.
