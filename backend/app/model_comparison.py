"""P2-01: perbandingan tiga pendekatan regresi untuk target usulan future_7d_mean_sbp.

DATA SINTETIS / SIMULASI. Target belum disetujui dosen (target_approved=False).

Aturan yang dikunci SEBELUM skor test dihitung (lihat urutan di run_comparison):
1. Window, fitur, target, dan split train/test memakai modul baseline CP3 tanpa diubah.
2. Pemilihan model memakai validasi leave-ID-out (GroupKFold) HANYA di dalam train.
3. Kriteria pemilihan: RMSE validasi terkecil di antara model terlatih (tie -> MAE terkecil).
4. Test utama dihitung sekali setelah pemilihan terkunci; tidak dipakai untuk memilih/tuning.
5. Imputasi, scaling, dan model di-fit hanya pada data training (fold atau train penuh).
"""
import hashlib
import json
import platform
from datetime import date
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from .baseline import (CONFIG, FEATURES, TARGET, leakage_audit, make_training, partitions, sha256, text_sha256)
from .pipeline import prepare

SCHEMA_VERSION = 1
STATUS = 'DATA SINTETIS / SIMULASI - EKSPERIMEN'
NAIVE = 'Naive 7-day mean'
SEED = CONFIG['seed']
VALIDATION_FOLDS = 4
ARTIFACT_PREFIX = 'comparison'

# Hiperparameter tetap dan konservatif karena train hanya puluhan window. Tidak ada tuning pada test.
HYPERPARAMETERS = {
    'Linear Regression': {},
    'Random Forest': dict(n_estimators=300, max_depth=5, min_samples_leaf=5, max_features=0.6, random_state=SEED, n_jobs=1),
    'Hist Gradient Boosting': dict(max_iter=120, learning_rate=0.05, max_depth=3, min_samples_leaf=5, l2_regularization=1.0, random_state=SEED),
}


def build_model(name):
    """Pipeline identik untuk semua kandidat: impute(median) -> scale -> regressor. Langkah bernama sama
    agar audit leakage baseline CP3 dapat dipakai ulang."""
    regressors = {
        'Linear Regression': lambda: LinearRegression(),
        'Random Forest': lambda: RandomForestRegressor(**HYPERPARAMETERS[name]),
        'Hist Gradient Boosting': lambda: HistGradientBoostingRegressor(**HYPERPARAMETERS[name]),
    }
    if name not in regressors:
        raise KeyError(f'Algoritma tidak dikenal: {name}')
    return Pipeline([('impute', SimpleImputer(strategy='median', keep_empty_features=True)),
                     ('scale', StandardScaler()), ('regressor', regressors[name]())])


LEARNED = list(HYPERPARAMETERS)


def column_key(name):
    """Nama kolom CSV/JSON untuk prediksi suatu model."""
    return name.lower().replace(' ', '_').replace('-', '_')


def metrics(actual, predicted):
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    r2 = float(r2_score(actual, predicted)) if len(actual) > 1 and np.ptp(actual) > 0 else None
    return dict(mae=float(mean_absolute_error(actual, predicted)),
                rmse=float(np.sqrt(mean_squared_error(actual, predicted))), r2=r2, n=int(len(actual)))


def validate(train):
    """Validasi leave-ID-out di dalam train: tidak ada responden yang muncul di fit dan validasi sekaligus."""
    ids = train.respondent_id.nunique()
    if ids < 3:
        raise ValueError('Validasi membutuhkan minimal 3 ID pada train.')
    folds = min(VALIDATION_FOLDS, ids)
    splitter = GroupKFold(n_splits=folds)
    predictions = {name: np.full(len(train), np.nan) for name in [NAIVE, *LEARNED]}
    fold_of = np.full(len(train), -1)
    fold_info = []
    for fold, (fit_index, val_index) in enumerate(splitter.split(train, groups=train.respondent_id)):
        fit, val = train.iloc[fit_index], train.iloc[val_index]
        if set(fit.respondent_id) & set(val.respondent_id):
            raise AssertionError('ID bocor antara fit dan validasi')
        fold_of[val_index] = fold
        predictions[NAIVE][val_index] = val.past_7d_sbp.to_numpy()
        for name in LEARNED:
            predictions[name][val_index] = build_model(name).fit(fit[FEATURES], fit.target).predict(val[FEATURES])
        fold_info.append(dict(fold=fold, fit_rows=len(fit), validation_rows=len(val),
                              validation_ids=sorted(val.respondent_id.unique().tolist())))
    actual = train.target.to_numpy()
    scores = {name: metrics(actual, values) for name, values in predictions.items()}
    per_fold = {name: [dict(fold=f, **metrics(actual[fold_of == f], predictions[name][fold_of == f])) for f in range(folds)]
                for name in predictions}
    return dict(scores=scores, per_fold=per_fold, folds=fold_info, predictions=predictions, actual=actual, fold_of=fold_of)


def select_model(validation_scores):
    """Aturan pemilihan tetap: RMSE validasi terkecil di antara model terlatih; tie -> MAE."""
    ranked = sorted(LEARNED, key=lambda name: (validation_scores[name]['rmse'], validation_scores[name]['mae'], name))
    best = ranked[0]
    return dict(selected=best, ranking=ranked, rule='RMSE validasi leave-ID-out terkecil; tie dipecah dengan MAE lalu nama',
                beats_naive_on_validation=validation_scores[best]['rmse'] < validation_scores[NAIVE]['rmse'])


def run_comparison(profile_csv, day_csv, out_dir, report_dir=None):
    profiles, days, sessions, quality = prepare(pd.read_csv(profile_csv, dtype=str, keep_default_na=False),
                                                pd.read_csv(day_csv, dtype=str, keep_default_na=False), synthetic=True)
    if any(not row['respondent_id'].startswith('SIM') for row in profiles):
        raise ValueError('Perbandingan P2-01 hanya untuk ID sintetis SIM; data aktual tidak boleh diberi label simulasi.')
    frame = make_training(profiles, days, sessions)
    parts = partitions(frame)
    train, test = parts['train'], parts['test']

    # Tahap 1-2: validasi dan pemilihan hanya memakai train. Test belum disentuh.
    validation = validate(train)
    selection = select_model(validation['scores'])

    # Tahap 3: fit penuh pada train, audit leakage, dan evaluasi test sekali setelah pemilihan terkunci.
    fitted = {name: build_model(name).fit(train[FEATURES], train.target) for name in LEARNED}
    audits = {name: leakage_audit(train, test, fitted[name]) for name in LEARNED}
    test_predictions = {NAIVE: test.past_7d_sbp.to_numpy(), **{name: fitted[name].predict(test[FEATURES]) for name in LEARNED}}
    test_scores = {name: metrics(test.target.to_numpy(), values) for name, values in test_predictions.items()}

    rows = test[['respondent_id', 'asof_date', 'target_start', 'target_end', 'target']].rename(
        columns={'asof_date': 'date', 'target': 'actual'}).copy()
    for name, values in test_predictions.items():
        key = column_key(name)
        rows[key] = values
        rows[key + '_residual'] = rows.actual - values

    provenance = dict(text_hash_mode='utf8-lf-v1', profile_sha256=text_sha256(profile_csv), daily_sha256=text_sha256(day_csv),
                      prepared_content_sha256=quality['prepared_content_sha256'], code_sha256=text_sha256(__file__),
                      baseline_code_sha256=text_sha256(Path(__file__).with_name('baseline.py')),
                      versions=dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__,
                                    sklearn=sklearn.__version__, joblib=joblib.__version__))
    run_id = hashlib.sha256(json.dumps(dict(provenance=provenance, config=CONFIG, hp=HYPERPARAMETERS, folds=VALIDATION_FOLDS),
                                       sort_keys=True).encode()).hexdigest()[:20]

    selected = selection['selected']
    comparison = [dict(model=name, kind='baseline naif' if name == NAIVE else 'terlatih',
                       validation=validation['scores'][name], test=test_scores[name],
                       hyperparameters=HYPERPARAMETERS.get(name, {})) for name in [NAIVE, *LEARNED]]
    result = dict(
        schema_version=SCHEMA_VERSION, run_id=run_id, status=STATUS, target=TARGET, target_approved=False,
        horizon_days=7, is_synthetic=True, is_diagnosis=False, real_model_validated=False,
        description='Rerata SBP harian t+1..t+7; origin akhir hari t. Usulan target, belum disetujui dosen.',
        dataset=f'{len(profiles)} ID sintetis, {len(days)} ID-tanggal, {len(sessions)} sesi; {len(frame)} complete windows.',
        features=FEATURES, feature_ranges={name: dict(min=float(train[name].min()), max=float(train[name].max())) for name in FEATURES},
        config=CONFIG, cutoff=parts['cutoff'], seed=SEED, validation_folds=len(validation['folds']),
        split='Held-out ID + purge label kronologis + target uji tidak overlap (identik baseline CP3); validasi model = leave-ID-out di dalam train',
        rows_training=len(train), rows_test=len(test), respondents_train=sorted(train.respondent_id.unique().tolist()),
        respondents_test=sorted(test.respondent_id.unique().tolist()), folds=validation['folds'],
        comparison=comparison, validation_per_fold=validation['per_fold'], selection=selection, selected_model=selected,
        leakage_audit=audits[selected], leakage_audit_all={name: {k: v for k, v in audit.items()} for name, audit in audits.items()},
        actual_vs_predicted=json.loads(rows.to_json(orient='records', double_precision=15)),
        provenance=provenance, as_of=date.today().isoformat(), tuned=False,
        limitation=(f'DATA SINTETIS. Train hanya {len(train)} window dari {train.respondent_id.nunique()} ID dan test utama hanya '
                    f'{len(test)} origin dari {test.respondent_id.nunique()} ID, sehingga selisih antar-model tidak stabil dan tidak '
                    'membuktikan generalisasi. Window train saling berkorelasi. Target belum disetujui dosen. Bukan validasi klinis atau diagnosis.'),
        warnings=[w for w in [
            f'Test hanya {len(test)} origin: metrik test sangat tidak stabil.' if len(test) < 30 else None,
            f'Train hanya {len(train)} window: model non-linear mudah overfit.' if len(train) < 200 else None,
            'Tidak ada model terlatih yang mengalahkan baseline naif pada validasi.' if not selection['beats_naive_on_validation'] else None] if w],
    )
    out = Path(out_dir)
    out.mkdir(exist_ok=True, parents=True)
    slug = selected.lower().replace(' ', '_')
    model_file = f'{slug}_synthetic.joblib'
    joblib.dump(fitted[selected], out / model_file)
    result['model_file'] = model_file
    result['model_sha256'] = sha256(out / model_file)
    metrics_path = out / f'{ARTIFACT_PREFIX}_metrics.json'
    metrics_path.write_bytes((json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode('utf-8'))
    (out / f'{ARTIFACT_PREFIX}_manifest.json').write_bytes((json.dumps(dict(
        schema_version=1, metrics_hash_mode='utf8-lf-v1', run_id=run_id, metrics_sha256=text_sha256(metrics_path),
        model_file=model_file, model_sha256=result['model_sha256'], target_approved=False), indent=2) + '\n').encode('utf-8'))
    (out / 'MODEL_CARD.md').write_text(render_model_card(result), encoding='utf-8')

    if report_dir:
        report = Path(report_dir)
        report.mkdir(exist_ok=True, parents=True)
        train.to_csv(report / 'train_windows.csv', index=False)
        test.to_csv(report / 'test_windows.csv', index=False)
        val_frame = train[['respondent_id', 'asof_date', 'target']].copy()
        val_frame['fold'] = validation['fold_of']
        for name, values in validation['predictions'].items():
            val_frame[name] = values
        val_frame.to_csv(report / 'validation_predictions.csv', index=False, float_format='%.15g')
        rows.to_csv(report / 'test_predictions.csv', index=False, float_format='%.15g')
        pd.DataFrame([dict(model=c['model'], split=split, **c[split]) for c in comparison for split in ('validation', 'test')]
                     ).to_csv(report / 'comparison_metrics.csv', index=False)
        (report / 'experiment.json').write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    return result


def _fmt(value, digits=3):
    return 'n/a' if value is None else f'{value:.{digits}f}'


def render_model_card(result):
    rows = '\n'.join(f"| {c['model']} | {c['kind']} | {_fmt(c['validation']['rmse'])} | {_fmt(c['validation']['mae'])} | "
                     f"{_fmt(c['test']['rmse'])} | {_fmt(c['test']['mae'])} | {_fmt(c['test']['r2'])} |" for c in result['comparison'])
    selection = result['selection']
    hp = '\n'.join(f"- **{name}**: `{json.dumps(params, sort_keys=True)}`" for name, params in HYPERPARAMETERS.items())
    warnings = '\n'.join(f'- {w}' for w in result['warnings']) or '- Tidak ada peringatan otomatis.'
    return f'''# Model Card - {result['selected_model']} ({result['status']})

> **DATA SINTETIS / SIMULASI. Bukan diagnosis, bukan hasil penelitian aktual. Target `{result['target']}` belum disetujui dosen (`target_approved=false`).**

Dibuat otomatis oleh `backend/app/model_comparison.py` (run `{result['run_id']}`). Jangan edit manual; jalankan ulang `python -m etl.run_model_comparison`.

## Tujuan dan target
Memperkirakan rerata SBP harian (mmHg) pada tujuh hari setelah origin (akhir hari t). Horizon dan target adalah usulan teknis yang menunggu keputusan dosen.

## Data
{result['dataset']} Fitur: `{', '.join(result['features'])}`. Train {result['rows_training']} window, test utama {result['rows_test']} origin. Seed {result['seed']}.

## Protokol evaluasi
- Split train/test identik baseline CP3: ID held-out + purge label kronologis (cutoff {result['cutoff']}) + target uji tidak overlap.
- Pemilihan model memakai validasi leave-ID-out ({result['validation_folds']} fold) di dalam train. Aturan: {selection['rule']}.
- Test dihitung sekali setelah pemilihan terkunci. Imputer median, scaler, dan regressor di-fit hanya pada data fit.
- Audit leakage baseline CP3 lulus untuk semua model (tidak ada ID atau kunci ID-tanggal yang dibagi, label train selesai sebelum origin test).

## Hasil (mmHg)
| Model | Jenis | RMSE validasi | MAE validasi | RMSE test | MAE test | R2 test |
|---|---|---:|---:|---:|---:|---:|
{rows}

Model terpilih berdasarkan validasi: **{result['selected_model']}** (peringkat: {', '.join(selection['ranking'])}). Mengalahkan baseline naif pada validasi: **{'ya' if selection['beats_naive_on_validation'] else 'tidak'}**.

## Hiperparameter (tetap, tanpa tuning)
{hp}

## Peringatan otomatis
{warnings}

## Keterbatasan
{result['limitation']}

## Penggunaan yang tidak diperbolehkan
Diagnosis atau klasifikasi hipertensi; keputusan medis; klaim performa pada responden aktual; menyebutnya model final penelitian sebelum target disetujui dosen dan data aktual divalidasi.
'''


def load_comparison(folder):
    """Muat artefak perbandingan dengan verifikasi hash. Tidak pernah mengisi metrik pengganti."""
    folder = Path(folder)
    try:
        manifest = json.loads((folder / f'{ARTIFACT_PREFIX}_manifest.json').read_text(encoding='utf-8'))
        if manifest.get('metrics_hash_mode') != 'utf8-lf-v1':
            raise ValueError('Mode hash tidak dikenal')
        if text_sha256(folder / f'{ARTIFACT_PREFIX}_metrics.json') != manifest['metrics_sha256']:
            raise ValueError('Hash metrik tidak cocok')
        if sha256(folder / manifest['model_file']) != manifest['model_sha256']:
            raise ValueError('Hash model tidak cocok')
        result = json.loads((folder / f'{ARTIFACT_PREFIX}_metrics.json').read_text(encoding='utf-8'))
        if result['schema_version'] != SCHEMA_VERSION or result['run_id'] != manifest['run_id'] or result['target'] != TARGET:
            raise ValueError('Kontrak artefak tidak cocok')
        return {**result, 'available': True, 'artifact_integrity_verified': True}
    except (OSError, ValueError, KeyError, TypeError):
        return dict(available=False, message='Artefak perbandingan model belum tersedia atau integritasnya gagal. Jalankan etl.run_model_comparison secara offline; metrik tidak diganti data contoh.')
