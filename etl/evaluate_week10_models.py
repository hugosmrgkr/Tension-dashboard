"""Evaluate saved week-10 predictions; no training, tuning, database or serving changes."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

from backend.app.baseline import sha256, text_sha256
from backend.app.model_comparison import LEARNED, NAIVE
from backend.app.model_evaluation import evaluate_saved_run
from etl.run_week10_tuning import active_hashes

ROOT = Path(__file__).resolve().parents[1]
CARD_MARKER = '\n## Analisis error Minggu 10\n'


def card_section(analysis):
    selected = analysis['selected_model']
    stats = next(row for row in analysis['summary'] if row['model'] == selected and
                 row['stage'] == 'selected_configuration' and row['split'] == 'historical_test')
    return (CARD_MARKER + '\nDATA SINTETIS / SIMULASI; evaluasi test historis, bukan holdout baru.\n\n'
            + f"Model {selected}: MAE {stats['mae']:.3f}, RMSE {stats['rmse']:.3f} mmHg; "
            + f"R2 {stats['r2']:.3f}; bias (prediksi - aktual) {stats['bias']:+.3f} mmHg.\n\n"
            + f"{stats['under_count']} prediksi terlalu rendah, {stats['over_count']} terlalu tinggi, "
            + f"{stats['equal_count']} sama dalam toleransi numerik 1e-9 mmHg (bukan batas klinis). "
            + f"Error absolut terbesar {stats['max_absolute_error']:.3f} mmHg.\n\n"
            + f"Dibanding naif pada pasangan yang sama: {analysis['selected_vs_naive']['better']} lebih kecil, "
            + f"{analysis['selected_vs_naive']['worse']} lebih besar, {analysis['selected_vs_naive']['equal']} sama. "
            + 'Perbandingan pasangan ini deskriptif, bukan uji signifikansi.\n\n'
            + 'Hanya 7 origin dari 7 ID, satu origin per ID. Error per responden hanya deskriptif; '
            + 'tidak membuktikan kestabilan individu, perbedaan kelompok, atau sebab error. '
            + 'Tidak ada interval ketidakpastian tervalidasi atau klaim diagnosis.\n\n'
            + 'Model terlatih dipilih dari validasi; hasil test tidak mengubah pemilihan. '
            + 'Baseline naif tetap pembanding dan unggul pada eksperimen ini. '
            + 'Laporan: docs/WEEK10_EVALUATION_REPORT.md; tabel/grafik: reports/week10_evaluation/.\n')


def refresh_card():
    """Keep an evaluated card on tuning reruns only when source predictions still match."""
    report = ROOT / 'reports/week10_evaluation'
    model = ROOT / 'models/tuning_week10'
    if not (report / 'evaluation.json').exists():
        return
    analysis = json.loads((report / 'evaluation.json').read_text(encoding='utf-8'))
    current = json.loads((model / 'tuning_metrics.json').read_text(encoding='utf-8'))
    if analysis['run_id'] != current['run_id']:
        return
    for path, digest in analysis['input_hashes'].items():
        if text_sha256(ROOT / path) != digest:
            return
    card = model / 'MODEL_CARD.md'
    original = card.read_text(encoding='utf-8').split(CARD_MARKER)[0]
    card.write_text(original + card_section(analysis), encoding='utf-8')


def table(frame, columns):
    labels = [label for _, label in columns]
    lines = ['| ' + ' | '.join(labels) + ' |', '|' + '|'.join(['---'] * len(labels)) + '|']
    for _, row in frame.iterrows():
        values = []
        for name, _ in columns:
            value = row[name]
            values.append('Tidak tersedia' if pd.isna(value) else f'{value:.3f}' if isinstance(value, float) else str(value))
        lines.append('| ' + ' | '.join(values) + ' |')
    return '\n'.join(lines)


def figures(errors, selected, folder):
    folder.mkdir(exist_ok=True)
    active = errors[(errors.model == NAIVE) | (errors.stage == 'selected_configuration')]
    chosen = active[active.model == selected]
    fig, axes = plt.subplots(2, 2, figsize=(12, 9), layout='constrained')
    colors = ['#8495a7', '#245781', '#3d8997', '#b88a42']
    low = min(active.actual.min(), active.prediction.min()) - 1
    high = max(active.actual.max(), active.prediction.max()) + 1
    for (name, group), color in zip(active.groupby('model', sort=False), colors):
        axes[0, 0].scatter(group.actual, group.prediction, label=name, color=color, s=32)
    axes[0, 0].plot([low, high], [low, high], '--', color='gray')
    axes[0, 0].set(xlabel='Aktual (mmHg)', ylabel='Prediksi (mmHg)', xlim=(low, high), ylim=(low, high),
                   title='Aktual vs prediksi | semua metode')
    axes[0, 0].legend(fontsize=7)
    axes[0, 1].scatter(chosen.prediction, chosen.residual, color='#245781')
    for row in chosen.itertuples():
        axes[0, 1].annotate(row.respondent_id, (row.prediction, row.residual), xytext=(4, 4), textcoords='offset points', fontsize=7)
    axes[0, 1].axhline(0, color='gray', linestyle='--')
    axes[0, 1].set(xlabel='Prediksi (mmHg)', ylabel='Residual = aktual - prediksi (mmHg)', title=selected + ' | residual')
    axes[0, 1].margins(x=.15, y=.15)
    axes[1, 0].hist(chosen.signed_error, bins=5, color='#245781', edgecolor='white')
    axes[1, 0].axvline(0, color='gray', linestyle='--')
    axes[1, 0].set(xlabel='Error = prediksi - aktual (mmHg)', ylabel='Jumlah origin', title='Arah error | hanya 7 origin')
    axes[1, 0].yaxis.set_major_locator(plt.MaxNLocator(integer=True))
    ids = sorted(active.respondent_id.unique())
    for index, (name, group) in enumerate(active.groupby('model', sort=False)):
        positions = [i + (index - 1.5) * .2 for i in range(len(ids))]
        axes[1, 1].bar(positions, group.set_index('respondent_id').loc[ids].absolute_error, width=.2, label=name, color=colors[index])
    axes[1, 1].set_xticks(range(len(ids)), ids, rotation=25)
    axes[1, 1].set(ylabel='Error absolut (mmHg)', title='Error per ID | satu origin per ID')
    axes[1, 1].legend(fontsize=6)
    fig.suptitle('DATA SINTETIS / SIMULASI - TEST HISTORIS, n=7; bukan validasi klinis', fontsize=12)
    fig.savefig(folder / 'error_analysis.png', dpi=160)
    plt.close(fig)


def execute():
    before = active_hashes()
    model_dir, source = ROOT / 'models/tuning_week10', ROOT / 'reports/week10_tuning'
    protected_tuning = {path.name: sha256(path) for path in model_dir.iterdir() if path.is_file() and path.name != 'MODEL_CARD.md'}
    result, summary, errors, per_id = evaluate_saved_run(model_dir, source,
        ROOT / 'data/sample/Data_Responden_Sintetis.csv', ROOT / 'data/sample/Data_Harian_Sintetis.csv')
    report = ROOT / 'reports/week10_evaluation'
    report.mkdir(exist_ok=True)
    test_evidence = {'status': 'Belum ada bukti JUnit pada direktori laporan.'}
    if (report / 'tests.xml').exists():
        suites = list(ET.parse(report / 'tests.xml').getroot().iter('testsuite'))
        totals = {name: sum(int(suite.get(name, 0)) for suite in suites)
                  for name in ['tests', 'failures', 'errors', 'skipped']}
        test_evidence = dict(**totals, passed=totals['tests']-totals['failures']-totals['errors']-totals['skipped'],
                             junit_sha256=sha256(report / 'tests.xml'))
    summary.to_csv(report / 'metrics_and_bias.csv', index=False, float_format='%.15g')
    errors.to_csv(report / 'all_errors.csv', index=False, float_format='%.15g')
    per_id.to_csv(report / 'errors_per_respondent.csv', index=False, float_format='%.15g')
    selected = result['selection']['model']
    chosen = errors[(errors.model == selected) & (errors.stage == 'selected_configuration')]
    largest = chosen.sort_values(['absolute_error', 'respondent_id'], ascending=[False, True]).head(5)
    largest.to_csv(report / 'largest_selected_model_errors.csv', index=False, float_format='%.15g')
    top_all = errors.sort_values('absolute_error', ascending=False).groupby(['model', 'stage'], sort=False).head(3)
    top_all.to_csv(report / 'largest_errors_each_method.csv', index=False, float_format='%.15g')
    input_paths = ['models/tuning_week10/tuning_metrics.json',
                   'reports/week10_tuning/historical_test_predictions.csv', 'reports/week10_tuning/validation_predictions.csv']
    analysis = dict(schema_version=1, run_id=result['run_id'], selected_model=selected,
                    status='DATA SINTETIS / SIMULASI', historical_test=True, trained=False,
                    selection_changed=False, promoted_to_serving=False,
                    error_definition='signed_error = prediction - actual; residual = actual - prediction',
                    input_hashes={path: text_sha256(ROOT / path) for path in input_paths},
                    summary=json.loads(summary.to_json(orient='records', double_precision=15)),
                    selected_vs_naive=dict(better=int((chosen.absolute_error_minus_naive < -1e-9).sum()),
                                           worse=int((chosen.absolute_error_minus_naive > 1e-9).sum()),
                                           equal=int((chosen.absolute_error_minus_naive.abs() <= 1e-9).sum())),
                    largest_errors=json.loads(largest.to_json(orient='records', double_precision=15)),
                    limitation=result['limitation'])
    (report / 'evaluation.json').write_text(json.dumps(analysis, indent=2, ensure_ascii=False, allow_nan=False)+'\n', encoding='utf-8')
    figures(errors, selected, report / 'figures')
    test = summary[summary.split == 'historical_test']
    metrics_table = table(test, [('model', 'Model'), ('stage', 'Tahap'), ('mae', 'MAE'), ('rmse', 'RMSE'),
                                ('r2', 'R2'), ('bias', 'Bias'), ('under_count', 'Terlalu rendah'), ('over_count', 'Terlalu tinggi')])
    largest_table = table(largest, [('respondent_id', 'ID'), ('asof_date', 'Origin'), ('actual', 'Aktual'),
                                    ('prediction', 'Prediksi'), ('absolute_error', 'Error absolut'),
                                    ('naive_absolute_error', 'Error naif'), ('direction', 'Arah')])
    stats = test[(test.model == selected) & (test.stage == 'selected_configuration')].iloc[0]
    worst = largest.iloc[0]
    rf = test[test.model == 'Random Forest'].set_index('stage')
    doc = f'''# Evaluasi dan analisis error Minggu 10

DATA SINTETIS / SIMULASI. Run sumber `{result['run_id']}`.

## Apa yang dikerjakan
Evaluasi ini membaca metrik/manifest tuning terverifikasi dan prediksi tersimpan.
Tidak melakukan training, tuning, pemilihan ulang, akses database, atau promosi model.
Target/fitur/split tetap milik eksperimen tuning. Persetujuan target diasumsikan untuk
tugas ini; hasilnya tidak menjadi bukti persetujuan akademik atau hasil data aktual.

## Verifikasi sumber dan perhitungan
- Hash manifest/model tuning diverifikasi dengan `load_tuning`.
- Hash dua CSV dan fingerprint prepared harus sama dengan provenance.
- ID-origin dan nilai target CSV dicocokkan dengan split dari sumber; duplikat,
  baris hilang/tambahan, NaN/inf dan target berbeda ditolak.
- Metrik dihitung ulang dari pasangan prediksi-aktual, dicocokkan dengan artefak
  terverifikasi. Validasi OOF dihitung ulang untuk naif dan konfigurasi terpilih tiap
  algoritma. OOF konfigurasi original tidak disimpan oleh langkah tuning, sehingga
  statistik error tambahan original pada validasi tidak dibuat-buat.
- **Signed error/bias = prediksi - aktual**: positif terlalu tinggi, negatif terlalu
  rendah. **Residual = aktual - prediksi**, tandanya berlawanan. Toleransi 1e-9 hanya
  untuk kesamaan numerik, bukan batas aman/validitas klinis.
- MAE/RMSE/bias/error absolut dalam mmHg; R2 tanpa satuan, bukan akurasi persen.

## Perbandingan test historis
Tabel validasi dan statistik tambahan tersedia pada `metrics_and_bias.csv`.

{metrics_table}

## Interpretasi yang didukung hasil
RF dan HGB membaik setelah tuning dibanding pengaturan awal pada validasi dan test
historis. Linear Regression tetap model terlatih yang dipilih **dari validasi**;
baseline naif tetap mengungguli model terlatih secara agregat pada eksperimen ini.
Tidak menggunakan hasil test untuk memilih pemenang baru atau mengubah grid.

Perbaikan agregat tidak berarti setiap prediksi membaik. Pada RF, error absolut
terbesar naik dari {rf.loc['original', 'max_absolute_error']:.3f} menjadi
{rf.loc['selected_configuration', 'max_absolute_error']:.3f} mmHg, meskipun RMSE turun.
Pada {selected}, error absolut lebih kecil dari naif pada
{analysis['selected_vs_naive']['better']} pasangan dan lebih besar pada
{analysis['selected_vs_naive']['worse']} pasangan. Ini perbandingan deskriptif, bukan
uji signifikansi atau alasan untuk memilih model berdasarkan test.

Untuk {selected}, bias historis {stats['bias']:+.3f} mmHg;
{int(stats['under_count'])} dari {int(stats['n'])} prediksi terlalu rendah dan
{int(stats['over_count'])} terlalu tinggi. Arah ini hanya merangkum tujuh origin,
bukan bukti bias populasi yang konsisten. MAE {stats['mae']:.3f} mmHg menunjukkan
rata-rata besar error, sedangkan RMSE {stats['rmse']:.3f} lebih sensitif pada error besar.

## Lima error terbesar model terpilih
Setiap target merupakan rerata SBP tujuh hari setelah origin (rentang pada sampel ini
{chosen.forecast_start.min()} sampai {chosen.forecast_end.max()}), bukan satu pembacaan tekanan darah. Kolom arah `under` berarti
terlalu rendah dan `over` berarti terlalu tinggi. Semua angka dihitung sebelum pembulatan.

{largest_table}

Error terbesar terjadi pada {worst.respondent_id}: {worst.absolute_error:.3f} mmHg.
Pada contoh yang sama, baseline naif memperkirakan {worst.naive_prediction:.3f} mmHg
dengan error {worst.naive_absolute_error:.3f} mmHg. Jadi penyesuaian model terlatih
tidak selalu memperbaiki pembanding sederhana pada setiap contoh.
Ini temuan deskriptif, bukan bukti profil, obat atau gaya hidup tertentu menyebabkan
kesalahan. Tidak mengklaim penyebab error tanpa eksperimen/analisis tambahan.

## Error per responden dan grafik
`errors_per_respondent.csv` memuat statistik per metode dan ID; hanya **satu origin
per ID** sehingga MAE per ID sama dengan error absolut satu contoh dan R2 tidak
tersedia. Jangan meranking kestabilan individu atau membuat kesimpulan demografi.

![Aktual-prediksi, residual, arah error, dan error per ID](../reports/week10_evaluation/figures/error_analysis.png)

Grafik: (1) aktual vs prediksi empat metode, (2) residual model terpilih,
(3) histogram signed error dengan sampel tujuh, (4) error absolut per ID.
Histogram tidak digunakan untuk mengklaim normalitas. Tidak ada interval keyakinan
atau klaim signifikansi statistik dari sampel ini.

## Keterbatasan dan keputusan
{result['limitation']}

Hasil validasi OOF dipakai saat memilih/tuning, sehingga bukan evaluasi eksternal
yang independen. Kalender inner CV beririsan; window training berkorelasi.
Semua origin test historis berada pada tanggal yang sama, sehingga belum menilai
perubahan performa antarperiode. Bukti di sini tidak menentukan penyebab naif unggul.
Tabel error memiliki 49 baris (tujuh metode/konfigurasi pada tujuh origin), bukan
49 contoh independen.

Keputusan teknis: pertahankan hasil tuning sebagai eksperimen terpisah. Jangan
menyebut model lebih akurat pada responden aktual. Langkah penelitian berikutnya
memerlukan dataset aktual tervalidasi dan kalender lebih panjang untuk evaluasi
waktu/prospektif; model serving aktif tidak diganti dalam pekerjaan ini.

## Reproduksi dan file hasil
Jalankan dari root dengan environment proyek:

```powershell
.\\.venv\\Scripts\\python.exe -m etl.evaluate_week10_models
```

Notebook: `notebooks/06_evaluasi_error_minggu10.ipynb`.
Kode: `backend/app/model_evaluation.py`, `etl/evaluate_week10_models.py`.
Tabel/JSON/gambar: `reports/week10_evaluation/`.
Model card diperbarui hanya di `models/tuning_week10/MODEL_CARD.md`.
Hasil pemeriksaan: `reports/week10_evaluation/verification.json`.
Tidak perlu menjalankan training ulang; skrip menolak prediksi/sumber yang tidak cocok.

## Pengujian
Perintah: `python -m pytest backend/tests/test_week10_evaluation.py backend/tests/test_week10_tuning.py backend/tests/test_p2_model_comparison.py -q -p no:cacheprovider --junitxml=reports/week10_evaluation/tests.xml`.
Ringkasan JUnit tersedia pada eksekusi laporan ini: `{json.dumps(test_evidence, sort_keys=True)}`.
Tes memeriksa arah/besar error, penolakan NaN/inf dan target/ID tidak cocok,
rekomputasi metrik, tidak ada pemanggilan fit saat evaluasi, serta model card yang
idempoten dan menolak sumber stale. Notebook dieksekusi tanpa output error dan
grafik diperiksa secara visual. Frontend/browser dan PostgreSQL tidak diuji ulang
karena pekerjaan ini hanya evaluasi offline, tanpa perubahan pada jalur tersebut.
'''
    (ROOT / 'docs/WEEK10_EVALUATION_REPORT.md').write_text(doc, encoding='utf-8')
    refresh_card()
    if before != active_hashes():
        raise RuntimeError('Artefak model aktif berubah.')
    after = {path.name: sha256(path) for path in model_dir.iterdir() if path.is_file() and path.name != 'MODEL_CARD.md'}
    if protected_tuning != after:
        raise RuntimeError('Binary/metrik/manifest tuning berubah selama evaluasi.')
    verification = dict(run_id=result['run_id'], source_and_prediction_keys_verified=True,
                         recomputed_metrics_match_artifact=True, active_models_unchanged=True,
                         tuning_binary_metrics_manifest_unchanged=True, trained=False, database_accessed=False,
                         targeted_tests=test_evidence,
                         code_sha256={name: text_sha256(ROOT / name) for name in
                                      ['backend/app/model_evaluation.py', 'etl/evaluate_week10_models.py']},
                         generated_hashes={str(path.relative_to(report)): sha256(path) for path in report.rglob('*')
                                           if path.is_file() and path.name != 'verification.json'})
    (report / 'verification.json').write_text(json.dumps(verification, indent=2)+'\n', encoding='utf-8')
    print(f"Run {result['run_id']} | {len(errors)} pasangan model-origin | {len(chosen)} origin model terpilih")
    print(f"Bias {stats['bias']:+.3f} mmHg | under={int(stats['under_count'])}, over={int(stats['over_count'])}")
    return analysis


if __name__ == '__main__':
    execute()
