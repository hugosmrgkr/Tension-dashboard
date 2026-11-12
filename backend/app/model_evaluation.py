"""Read-only statistical evaluation of a verified synthetic tuning run; no fitting."""
import numpy as np
import pandas as pd

from .baseline import make_training, partitions, text_sha256
from .model_comparison import LEARNED, NAIVE, metrics
from .model_tuning import load_tuning
from .pipeline import prepare

ERROR_TOLERANCE = 1e-9  # Numerical equality only, not a clinical error threshold.


def error_statistics(actual, predicted):
    actual, predicted = np.asarray(actual, dtype=float), np.asarray(predicted, dtype=float)
    if actual.ndim != 1 or predicted.shape != actual.shape or not len(actual):
        raise ValueError('Actual/predicted wajib vektor nonkosong dengan ukuran sama.')
    if not np.isfinite(actual).all() or not np.isfinite(predicted).all():
        raise ValueError('Evaluasi menolak NaN/inf; tidak mengisi target atau prediksi palsu.')
    signed = predicted - actual
    absolute = np.abs(signed)
    return dict(**metrics(actual, predicted), bias=float(signed.mean()),
                median_absolute_error=float(np.median(absolute)), max_absolute_error=float(absolute.max()),
                over_count=int((signed > ERROR_TOLERANCE).sum()),
                under_count=int((signed < -ERROR_TOLERANCE).sum()),
                equal_count=int((absolute <= ERROR_TOLERANCE).sum()))


def validate_prediction_frame(predictions, expected, actual_column, prediction_columns):
    """Align by ID+origin and check outcomes against source, never trust CSV order."""
    keys = ['respondent_id', 'asof_date']
    required = keys + [actual_column] + prediction_columns
    if any(column not in predictions for column in required):
        raise ValueError('Kolom prediksi tidak lengkap.')
    if predictions[keys].isna().any().any() or predictions.duplicated(keys).any():
        raise ValueError('ID-origin kosong/duplikat pada hasil prediksi.')
    left = predictions.set_index(keys)
    right = expected.set_index(keys)
    if len(left) != len(right) or set(left.index) != set(right.index):
        raise ValueError('Kunci ID-origin tidak cocok dengan split sumber.')
    aligned = left.loc[right.index].reset_index()
    try:
        np.testing.assert_allclose(aligned[actual_column].to_numpy(dtype=float),
                                   right.target.to_numpy(dtype=float), rtol=1e-12, atol=1e-12)
    except (AssertionError, ValueError) as exc:
        raise ValueError('Target pada CSV berbeda dari sumber eksperimen.') from exc
    if not np.isfinite(aligned[[actual_column] + prediction_columns].to_numpy(dtype=float)).all():
        raise ValueError('Target/prediksi nonfinite pada CSV.')
    return aligned


def evaluate_saved_run(model_dir, tuning_report, profile_csv, daily_csv):
    """No estimator.fit/predict or DB access. Recompute metrics from stored predictions."""
    result = load_tuning(model_dir)
    if not result['is_synthetic'] or result.get('promoted_to_serving'):
        raise ValueError('Evaluasi ini khusus artefak tuning sintetis terpisah.')
    for key, path in [('profile_sha256', profile_csv), ('daily_sha256', daily_csv)]:
        if text_sha256(path) != result['provenance'][key]:
            raise ValueError('CSV sumber tidak cocok dengan provenance tuning.')
    inputs = [pd.read_csv(path, dtype=str, keep_default_na=False) for path in (profile_csv, daily_csv)]
    prepared = prepare(*inputs, synthetic=True)
    if prepared[3]['prepared_content_sha256'] != result['provenance']['prepared_content_sha256']:
        raise ValueError('Fingerprint data yang diproses berbeda dari eksperimen.')
    parts = partitions(make_training(*prepared[:3]))
    columns = {NAIVE: NAIVE}
    for name in LEARNED:
        for stage in ['original', 'selected_configuration']:
            columns[name + ' / ' + stage] = name + ' / ' + stage
    historical = validate_prediction_frame(pd.read_csv(tuning_report / 'historical_test_predictions.csv'),
                                           parts['test'], 'actual', list(columns))
    validation = validate_prediction_frame(pd.read_csv(tuning_report / 'validation_predictions.csv'),
                                           parts['train'], 'target', LEARNED)
    comparisons, errors = [], []
    for row in result['comparison']:
        name, stage = row['model'], row['stage']
        key = NAIVE if name == NAIVE else name + ' / ' + stage
        stats = error_statistics(historical.actual, historical[key])
        for metric in ['mae', 'rmse', 'r2', 'n']:
            if not np.isclose(stats[metric], row['historical_test'][metric], rtol=1e-11, atol=1e-11):
                raise ValueError('Metrik CSV test historis tidak cocok dengan artefak terverifikasi.')
        comparisons.append(dict(model=name, stage=stage, split='historical_test', **stats))
        if name == NAIVE:
            values = parts['train'].past_7d_sbp.to_numpy()
        elif stage == 'selected_configuration':
            values = validation[name].to_numpy()
        else:
            # Original OOF predictions are not stored; don't fabricate error statistics.
            values = None
        if values is not None:
            valstats = error_statistics(validation.target, values)
            for metric in ['mae', 'rmse', 'r2', 'n']:
                if not np.isclose(valstats[metric], row['validation'][metric], rtol=1e-11, atol=1e-11):
                    raise ValueError('Metrik OOF tidak cocok dengan artefak terverifikasi.')
            comparisons.append(dict(model=name, stage=stage, split='validation', **valstats))
        for _, sample in historical.iterrows():
            actual, prediction = float(sample.actual), float(sample[key])
            signed = prediction - actual
            naive_prediction = float(sample[NAIVE])
            naive_absolute_error = abs(naive_prediction - actual)
            origin = pd.Timestamp(sample.asof_date)
            errors.append(dict(model=name, stage=stage, respondent_id=sample.respondent_id,
                               asof_date=sample.asof_date, forecast_start=str((origin + pd.Timedelta(days=1)).date()),
                               forecast_end=str((origin + pd.Timedelta(days=7)).date()), actual=actual,
                               prediction=prediction, signed_error=signed, residual=-signed, absolute_error=abs(signed),
                               naive_prediction=naive_prediction, naive_absolute_error=naive_absolute_error,
                               absolute_error_minus_naive=abs(signed)-naive_absolute_error,
                               direction='over' if signed > ERROR_TOLERANCE else 'under' if signed < -ERROR_TOLERANCE else 'equal'))
    errors = pd.DataFrame(errors)
    per_id = []
    for (name, stage, rid), group in errors.groupby(['model', 'stage', 'respondent_id'], sort=True):
        per_id.append(dict(model=name, stage=stage, respondent_id=rid,
                           **error_statistics(group.actual, group.prediction),
                           limitation='Satu origin per ID; tidak menilai performa stabil individu.' if len(group) == 1
                           else 'Observasi berulang; ukuran sampel kecil.'))
    return result, pd.DataFrame(comparisons), errors, pd.DataFrame(per_id)
