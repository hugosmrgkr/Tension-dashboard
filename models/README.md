# Baseline model checkpoint M6–M8

- `baseline_metrics.json`: metrik **hasil eksperimen benar-benar dihitung** dari dua CSV sintetis.
- `linear_regression_synthetic.joblib`: model pembanding awal pada data simulasi. Jangan deploy sebagai model diagnosis. FastAPI endpoint demo menampilkan baseline naif sebagai contoh yang mudah dijelaskan.
- Model baseline naif: rata-rata sistolik 7 hari sebelumnya → perkiraan rata-rata sistolik 7 hari berikutnya.
- Model pembanding: Linear Regression; split berdasarkan ID responden (`GroupShuffleSplit`), tidak mencampurkan responden train/test.
- Hanya baris dengan tujuh hari histori dan tujuh hari target lengkap yang dipakai. Fitur tidak menggunakan data masa depan.
- Eksperimen final minimal tiga model dan tuning akan menjadi pekerjaan berikutnya, setelah data aktual cukup dan target disetujui dosen.
- `baseline_metrics.json` tidak boleh dibaca sebagai bukti evaluasi pada pasien atau masyarakat nyata.
