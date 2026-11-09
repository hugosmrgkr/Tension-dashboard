# Reproduce synthetic baseline artifacts offline, without opening a database.
import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from backend.app.baseline import run_experiment,load_experiment
ROOT=Path(__file__).resolve().parents[1]

def write_evidence(result,report):
    report=Path(report);figures=report/'figures';figures.mkdir(parents=True,exist_ok=True)
    scores=pd.DataFrame(result['scores']);scores.to_csv(report/'metrics.csv',index=False)
    predictions=pd.read_csv(report/'primary_predictions.csv')
    fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
    for key,label in [('naive','Naive 7-day mean'),('linear','Linear Regression')]:
        axes[0].scatter(predictions.actual,predictions[key],label=label)
        axes[1].scatter(predictions[key],predictions.actual-predictions[key],label=label)
    bounds=[predictions[['actual','naive','linear']].min().min(),predictions[['actual','naive','linear']].max().max()]
    axes[0].plot(bounds,bounds,'k--',alpha=.5);axes[0].set(xlabel='Actual future-7-day SBP (mmHg)',ylabel='Predicted SBP (mmHg)',title=f'SYNTHETIC | n={len(predictions)} held-out origins')
    axes[1].axhline(0,color='gray',linestyle='--');axes[1].set(xlabel='Prediction (mmHg)',ylabel='Actual - predicted (mmHg)',title='Residuals | no clinical interpretation')
    for ax in axes:ax.legend(fontsize=8);ax.grid(alpha=.2)
    fig.savefig(figures/'predictions_residuals.png',dpi=150);plt.close(fig)
    fig,ax=plt.subplots(figsize=(8,4),layout='constrained');scores.set_index('model')[['mae','rmse']].plot.bar(ax=ax,color=['#245d9f','#d49635'],rot=0)
    ax.set(ylabel='Error (mmHg)',title='SYNTHETIC | primary non-overlapping test targets');fig.savefig(figures/'model_errors.png',dpi=150);plt.close(fig)
    train=pd.read_csv(report/'train_windows.csv');test=pd.read_csv(report/'test_windows.csv')
    fig,ax=plt.subplots(figsize=(10,5),layout='constrained')
    for name,frame in [('train',train),('test',test)]:ax.scatter(pd.to_datetime(frame.asof_date),frame.respondent_id,label=name,alpha=.6)
    ax.axvline(pd.Timestamp(result['cutoff']),color='gray',linestyle='--',label='fit cutoff (labels known)')
    ax.set(xlabel='Origin at end of day',ylabel='Synthetic ID',title='ID holdout + chronological label purge');ax.legend();fig.autofmt_xdate();fig.savefig(figures/'split_timeline.png',dpi=150);plt.close(fig)
    table='\n'.join('| '+row['model']+f" | {row['mae']:.6f} | {row['rmse']:.6f} | {row['r2']:.6f} |" for row in result['scores'])
    worst=predictions.assign(abs_error=lambda f:(f.actual-f.linear).abs()).sort_values('abs_error',ascending=False).iloc[0]
    naive,linear=result['scores'];winner=min(result['scores'],key=lambda row:row['mae'])['model']
    legacy=result['secondary_evaluations']['legacy_subject_only'];rolling=result['secondary_evaluations']['purged_rolling']
    text=f'''# CP3 Baseline Report - DATA SINTETIS / SIMULASI

Dihitung oleh `etl/verify_baseline.py`, bukan pengisian metrik manual. Run `{result['run_id']}`. Target `{result['target']}` **belum disetujui final oleh dosen**. Tidak ada validitas klinis, diagnosis hipertensi, atau hasil penelitian aktual.

## Definisi, fitur dan persyaratan

Origin adalah **akhir hari t**, setelah pengukuran/perilaku t tersedia. SBP sesi = rerata pembacaan SBP diterima parser; SBP harian = rerata sesi yang lolos gate teknis pasangan pembacaan (Pagi/Malam berbobot sama bila keduanya tersedia). Target = rerata tujuh SBP harian **t+1..t+7**, bukan rerata semua sesi dengan bobot hari berbeda. Histori **t-6..t** dan target masing-masing wajib tujuh tanggal berurutan dengan SBP harian tersedia. Window tidak lengkap dilewati; tidak membuat hari palsu. Satu pasangan lengkap pada nomor pembacaan sama dapat dipakai bila tidak ada komponen ambigu. Pasangan silang, komponen parsial dan SBP<=DBP menunggu review dan tidak masuk agregat/model. Ini gate teknis sementara, bukan keputusan klinis; aturan penelitian final harus disetujui dosen.

Fitur: `{', '.join(result['features'])}`. Perilaku hanya dari histori, NA diabaikan pada rerata histori; median training mengisi fitur seluruh historinya kosong. Simpangan baku ddof=0. Profil usia/BMI diasumsikan diketahui sebelum origin pada fixture statis. Ketersediaan profil/late submission aktual belum dibuktikan; tidak mengklaim asumsi ini berlaku pada penelitian aktual.

## Audit leakage dan metode

{result['dataset']} Split ID GroupShuffleSplit: 32% ID holdout, seed 42. Skema lama: {legacy['rows_train']} train / {legacy['rows_test']} test pada kalender sama, {legacy['overlapping_test_target_id_days']} kelebihan ID-hari target test akibat window berurutan. Split lama memang memisahkan subjek dan preprocessing hanya fit train, tetapi belum evaluasi ramalan masa depan ketat.

Evaluasi utama memilih batas **sebelum melihat skor**, 60% kalender observasi = **{result['cutoff']}**. Train `target_end <= cutoff`; test ID terpisah dan `asof_date >= cutoff`; target test per ID berjarak minimal tujuh hari. Hasil **{result['rows_training']} train / {result['rows_test']} test**, {len(result['respondents_train'])} ID train / {len(result['respondents_test'])} ID test. Semua label train sudah diketahui saat origin test pertama.

Audit aktual: `{json.dumps(result['audit'])}`.

Training windows tetap overlap **di dalam train**, sehingga baris train tidak independen. Test utama tidak overlap per ID; tidak ada ID atau kunci pengukuran ID-tanggal dibagi antarsubset. Median imputer dan mean scaler diverifikasi terhadap train saja. Tidak ada tuning/pemilihan cutoff berdasarkan skor test. Jumlah sampel kecil dan satu split tidak membuktikan generalisasi.

## Metrik utama sebenarnya

| Metode | MAE (mmHg) | RMSE (mmHg) | R2 |
|---|---:|---:|---:|
{table}

MAE lebih kecil pada sampel ini: **{winner}**. MAE Linear - naive = **{linear['mae']-naive['mae']:.6f} mmHg**. Bukan uji signifikansi/model klinis terbaik. R2 bukan accuracy persen; bergantung variasi antar-ID dan hanya {result['rows_test']} origin. Tidak ada validation set/tuning atau klaim model final.

## Sensitivitas dan analisis error

Skor subject-only dan purged rolling ada di `experiment.json`; prediksi lengkap di `legacy_predictions.csv` / `rolling_predictions.csv`. Purged rolling memiliki {rolling['rows_test']} baris test namun target saling overlap, sehingga hanya sensitivitas. Skor beda split tidak membuktikan peningkatan model.

Error absolut Linear terbesar: **{worst.respondent_id}, origin {worst.date}**, aktual {worst.actual:.6f}, prediksi {worst.linear:.6f}, residual {worst.actual-worst.linear:.6f} mmHg. Dugaan yang perlu diperiksa: perubahan masa depan tidak tertangkap histori, perbedaan antar-ID holdout, dan train kecil; bukan penyebab terbukti. `error_analysis.csv` mengurutkan seluruh error; `primary_predictions.csv` mempertahankan presisi untuk verifikasi ulang.

{result['limitation']}

## Reproduksi, artefak dan kompatibilitas

Dari root: `python -m etl.verify_baseline`. Membaca dua CSV sintetis dan menulis `models/`, `reports/cp3_baseline/`, laporan ini; tidak membuka DB. Notebook utama `notebooks/03_verifikasi_baseline_cp3.ipynb`: `python -m etl.execute_cp3_notebook`. Notebook 01 merupakan catatan awal, bukan hasil final verifikasi ini.

Versi aktual: `{json.dumps(result['provenance']['versions'])}`. Hash sumber/dataset/kode ada pada provenance. `baseline_manifest.json` memasangkan metrics/model melalui hash; API menolak artefak hilang/rusak. Field lama JSON untuk dashboard dipertahankan dengan tambahan audit/config/run ID. Prediksi joblib hasil reload dibandingkan dengan CSV dalam tes.

Endpoint tetap naive, bukan inferensi Linear Regression, memakai fungsi agregasi yang sama dengan eksperimen dan melaporkan rentang histori/ramalan. Metrik evaluasi berasal dari artefak; kecocokan warehouse dilaporkan terpisah. Sumber non-sintetis tetap dibatasi.

![Split ID dan waktu](../reports/cp3_baseline/figures/split_timeline.png)
![Error utama](../reports/cp3_baseline/figures/model_errors.png)
![Prediksi dan residual](../reports/cp3_baseline/figures/predictions_residuals.png)
'''
    (ROOT/'docs/CP3_BASELINE_REPORT.md').write_text(text,encoding='utf-8')

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-dir',default=str(ROOT/'models'));parser.add_argument('--report-dir',default=str(ROOT/'reports/cp3_baseline'));args=parser.parse_args()
    result=run_experiment(ROOT/'data/sample/Data_Responden_Sintetis.csv',ROOT/'data/sample/Data_Harian_Sintetis.csv',args.output_dir,args.report_dir)
    assert load_experiment(args.output_dir)['available'];write_evidence(result,args.report_dir)
    print(json.dumps({key:result[key] for key in ['run_id','rows_training','rows_test','cutoff','scores','audit']},indent=2))
if __name__=='__main__':main()
