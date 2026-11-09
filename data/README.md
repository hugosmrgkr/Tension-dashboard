# Sumber data sintetis (bukan dataset penelitian)

`sample/Data_Responden_Sintetis.csv` adalah profil awal (19 ID, 24 kolom Form Awal).
`sample/Data_Harian_Sintetis.csv` adalah catatan harian (570 baris, 28 kolom Form Harian).
Workbook gabungan pengguna mempunyai sheet `Data_Responden`, `Data_Harian`, dan `Petunjuk`. Dua CSV di atas adalah sumber aktif agar file tidak dihitung dua kali.

- ID `SIM001`–`SIM019` bersifat sintetis.
- Form Awal: satu baris = satu profil. Form Harian: satu baris = satu ID dan tanggal.
- Dua sesi BP per hari, masing-masing dua pasangan pembacaan. Dalam warehouse: 1.140 baris fakta sesi.
- Jam tidur dalam CSV sintetis `06:31` ditafsirkan **6 jam 31 menit** untuk demo. **JANGAN** terapkan otomatis pada respon aktual karena arti pertanyaan masih perlu konfirmasi.
- Missing value tidak diganti nol. Nilai mentah tidak ditimpa. Nama responden tidak masuk database/API.
- Dataset sintetis dilarang disebut hasil penelitian nyata atau dipakai untuk klaim prevalensi.

Hasil audit kualitas tersedia lewat `/api/quality`. Data aktual disimpan terpisah, privat, dan baru dimuat setelah persetujuan dan validasi.
