"""Metric signs, data alignment/tampering and real-artifact evaluation without fit."""
from pathlib import Path
import shutil

import numpy as np
import pandas as pd
import pytest
from sklearn.pipeline import Pipeline

from app.model_evaluation import error_statistics, evaluate_saved_run, validate_prediction_frame

ROOT = Path(__file__).resolve().parents[2]


def test_signed_bias_counts_and_metrics_are_computed_from_pairs():
    stats = error_statistics([100, 110, 120], [102, 107, 120])
    assert stats['bias'] == pytest.approx(-1 / 3)
    assert stats['mae'] == pytest.approx(5 / 3)
    assert stats['rmse'] == pytest.approx(np.sqrt(13 / 3))
    assert stats['median_absolute_error'] == 2 and stats['max_absolute_error'] == 3
    assert (stats['over_count'], stats['under_count'], stats['equal_count']) == (1, 1, 1)


@pytest.mark.parametrize('actual,predicted', [([], []), ([1], [1, 2]), ([np.nan], [1]), ([1], [np.inf])])
def test_invalid_pairs_are_rejected(actual, predicted):
    with pytest.raises(ValueError):
        error_statistics(actual, predicted)


def test_single_origin_has_no_r2_and_no_population_inference():
    stats = error_statistics([123], [120])
    assert stats['r2'] is None and stats['n'] == 1
    assert stats['mae'] == stats['rmse'] == 3


@pytest.fixture
def frames():
    source = pd.DataFrame({'respondent_id': ['SIM001', 'SIM002'], 'asof_date': ['2026-09-18'] * 2,
                           'target': [120., 125.]})
    predictions = source.rename(columns={'target': 'actual'}).assign(model=[119., 123.])
    return source, predictions


def test_alignment_uses_identity_not_csv_order(frames):
    source, predictions = frames
    aligned = validate_prediction_frame(predictions.iloc[::-1], source, 'actual', ['model'])
    assert aligned.respondent_id.tolist() == source.respondent_id.tolist()
    assert aligned.model.tolist() == [119., 123.]


@pytest.mark.parametrize('kind', ['duplicate', 'missing', 'unknown', 'target', 'nonfinite'])
def test_modified_or_invalid_prediction_rows_are_rejected(frames, kind):
    source, predictions = frames
    if kind == 'duplicate':
        predictions = pd.concat([predictions, predictions.iloc[[0]]])
    elif kind == 'missing':
        predictions = predictions.iloc[:1]
    elif kind == 'unknown':
        predictions.loc[0, 'respondent_id'] = 'SIM999'
    elif kind == 'target':
        predictions.loc[0, 'actual'] += 1
    else:
        predictions.loc[0, 'model'] = np.nan
    with pytest.raises(ValueError):
        validate_prediction_frame(predictions, source, 'actual', ['model'])


def real_evaluation(report):
    return evaluate_saved_run(ROOT / 'models/tuning_week10', report,
        ROOT / 'data/sample/Data_Responden_Sintetis.csv', ROOT / 'data/sample/Data_Harian_Sintetis.csv')


def test_real_artifact_evaluation_does_not_train_and_signs_are_consistent(monkeypatch):
    monkeypatch.setattr(Pipeline, 'fit', lambda *args, **kwargs: pytest.fail('Evaluation must not fit a model'))
    result, summary, errors, per_id = real_evaluation(ROOT / 'reports/week10_tuning')
    assert len(errors) == 49 and set(errors.respondent_id) == set(result['test_ids'])
    np.testing.assert_allclose(errors.signed_error, errors.prediction - errors.actual)
    np.testing.assert_allclose(errors.residual, -errors.signed_error)
    np.testing.assert_allclose(errors.absolute_error_minus_naive,
                               errors.absolute_error - errors.naive_absolute_error)
    assert set(per_id.n) == {1} and per_id.r2.isna().all()
    assert set(errors.forecast_start) == {'2026-09-19'}
    assert set(errors.forecast_end) == {'2026-09-25'}
    assert (summary.under_count + summary.over_count + summary.equal_count == summary.n).all()


def test_tampered_prediction_values_fail_verified_metric_comparison(tmp_path):
    for name in ['historical_test_predictions.csv', 'validation_predictions.csv']:
        shutil.copyfile(ROOT / 'reports/week10_tuning' / name, tmp_path / name)
    path = tmp_path / 'historical_test_predictions.csv'
    frame = pd.read_csv(path)
    frame.loc[0, 'Naive 7-day mean'] += 5
    frame.to_csv(path, index=False)
    with pytest.raises(ValueError, match='Metrik CSV'):
        real_evaluation(tmp_path)


def test_evaluated_card_refresh_is_idempotent_and_refuses_stale_inputs(tmp_path, monkeypatch):
    import json
    from etl import evaluate_week10_models as cli
    from app.baseline import text_sha256
    monkeypatch.setattr(cli, 'ROOT', tmp_path)
    model = tmp_path / 'models/tuning_week10'
    report = tmp_path / 'reports/week10_evaluation'
    model.mkdir(parents=True)
    report.mkdir(parents=True)
    (model / 'tuning_metrics.json').write_text(json.dumps({'run_id': 'test-card'}))
    source = tmp_path / 'predictions.csv'
    source.write_text('fixture')
    analysis = {'run_id': 'test-card', 'selected_model': 'Linear Regression',
                'selected_vs_naive': {'better': 3, 'worse': 4, 'equal': 0},
                'input_hashes': {'predictions.csv': text_sha256(source)},
                'summary': [{'model': 'Linear Regression', 'stage': 'selected_configuration',
                             'split': 'historical_test', 'mae': 2., 'rmse': 3., 'r2': .5,
                             'bias': -1., 'under_count': 4, 'over_count': 3, 'equal_count': 0,
                             'max_absolute_error': 5.}]}
    (report / 'evaluation.json').write_text(json.dumps(analysis))
    card = model / 'MODEL_CARD.md'
    card.write_text('Base card\n')
    cli.refresh_card()
    first = card.read_text()
    cli.refresh_card()
    assert card.read_text() == first and first.count(cli.CARD_MARKER) == 1
    source.write_text('changed')
    card.write_text('Base card\n')
    cli.refresh_card()
    assert card.read_text() == 'Base card\n'
