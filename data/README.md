# Data penelitian

Tidak disertakan dataset pasien asli. Saat pertama start, backend membuat data sintetis dari fungsi `buat_data_hipertensi_demo` yang disalin dari source Streamlit pengguna.

Syarat tugas dosen: data tabular bukan dari Kaggle, minimal 5.000 baris data publik ATAU 500 baris data primer, dan sedikitnya 10 kolom; diperlukan provenance, izin, dan anonimisasi. 750 baris demo di sini **tidak dihitung** sebagai dataset penelitian yang memenuhi syarat.

Kolom minimal impor: `tanggal`, `kecamatan`, `jenis_kelamin`, `usia`, `bmi`, `aktivitas_fisik_hari_per_minggu`, `pola_makan`, `jam_tidur`, `merokok`, `sistolik`, `diastolik`.

Sangat disarankan `id_partisipan` untuk data longitudinal. Kolom `tingkat_stres` opsional dan default=5. `status_hipertensi` dihitung ulang dari tekanan darah berdasarkan aturan prototipe, sehingga tidak dipercaya mentah dari file.

Tidak menyimpan data nyata di git tanpa izin dan pengamanan. File CSV/XLSX menggantikan dataset aktif dalam database, bukan ditaruh otomatis ke repositori.
