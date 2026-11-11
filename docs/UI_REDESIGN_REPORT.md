# Redesign UI — Toba Health Insight

Tanggal: 11 November 2026. Acuan: gambar dan instruksi redesign pengguna.

## Revisi dosen: perbandingan SBP dan DBP dalam satu grafik

Dashboard dan halaman Tren Tekanan Darah kini memiliki panel **Pagi** dan **Malam**.
Setiap panel membandingkan garis **SBP** dan **DBP** pada satu sumbu mmHg dengan
warna dan legenda yang konsisten. Garis DBP memakai pola putus-putus agar mudah
dibedakan. Sampel dihitung per sesi; klik kedua garis tetap memfilter tanggal-sesi.
Panel sesi tanpa data menampilkan empty state, sedangkan nilai kosong tidak diisi nol.

Komponen baru: `SessionPressureLines` di `frontend/src/components/Visuals.jsx`.
Tes frontend revisi: **16 lulus**, termasuk isolasi sesi, pasangan SBP/DBP,
urutan tanggal, missing, empty state dan cross-filter. Screenshot dan hasil 17 tes
browser di bagian laporan awal di bawah adalah bukti sebelum revisi grafik ini;
browser tests belum dijalankan ulang untuk revisi grafik.

## Hasil

Redesign frontend mengikuti sidebar navy sederhana, latar abu terang, kartu putih,
border tipis, dan jarak antarkomponen yang lebih lega. Semua delapan halaman tetap
tersedia. Angka dan jenis KPI mengikuti kontrak API proyek, bukan angka contoh
330/660/94% pada gambar referensi.

| Area / halaman | Perubahan |
| --- | --- |
| Sidebar | Nama produk berupa teks; logo dan ilustrasi dekoratif tidak lagi ditampilkan. Ikon menu tetap tersedia, menu aktif memakai highlight navy. |
| Header dan sumber | Judul lebih jelas, badge sumber tidak diduplikasi di header. Tombol muat ulang menyatu dengan informasi sumber. Label sintetis tetap terlihat. |
| Filter global | Satu kartu, kontrol berukuran konsisten, grid responsif, preset tanggal dan chip filter tetap tersedia. Filter tetap langsung berlaku; tidak ditambah tombol Terapkan yang mengubah perilaku. |
| Dashboard | Hero besar dihapus. Empat KPI dipertahankan. Penjelasan pembanding periode bisa dibuka. Kualitas data dipindahkan setelah grafik agar grafik lebih cepat terlihat. Shortcut detail tren tetap tersedia. |
| Data Partisipan | Menggunakan header, kartu grafik, tabel, input pencarian dan spacing bersama yang lebih ringan. |
| Analisis Faktor Risiko | Kartu grafik, caption, satuan dan tabel tampil konsisten; peringatan asosiasi tetap tersedia. |
| Tren Tekanan Darah | Pagi biru dan Malam navy konsisten pada grafik garis dan boxplot sesi; detail pembacaan dan drill-down dipertahankan. |
| Prediksi Tekanan Darah | Form, hasil, metadata dan panduan menggunakan gaya kartu yang sama; batas eksperimen dan target belum disetujui tetap terlihat. |
| Evaluasi Model | Kartu metrik, visualisasi dan tabel mengikuti tema baru. Nilai eksperimen tidak diubah. |
| Laporan & Ringkasan | Kartu insight, tipografi, caption dan spacing mengikuti tema bersama. |
| Kelola Data | Kartu sumber, kualitas, tabel dan tombol mengikuti tema bersama. Ekspor dan petunjuk ETL tetap tersedia. |
| Ponsel | Sidebar menjadi drawer; filter dapat dilipat, grafik satu kolom, tabel tetap bisa digeser di dalam wadahnya. |

## Alasan desain

- Navy menjadi identitas sidebar dan aksen, bukan warna latar setiap panel.
- Informasi tambahan dapat dibuka, sementara KPI dan grafik mendapat hierarki utama.
- Tema visual dipisahkan dari stylesheet lama agar perubahan presentasi mudah ditinjau.
- Jenis grafik tetap mengikuti implementasi analitik yang tersedia. Grafik kategori
  diagnosis dan angka contoh dari referensi tidak ditambahkan.

## File dibuat / diubah

| File | Peran |
| --- | --- |
| `frontend/src/dashboard-theme.css` (baru) | Lapisan tema visual bersama, breakpoint dan gaya delapan halaman. |
| `frontend/src/main.jsx` | Memuat tema setelah stylesheet dasar. |
| `frontend/src/App.jsx` | Merapikan informasi sumber dan tombol muat ulang. |
| `frontend/src/components/Common.jsx` | Menyederhanakan sidebar/header, font grafik dan posisi default legend. |
| `frontend/src/components/FilterBar.jsx` | Memperjelas judul dan keterangan filter. |
| `frontend/src/components/Visuals.jsx` | Palet dan konsistensi warna sesi. |
| `frontend/src/pages/Pages.jsx` | Menyederhanakan susunan Dashboard tanpa mengganti perhitungan data. |
| `frontend/tests/browser/dashboard.spec.js` | Pemeriksaan sidebar disesuaikan untuk branding teks tanpa gambar dekoratif. |
| `docs/UI_REDESIGN_REPORT.md` (baru) | Laporan ini. |

Backend, ETL, API, database utama, `.env`, data sumber dan artefak ML tidak diubah.
Dokumen pengguna `PANDUAN_VISUAL_CEK_PROGRES_CP3.md` yang sudah ada dibiarkan.

## Pengujian yang benar-benar dijalankan

| Pemeriksaan | Hasil akhir |
| --- | --- |
| `npm test` | **15 lulus**, 0 gagal. |
| `npm run build` | **Lulus**. Vite memberi peringatan bundle JavaScript besar (sekitar 4,92 MB sebelum gzip), terutama Plotly. Bukan error build. |
| `npm run test:browser` | **17 lulus**, 0 gagal pada build akhir, Microsoft Edge headless. |
| Delapan halaman desktop | Diuji lewat browser, termasuk kesesuaian KPI dengan API dan prediksi model. |
| Delapan halaman ponsel | Diuji pada 390 × 844, navigasi dan tidak ada overflow horizontal halaman. |
| Interaksi | Filter ID/tanggal/wilayah/sesi, cross-filter, reset, tooltip, pencarian/halaman tabel, ekspor, empty/error state dan fokus keyboard dasar tercakup tes frontend/browser yang dijalankan. |
| Pemeriksaan visual | Screenshot Dashboard desktop/ponsel dan Evaluasi Model diperiksa langsung; screenshot delapan halaman tersedia. |

Lingkungan browser memakai FastAPI lokal dan **SQLite sementara** yang diisi dua CSV
sintetis melalui pipeline yang sudah ada (19 profil, 570 catatan harian, 1.140 sesi).
Tidak ada ETL commit ke warehouse utama. Docker Desktop tidak aktif, sehingga
pengujian ini **bukan** verifikasi ulang stack Docker/PostgreSQL.

Pada percobaan awal dengan SQLite di memori, 16 tes browser lulus dan satu gagal
karena metadata model tidak tersedia sehingga tombol prediksi nonaktif. Pengujian
diulang memakai file SQLite di direktori sementara (koneksi terpisah) dan seluruh
17 tes lulus. Tidak dilakukan perubahan backend untuk melewati kegagalan tersebut.
Penyebab awal tidak diklaim sebagai bug produksi yang sudah terbukti.

Bukti hasil akhir:

- [Hasil Playwright JSON](../reports/ui_redesign/browser-results.json)
- [Dashboard desktop](../reports/ui_redesign/screenshots/desktop-1.png)
- [Dashboard ponsel](../reports/ui_redesign/screenshots/mobile-1.png)
- [Evaluasi Model](../reports/ui_redesign/screenshots/desktop-6.png)
- Screenshot lain: `reports/ui_redesign/screenshots/desktop-2.png` sampai
  `desktop-8.png`, dan `mobile-2.png` sampai `mobile-8.png`.

## Menjalankan dan batas verifikasi

Untuk preview lokal, pastikan backend tersedia lalu jalankan dari `frontend/`:

```powershell
npm run dev
```

Vite menggunakan proxy backend `http://localhost:8000` secara default. Bila backend
utama hanya tersedia melalui nginx `8080`, tetapkan variabel pada terminal:

```powershell
$env:TOBA_API_PROXY_TARGET='http://127.0.0.1:8080'
npm run dev
```

Untuk menampilkan kode frontend terbaru melalui Docker `8080`, image frontend
perlu dibangun ulang saat Docker Desktop aktif. Tidak ada deployment/rebuild
container utama yang dijalankan dalam pekerjaan ini.

Penyempurnaan opsional berikutnya: ukuran bundle Plotly, pengujian pembaca layar,
dan pengukuran kontras warna formal. Tampilan belum diklaim identik per piksel
dengan gambar referensi; struktur data dan fungsi proyek tetap menjadi acuan.
