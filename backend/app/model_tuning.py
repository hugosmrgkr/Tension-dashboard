"""Week 10 offline tuning: synthetic data, grouped validation, historical test.

Does not load a database or promote artifacts to the serving directory.
Inner validation estimates unseen-ID performance within the training calendar;
the short training calendar cannot support a purged temporal inner split.
"""
import hashlib
import json
import platform
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.model_selection import GroupKFold, ParameterGrid
from threadpoolctl import threadpool_limits

from .baseline import CONFIG, FEATURES, TARGET, leakage_audit, make_training, partitions, sha256, text_sha256
from .model_comparison import HYPERPARAMETERS, LEARNED, NAIVE, build_model, metrics
from .pipeline import prepare

GRIDS = {
    'Random Forest': {'max_depth': [2, 5], 'min_samples_leaf': [2, 5], 'max_features': [.6, 1.0]},
    'Hist Gradient Boosting': {'max_iter': [60, 120], 'learning_rate': [.03, .05], 'min_samples_leaf': [5, 10]},
}
LIMITATION = (
    'DATA SINTETIS / SIMULASI. Inner GroupKFold memisahkan ID, tetapi kalender fit/validasi '
    'dapat beririsan dan target window training berkorelasi. Ini bukan validasi forecasting '
    'kronologis penuh. Test CP3 sudah pernah diperiksa; evaluasi ulang bersifat historis, '
    'bukan holdout baru. Sampel kecil; bukan validasi klinis atau hasil data aktual. '
    'Persetujuan target diasumsikan untuk tugas ini; bukti akademik belum direkam dalam artefak aktif.'
)


def candidates():
    """Bounded, declared search including original settings; no test-dependent grid."""
    return {name: [dict(HYPERPARAMETERS[name], **params) for params in ParameterGrid(GRIDS[name])]
            if name in GRIDS else [dict(HYPERPARAMETERS[name])] for name in LEARNED}


def configured(name, params):
    model = build_model(name)
    return model.set_params(**{'regressor__' + key: value for key, value in params.items()})


def grouped_search(train):
    """Accept TRAIN ONLY so test labels cannot participate in search/selection."""
    if train.respondent_id.nunique() < 4:
        raise ValueError('Minimal 4 ID training diperlukan untuk 4-fold grouped validation.')
    splits = list(GroupKFold(n_splits=4).split(train, groups=train.respondent_id))
    fold_info = []
    for number, (fit_idx, val_idx) in enumerate(splits):
        fit, val = train.iloc[fit_idx], train.iloc[val_idx]
        assert not set(fit.respondent_id) & set(val.respondent_id)
        fold_info.append(dict(fold=number, fit_rows=len(fit), validation_rows=len(val),
                              fit_ids=sorted(fit.respondent_id.unique()),
                              validation_ids=sorted(val.respondent_id.unique()),
                              fit_target_end_max=fit.target_end.max(), validation_origin_min=val.asof_date.min(),
                              chronological=bool(fit.target_end.max() <= val.asof_date.min())))
    trials, predictions = [], {}
    with threadpool_limits(limits=1):
        for name, settings in candidates().items():
            for params in settings:
                key = name + '|' + json.dumps(params, sort_keys=True)
                values = np.full(len(train), np.nan)
                fold_scores = []
                for number, (fit_idx, val_idx) in enumerate(splits):
                    fit, val = train.iloc[fit_idx], train.iloc[val_idx]
                    model = configured(name, params).fit(fit[FEATURES], fit.target)
                    values[val_idx] = model.predict(val[FEATURES])
                    # Verify preprocessing uses only the fold fit data.
                    np.testing.assert_allclose(model.named_steps['impute'].statistics_,
                                               fit[FEATURES].median().fillna(0).to_numpy())
                    imputed = model.named_steps['impute'].transform(fit[FEATURES])
                    np.testing.assert_allclose(model.named_steps['scale'].mean_, imputed.mean(axis=0))
                    fold_scores.append(dict(fold=number, **metrics(val.target, values[val_idx])))
                assert np.isfinite(values).all()
                trials.append(dict(key=key, model=name, params=params,
                                   original=params == HYPERPARAMETERS[name],
                                   validation=metrics(train.target, values), folds=fold_scores))
                predictions[key] = values
    # Deterministic rule fixed before any test evaluation.
    rank = lambda row: (row['validation']['rmse'], row['validation']['mae'], row['key'])
    best = {name: min([row for row in trials if row['model'] == name], key=rank) for name in LEARNED}
    selected = min(best.values(), key=rank)
    return dict(trials=trials, best=best, selected=selected, predictions=predictions, folds=fold_info,
                naive_validation=metrics(train.target, train.past_7d_sbp))


def load_tuning(folder):
    """Verify LF/CRLF-stable metrics and strict binary model hash."""
    folder = Path(folder)
    manifest = json.loads((folder / 'tuning_manifest.json').read_text(encoding='utf-8'))
    if manifest['metrics_hash_mode'] != 'utf8-lf-v1' or manifest['model_file'] != 'selected_model.joblib':
        raise ValueError('Kontrak manifest tuning tidak valid')
    if text_sha256(folder / 'tuning_metrics.json') != manifest['metrics_sha256']:
        raise ValueError('Hash metrik tuning tidak cocok')
    if sha256(folder / 'selected_model.joblib') != manifest['model_sha256']:
        raise ValueError('Hash model tuning tidak cocok')
    result = json.loads((folder / 'tuning_metrics.json').read_text(encoding='utf-8'))
    if result['run_id'] != manifest['run_id'] or result['target'] != TARGET or result['schema_version'] != 1:
        raise ValueError('Kontrak hasil tuning tidak valid')
    return result


def run_tuning(profile_csv, daily_csv, out_dir, report_dir):
    out, report = Path(out_dir).resolve(), Path(report_dir).resolve()
    root = Path(__file__).resolve().parents[2]
    # Never overwrite CP3/P2 serving artifacts, even via an alternate CLI path.
    if out != root / 'models' / 'tuning_week10' or report != root / 'reports' / 'week10_tuning':
        raise ValueError('Output wajib models/tuning_week10 dan reports/week10_tuning; artefak aktif dilindungi.')
    inputs = [pd.read_csv(path, dtype=str, keep_default_na=False) for path in (profile_csv, daily_csv)]
    prepared = prepare(*inputs, synthetic=True)
    if any(not row['respondent_id'].startswith('SIM') for row in prepared[0]):
        raise ValueError('Tuning ini hanya menerima data sintetis SIM.')
    parts = partitions(make_training(*prepared[:3]))
    train, test = parts['train'], parts['test']
    search = grouped_search(train)
    selected = search['selected']  # Selection locked BEFORE historical test scoring.
    scores, fitted, audits, test_predictions = [], {}, {}, {}
    naive_test = test.past_7d_sbp.to_numpy()
    scores.append(dict(model=NAIVE, stage='reference', params={}, validation=search['naive_validation'],
                       historical_test=metrics(test.target, naive_test)))
    test_predictions[NAIVE] = naive_test
    with threadpool_limits(limits=1):
        for name in LEARNED:
            original = next(row for row in search['trials'] if row['model'] == name and row['original'])
            for stage, trial in [('original', original), ('selected_configuration', search['best'][name])]:
                key = name + ' / ' + stage
                model = configured(name, trial['params']).fit(train[FEATURES], train.target)
                audits[key] = leakage_audit(train, test, model)
                values = model.predict(test[FEATURES])
                scores.append(dict(model=name, stage=stage, params=trial['params'], validation=trial['validation'],
                                   historical_test=metrics(test.target, values)))
                test_predictions[key] = values
                if trial['key'] == selected['key']:
                    fitted['selected'] = model
    provenance = dict(profile_sha256=text_sha256(profile_csv), daily_sha256=text_sha256(daily_csv),
                      prepared_content_sha256=prepared[3]['prepared_content_sha256'],
                      code_sha256={name: text_sha256(Path(__file__).with_name(name)) for name in
                                   ['model_tuning.py', 'model_comparison.py', 'baseline.py', 'pipeline.py', 'bp_policy.py', 'survey_schema.py']},
                      versions=dict(python=platform.python_version(), sklearn=sklearn.__version__, numpy=np.__version__,
                                    pandas=pd.__version__, joblib=joblib.__version__))
    run_id = hashlib.sha256(json.dumps(dict(provenance=provenance, config=CONFIG, grid=GRIDS), sort_keys=True).encode()).hexdigest()[:20]
    result = dict(schema_version=1, run_id=run_id, status='DATA SINTETIS / SIMULASI', target=TARGET,
                  target_approval='assumed_for_this_task_not_independently_verified', target_approved=False,
                  is_synthetic=True, is_diagnosis=False, real_model_validated=False, promoted_to_serving=False,
                  cutoff=parts['cutoff'], rows_training=len(train), rows_test=len(test),
                  train_ids=sorted(train.respondent_id.unique()), test_ids=sorted(test.respondent_id.unique()),
                  features=FEATURES, seed=CONFIG['seed'], grids=GRIDS, folds=search['folds'],
                  selection=dict(model=selected['model'], params=selected['params'],
                                 rule='minimum pooled out-of-fold RMSE, then MAE, then canonical candidate key; learned models only',
                                 beats_naive_validation=selected['validation']['rmse'] < search['naive_validation']['rmse']),
                  trials=search['trials'], comparison=scores, leakage_audits=audits, provenance=provenance,
                  historical_test=True, limitation=LIMITATION)
    out.mkdir(parents=True, exist_ok=True)
    report.mkdir(parents=True, exist_ok=True)
    joblib.dump(fitted['selected'], out / 'selected_model.joblib')
    (out / 'tuning_metrics.json').write_bytes((json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode())
    (out / 'tuning_manifest.json').write_text(json.dumps(dict(run_id=run_id, metrics_hash_mode='utf8-lf-v1',
        metrics_sha256=text_sha256(out / 'tuning_metrics.json'), model_file='selected_model.joblib',
        model_sha256=sha256(out / 'selected_model.joblib')), indent=2)+'\n', encoding='utf-8')
    pd.DataFrame([dict(model=row['model'], params=json.dumps(row['params'], sort_keys=True), original=row['original'],
                       **row['validation']) for row in search['trials']]).to_csv(report / 'validation_trials.csv', index=False)
    pd.DataFrame([dict(model=row['model'], stage=row['stage'], split=split, **row[split])
                  for row in scores for split in ['validation', 'historical_test']]).to_csv(report / 'comparison.csv', index=False)
    predictions = test[['respondent_id', 'asof_date', 'target']].rename(columns={'target': 'actual'}).copy()
    for name, values in test_predictions.items():
        predictions[name] = values
    predictions.to_csv(report / 'historical_test_predictions.csv', index=False, float_format='%.15g')
    validation = train[['respondent_id', 'asof_date', 'target']].copy()
    for name in LEARNED:
        validation[name] = search['predictions'][search['best'][name]['key']]
    validation.to_csv(report / 'validation_predictions.csv', index=False, float_format='%.15g')
    return load_tuning(out)
