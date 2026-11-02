# Model ML belum tersedia

Belum ada artefak `.joblib` / `.onnx` karena ZIP Streamlit asli hanya memuat placeholder metrik dan klasifikasi berbasis aturan ambang tekanan darah.

Jangan membuat klaim bahwa 85,3% adalah akurasi model terlatih.

Setelah dataset valid tersedia, latih minimal 3 algoritma, lakukan split berdasarkan partisipan untuk menghindari kebocoran pengukuran berulang, tuning dan evaluasi pada test set. Simpan artefak model tervalidasi, catat versi, skema input/output, metrik, dan model card; lalu tambah route `/api/predict` yang benar-benar memuat artefak.
