# P2-01: jalankan perbandingan tiga algoritma secara offline pada data SINTETIS. Tidak membuka database.
import argparse
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from backend.app.model_comparison import run_comparison, NAIVE, LEARNED, column_key

ROOT = Path(__file__).resolve().parents[1]


def write_figures(result, report):
    figures = Path(report) / 'figures'
    figures.mkdir(parents=True, exist_ok=True)
    names = [NAIVE, *LEARNED]
    by = {c['model']: c for c in result['comparison']}
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), layout='constrained')
    for ax, split in zip(axes, ('validation', 'test')):
        values = [by[n][split]['rmse'] for n in names]
        ax.bar(range(len(names)), values, color=['#9aa5b1', '#245d9f', '#2e8b57', '#d49635'])
        ax.set_xticks(range(len(names)), names, rotation=15, fontsize=8)
        ax.set(ylabel='RMSE (mmHg)', title=f'SINTETIS | {split} (n={by[names[0]][split]["n"]})')
        ax.grid(alpha=.2, axis='y')
    fig.savefig(figures / 'rmse_validation_vs_test.png', dpi=150)
    plt.close(fig)
    predictions = pd.read_csv(Path(report) / 'test_predictions.csv')
    fig, ax = plt.subplots(figsize=(6, 5), layout='constrained')
    for name in names:
        ax.scatter(predictions.actual, predictions[column_key(name)], label=name, alpha=.7)
    low, high = predictions.actual.min() - 3, predictions.actual.max() + 3
    ax.plot([low, high], [low, high], 'k--', alpha=.5)
    ax.set(xlabel='Aktual (mmHg)', ylabel='Prediksi (mmHg)', title='SINTETIS | aktual vs prediksi (test utama)')
    ax.legend(fontsize=8)
    ax.grid(alpha=.2)
    fig.savefig(figures / 'actual_vs_predicted.png', dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', default=ROOT / 'data/sample/Data_Responden_Sintetis.csv')
    parser.add_argument('--daily', default=ROOT / 'data/sample/Data_Harian_Sintetis.csv')
    parser.add_argument('--out', default=ROOT / 'models/experiments')
    parser.add_argument('--report', default=ROOT / 'reports/p2_model_comparison')
    args = parser.parse_args()
    result = run_comparison(args.profile, args.daily, args.out, args.report)
    write_figures(result, args.report)
    print(f"Run {result['run_id']} | terpilih: {result['selected_model']} | beats naive (val): {result['selection']['beats_naive_on_validation']}")
    for c in result['comparison']:
        print(f"{c['model']:<24} val RMSE {c['validation']['rmse']:.3f} | test RMSE {c['test']['rmse']:.3f} MAE {c['test']['mae']:.3f}")
    for warning in result['warnings']:
        print('PERINGATAN:', warning)


if __name__ == '__main__':
    main()
