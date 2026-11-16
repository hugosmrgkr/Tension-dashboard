# Pemisahan delapan halaman aktif

Branch pengerjaan: `chore/split-active-pages`.

## Hasil audit dan routing

Entry aplikasi tetap `frontend/src/main.jsx` menuju `App.jsx`, dengan navigasi hash
dan daftar menu `NAV` dari `components/Common.jsx`. Sebelumnya delapan komponen
aktif diimpor dari `pages/Pages.jsx`. File `pages/Dashboard.jsx` lama dan
`pages/OtherPages.jsx` bukan implementasi yang dipakai routing aktif.

Sekarang `App.jsx` mengimpor langsung delapan modul aktif berikut. Nama hash,
props halaman, state filter, pembacaan API, autentikasi, pembatalan request dan
pengaturan loading/error/empty tetap dipertahankan.

| Menu | Modul dalam `frontend/src/pages/` | Pemilik tugas |
|---|---|---|
| Dashboard | `Dashboard.jsx` | Ruben |
| Data Partisipan | `DataPartisipan.jsx` | Aldi |
| Analisis Faktor Risiko | `AnalisisFaktorRisiko.jsx` | Nahesson |
| Tren Tekanan Darah | `TrenTekananDarah.jsx` | Ruben |
| Prediksi Tekanan Darah | `PrediksiTekananDarah.jsx` | Hugo |
| Evaluasi Model | `EvaluasiModel.jsx` | Nahesson |
| Laporan & Ringkasan | `LaporanRingkasan.jsx` | Kasih |
| Kelola Data | `KelolaData.jsx` | Aldi |

## Komponen bersama dan kompatibilitas

- `components/page-shared/Analysis.jsx` menampung `ChartCard` dan `Explainer` yang
  sebelumnya berada pada `Pages.jsx`. Struktur DOM dan class CSS-nya tetap sama.
- `Pages.jsx` menjadi re-export, bukan tempat implementasi halaman. Nama ekspor
  lama (`FaktorRisiko`, `Tren`, `Prediksi`, `Evaluasi`, `Laporan` dan lainnya)
  tetap kompatibel. Ekspor `QualitySummary` juga dipertahankan dari `Dashboard.jsx`.
- KPI dan ringkasan kualitas khusus Dashboard tetap bersama halaman tersebut;
  helper agregasi tren tetap di `TrenTekananDarah.jsx`; fallback baseline, helper
  nama kolom dan format metrik tetap di `EvaluasiModel.jsx`.
- Semua badan fungsi halaman/helper dipindahkan dari sumber aktif tanpa perubahan
  logika. Perubahan hanya pada batas modul, import dan deklarasi export.
- `Common.jsx`, `Visuals.jsx`, filter, helper API, dan semua CSS tidak diubah.

## Penanganan legacy

Dashboard lama disimpan sebagai `pages/Dashboard.legacy.jsx`, dengan isi asli
dipertahankan. `pages/Dashboard.jsx` sekarang berisi Dashboard aktif hasil ekstraksi
dari `Pages.jsx`, sehingga file yang dikerjakan Ruben tidak ambigu.

`OtherPages.jsx` tetap tersimpan dan tidak diaktifkan. Kedua file legacy tidak
diimpor App, barrel `Pages.jsx`, maupun modul halaman aktif, dan tidak masuk bundle
pengujian/produksi. Jangan menggunakannya sebagai sumber halaman baru.

## Verifikasi yang dijalankan

| Pemeriksaan | Hasil |
|---|---|
| `npm test` | **17 lulus**, 0 gagal |
| `npm run build` | **Berhasil**, 1.601 modul ditransformasi |
| Tes kompatibilitas ekspor | Delapan ekspor `Pages.jsx` identik dengan default export modul aktif; `QualitySummary` tetap tersedia |
| Pemeriksaan dependency graph pengujian | Delapan modul aktif masuk; `Dashboard.legacy.jsx` dan `OtherPages.jsx` tidak masuk |
| Tes perilaku yang sudah ada | Navigasi/render delapan halaman, nilai API, filter/cross-filter/reset, ekspor, paginasi, prediksi, evaluasi/fallback, auth, missing dan empty/error state lulus |
| Browser dan runtime Docker | Tidak dijalankan ulang dalam refactor ini |

Build masih memberi peringatan chunk JavaScript di atas 500 kB, terutama bundle
Plotly yang sudah digunakan. Ini bukan error build; refactor ini tidak melakukan
perubahan dependency, lazy loading atau optimasi bundle.

## File yang berubah

- `frontend/src/App.jsx`: import delapan halaman aktif secara langsung; switch
  routing dan logika lainnya tetap sama.
- `frontend/src/pages/Pages.jsx`: re-export kompatibilitas.
- Delapan modul halaman pada tabel di atas.
- `frontend/src/pages/Dashboard.legacy.jsx`: arsip file Dashboard lama.
- `frontend/src/components/page-shared/Analysis.jsx`: helper presentasi bersama.
- `frontend/tests/dashboard.test.mjs`: tes kompatibilitas dan pengecualian legacy.
- `docs/ACTIVE_PAGE_SPLIT.md`: peta file dan laporan ini.

## Pedoman kerja paralel

Setiap anggota mengubah halaman miliknya dan komponen khusus fiturnya. Perubahan
pada `App.jsx`, barrel `Pages.jsx`, helper presentasi bersama, filter, grafik umum
dan CSS global dikoordinasikan melalui Hugo. Jangan memindahkan kembali seluruh
implementasi ke `Pages.jsx`. Halaman lain dibaca sebagai referensi, bukan diedit
bersamaan tanpa koordinasi.

Backend, database, ETL, model, konfigurasi Docker dan data sumber tidak diubah.
Tidak ada commit, push atau merge otomatis.
