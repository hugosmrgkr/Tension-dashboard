"""Reproduce bounded week-10 tuning offline; never connects to a database."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

from backend.app.baseline import sha256
from backend.app.model_tuning import LIMITATION, run_tuning

ROOT = Path(__file__).resolve().parents[1]


def active_hashes():
    return {str(path.relative_to(ROOT)): sha256(path) for path in (ROOT / 'models').rglob('*')
            if path.is_file() and 'tuning_week10' not in path.parts}


def write_summary(result, report, out):
    rows = result['comparison']
    table = '\n'.join(f"| {row['model']} | {row['stage']} | {row['validation']['rmse']:.3f} | "
                       f"{row['validation']['mae']:.3f} | {row['historical_test']['rmse']:.3f} | "
                       f"{row['historical_test']['mae']:.3f} | {row['historical_test']['r2']:.3f} |" for row in rows)
    selected = result['selection']
    text = f'''# Minggu 10 - Eksperimen tuning sintetis

Run: `{result['run_id']}`. Target: `{result['target']}`.

## Tujuan dan batas pekerjaan
Mencari konfigurasi Random Forest dan HistGradientBoosting melalui training/validasi,
dengan Linear Regression dan baseline rerata SBP tujuh hari sebagai pembanding.
Persetujuan target diasumsikan sesuai instruksi pengguna, bukan bukti persetujuan
akademik yang diverifikasi. Tidak mengganti target atau flag artefak serving lama.

## Protokol yang dikunci sebelum test
- Dataset: dua CSV `data/sample/`, 19 ID, 570 ID-tanggal, 1.140 sesi sintetis.
- Fitur dan target memakai pipeline CP3: histori t-6..t, target t+1..t+7.
- Split CP3 tetap: {result['rows_training']} train dari {len(result['train_ids'])} ID;
  {result['rows_test']} test historis dari {len(result['test_ids'])} ID; cutoff {result['cutoff']}.
- Tuning: 8 konfigurasi RF dan 8 HGB; 1 konfigurasi LR pembanding; 4 fold GroupKFold.
  Total 68 fit validasi. Grid kecil ditetapkan dalam kode; konfigurasi P2 asli termasuk.
- Semua kandidat memakai fold yang sama, seed 42, imputer/scaler hanya di-fit pada
  bagian fit fold. Tidak mengimputasi target. Nilai fitur dihitung hanya sampai origin.
- Pilihan: pooled out-of-fold RMSE terendah, lalu MAE, lalu kunci kandidat deterministik.
  Peringkat global ini hanya antara model terlatih; baseline naif selalu dilaporkan.
- `grouped_search` hanya menerima frame train. Pemilihan dikunci sebelum test dihitung.
- Audit split luar memeriksa ID terpisah, tidak ada ID-tanggal bersama, label train
  tersedia sebelum origin test, target test tidak overlap, preprocessing training-only.

## Keterbatasan validasi waktu
Origin train hanya 7-11 September, sedangkan labelnya baru selesai 14-18 September.
Tidak ada pasangan fold train/validasi di kalender ini yang bisa memenuhi label-fit
selesai sebelum origin-validasi. Inner CV mengukur generalisasi ke ID lain dalam
kalender training, bukan strict future forecasting. Fold metadata mencatat kondisi ini.
Grid dipilih setelah tim pernah melihat hasil P2, sehingga ada risiko adaptasi terhadap
dataset lama; tidak disebut sebagai nested/unbiased evaluation. Test lama sudah pernah
diperiksa dan metrik di bawah berlabel historis, bukan holdout baru.

## Hasil sebenarnya
RMSE/MAE dalam mmHg; R2 tanpa satuan. Lebih kecil lebih baik untuk RMSE/MAE.

| Model | Tahap | RMSE validasi | MAE validasi | RMSE test historis | MAE test historis | R2 test historis |
|---|---|---:|---:|---:|---:|---:|
{table}

Model terpilih di antara model terlatih: **{selected['model']}**.
Konfigurasi: `{json.dumps(selected['params'], sort_keys=True)}`.
Mengalahkan naif pada validasi: **{'ya' if selected['beats_naive_validation'] else 'tidak'}**.
RF dan HGB dapat membaik terhadap konfigurasi aslinya tanpa mengalahkan LR atau naif.
Jika pemenang global tetap LR, model terlatih terbaik tidak berubah pada grid ini.
Skor test historis tidak digunakan untuk mengubah pemilihan atau mencari ulang grid.

## Artefak dan reproduksi
- Kode: `backend/app/model_tuning.py`, `etl/run_week10_tuning.py`.
- Notebook: `notebooks/05_tuning_model_minggu10.ipynb`.
- Artefak terpisah: `models/tuning_week10/selected_model.joblib`, metrik, manifest,
  dan model card. Hash teks dinormalisasi LF/CRLF; hash joblib memakai byte persis.
- Bukti: `reports/week10_tuning/validation_trials.csv`, `validation_predictions.csv`,
  `comparison.csv`, `historical_test_predictions.csv`, dan `figures/`.
- Jalankan dari root: `python -m etl.run_week10_tuning` menggunakan environment proyek.
- Notebook juga menjalankan eksperimen dan menampilkan tabel/gambar; menjalankan ulang
  menulis ulang hanya output eksperimen tuning yang disebut di atas.
- Hash semua file model aktif diperiksa sebelum/sesudah eksperimen. Tidak ada promosi
  ke dashboard/API, perubahan database, ETL aktif, `.env`, atau artefak CP3/P2.

## Verifikasi pengerjaan
Regression tests: `python -m pytest backend/tests/test_week10_tuning.py backend/tests/test_p2_model_comparison.py -q -p no:cacheprovider`.
Bukti hasil pengujian dan pemeriksaan ulang tersimpan di
`reports/week10_tuning/verification.json`: jumlah tes lulus/gagal, kesamaan hasil
dua eksekusi, paritas prediksi model tersimpan dengan CSV, kesamaan konfigurasi
original dengan skor P2, dan hash artefak aktif yang dilindungi.
Notebook telah dieksekusi tanpa output error; grafik diperiksa secara visual.
Frontend/browser dan integrasi PostgreSQL tidak diuji ulang pada langkah tuning
offline ini karena tidak ada perubahan pada serving, UI, atau database.

## Penggunaan dan langkah berikutnya
{LIMITATION}

Data aktual harus divalidasi terpisah. Perlu kalender lebih panjang untuk validasi
waktu dengan purge dan evaluasi prospektif baru; jangan memaksa split dari sampel kecil.
Integrasi model tuning ke serving membutuhkan pekerjaan kompatibilitas terpisah.
Eksperimen ini menyelesaikan langkah tuning teknis, bukan seluruh cakupan Minggu 10.
'''
    (ROOT / 'docs/WEEK10_TUNING_REPORT.md').write_text(text, encoding='utf-8')
    (out / 'MODEL_CARD.md').write_text(
        '# Model card - eksperimen tuning Minggu 10\n\n'
        + f"Run `{result['run_id']}`; algoritma {selected['model']}; target `{result['target']}`; horizon 7 hari.\n\n"
        + 'DATA SINTETIS / SIMULASI. 19 ID; 60 window train / 7 origin test historis.\n\n'
        + f"Fitur: {', '.join(result['features'])}.\n\n"
        + f"Konfigurasi: `{json.dumps(selected['params'], sort_keys=True)}`.\n\n"
        + '| Model | Tahap | RMSE val | MAE val | RMSE historis | MAE historis | R2 historis |\n'
        + '|---|---|---:|---:|---:|---:|---:|\n' + table + '\n\n'
        + LIMITATION + '\n\nTidak dipromosikan ke API/dashboard. Bukan diagnosis atau keputusan medis. '
        + 'Rincian protokol dan reproduksi: docs/WEEK10_TUNING_REPORT.md.\n', encoding='utf-8')
    # Retain the evaluated model card only if evaluation inputs still match this run.
    from etl.evaluate_week10_models import refresh_card
    refresh_card()
    figures = report / 'figures'
    figures.mkdir(exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), layout='constrained')
    for ax, split in zip(axes, ['validation', 'historical_test']):
        ax.barh([row['model']+' / '+row['stage'] for row in rows], [row[split]['rmse'] for row in rows], color='#245781')
        ax.set(xlabel='RMSE (mmHg)', title='SINTETIS | '+split)
        ax.tick_params(axis='y', labelsize=7)
        ax.grid(axis='x', alpha=.2)
    fig.savefig(figures / 'rmse_before_after.png', dpi=150)
    plt.close(fig)
    predictions = pd.read_csv(report / 'historical_test_predictions.csv')
    key = selected['model']+' / selected_configuration'
    fig, ax = plt.subplots(figsize=(6, 4), layout='constrained')
    ax.scatter(predictions.actual, predictions[key], color='#245781')
    low = min(predictions.actual.min(), predictions[key].min())
    high = max(predictions.actual.max(), predictions[key].max())
    ax.plot([low, high], [low, high], '--', color='gray')
    ax.set(xlabel='Aktual (mmHg)', ylabel='Prediksi (mmHg)', title='SINTETIS | Test historis, n=7')
    fig.savefig(figures / 'historical_actual_prediction.png', dpi=150)
    plt.close(fig)


def execute():
    before = active_hashes()
    out, report = ROOT / 'models/tuning_week10', ROOT / 'reports/week10_tuning'
    try:
        result = run_tuning(ROOT / 'data/sample/Data_Responden_Sintetis.csv',
                            ROOT / 'data/sample/Data_Harian_Sintetis.csv', out, report)
        write_summary(result, report, out)
    finally:
        if before != active_hashes():
            raise RuntimeError('Hash artefak aktif berubah; investigasi sebelum melanjutkan.')
    print(f"Run {result['run_id']} | {len(result['trials'])} kandidat | terpilih {result['selection']['model']}")
    print('Artefak aktif tidak berubah; tidak ada promosi model. DATA SINTETIS / SIMULASI.')
    return result


if __name__ == '__main__':
    execute()
