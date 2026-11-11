"""P2-01: perbandingan tiga algoritma pada DATA SINTETIS. Memastikan tidak ada leakage dan hasil reprodusibel."""
import copy
import json
import shutil
from pathlib import Path
import numpy as np
import pytest
from app.baseline import FEATURES, make_training, partitions
from app.model_comparison import (LEARNED, NAIVE, build_model, load_comparison, run_comparison, select_model, validate)

ROOT = Path(__file__).resolve().parents[2]
PROFILE = ROOT / 'data/sample/Data_Responden_Sintetis.csv'
DAILY = ROOT / 'data/sample/Data_Harian_Sintetis.csv'


@pytest.fixture(scope='module')
def run(tmp_path_factory):
    out = tmp_path_factory.mktemp('p2')
    return run_comparison(PROFILE, DAILY, out / 'models', out / 'report'), out


def test_three_learned_algorithms_plus_naive_are_compared(run):
    result, _ = run
    assert [c['model'] for c in result['comparison']] == [NAIVE, 'Linear Regression', 'Random Forest', 'Hist Gradient Boosting']
    assert len(LEARNED) == 3
    for c in result['comparison']:
        assert c['validation']['rmse'] > 0 and c['test']['rmse'] > 0 and c['validation']['n'] == result['rows_training']


def test_synthetic_label_and_target_not_approved(run):
    result, _ = run
    assert result['target_approved'] is False and result['is_synthetic'] and not result['is_diagnosis']
    assert 'SINTETIS' in result['status'] and result['real_model_validated'] is False


def test_validation_is_leave_id_out_and_inside_train(prepared):
    parts = partitions(make_training(*prepared[:3]))
    val = validate(parts['train'])
    assert len(val['folds']) >= 3
    seen = set()
    for fold in val['folds']:
        ids = set(fold['validation_ids'])
        assert not ids & seen  # setiap ID divalidasi tepat satu fold
        seen |= ids
    assert seen == set(parts['train'].respondent_id)
    assert not set(parts['train'].respondent_id) & set(parts['test'].respondent_id)
    assert not np.isnan(val['predictions']['Random Forest']).any()


def test_selection_uses_validation_only_and_rule_is_deterministic():
    scores = {NAIVE: dict(rmse=1.0, mae=1.0), 'Linear Regression': dict(rmse=3.0, mae=2.0),
              'Random Forest': dict(rmse=2.0, mae=2.5), 'Hist Gradient Boosting': dict(rmse=2.0, mae=2.0)}
    selection = select_model(scores)
    assert selection['selected'] == 'Hist Gradient Boosting'  # tie RMSE -> MAE
    assert selection['beats_naive_on_validation'] is False


def test_measurements_after_cutoff_cannot_change_validation_or_selection(prepared):
    p, d, s, _ = copy.deepcopy(prepared)
    base = partitions(make_training(p, d, s))
    original = validate(base['train'])
    for row in s:
        if str(row['date']) > base['cutoff']:
            for key in ('sbp_mean', 'sbp1', 'sbp2'):
                row[key] += 100
            for key in ('dbp_mean', 'dbp1', 'dbp2'):
                row[key] += 50
    changed_parts = partitions(make_training(p, d, s))
    changed = validate(changed_parts['train'])
    for name in original['scores']:
        assert changed['scores'][name]['rmse'] == pytest.approx(original['scores'][name]['rmse'])
    assert select_model(changed['scores'])['selected'] == select_model(original['scores'])['selected']


def test_preprocessing_is_fit_on_train_only(run, prepared):
    parts = partitions(make_training(*prepared[:3]))
    model = build_model('Random Forest').fit(parts['train'][FEATURES], parts['train'].target)
    np.testing.assert_allclose(model.named_steps['impute'].statistics_, parts['train'][FEATURES].median().fillna(0).to_numpy())
    result, _ = run
    assert result['leakage_audit']['imputer_matches_training_only'] and result['leakage_audit']['scaler_matches_training_only']
    assert not result['leakage_audit']['subject_overlap'] and result['leakage_audit']['shared_measurement_id_dates'] == 0


def test_run_is_reproducible_and_artifacts_verify(run, tmp_path):
    first, out = run
    second = run_comparison(PROFILE, DAILY, tmp_path / 'm', tmp_path / 'r')
    assert first['run_id'] == second['run_id']
    assert [c['validation'] for c in first['comparison']] == [c['validation'] for c in second['comparison']]
    assert [c['test'] for c in first['comparison']] == [c['test'] for c in second['comparison']]
    loaded = load_comparison(out / 'models')
    assert loaded['available'] and loaded['artifact_integrity_verified'] and loaded['target_approved'] is False
    assert (out / 'models/MODEL_CARD.md').read_text(encoding='utf-8').count('DATA SINTETIS') >= 1


def test_tampered_artifact_is_rejected(run, tmp_path):
    _, out = run
    copy_dir = tmp_path / 'copy'
    shutil.copytree(out / 'models', copy_dir)
    metrics = copy_dir / 'comparison_metrics.json'
    data = json.loads(metrics.read_text(encoding='utf-8'))
    data['comparison'][1]['test']['rmse'] = 0.001
    metrics.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    assert load_comparison(copy_dir)['available'] is False
    assert load_comparison(tmp_path / 'tidak-ada')['available'] is False


def test_real_ids_are_refused(tmp_path):
    import pandas as pd
    profile = pd.read_csv(PROFILE, dtype=str, keep_default_na=False, encoding='utf-8-sig')
    daily = pd.read_csv(DAILY, dtype=str, keep_default_na=False, encoding='utf-8-sig')
    column = '1. ID Responden'
    mapping = {value: 'REAL' + value[3:] for value in profile[column].unique()}
    profile[column] = profile[column].map(mapping)
    daily[column] = daily[column].map(mapping)
    profile.to_csv(tmp_path / 'p.csv', index=False)
    daily.to_csv(tmp_path / 'd.csv', index=False)
    with pytest.raises(ValueError):
        run_comparison(tmp_path / 'p.csv', tmp_path / 'd.csv', tmp_path / 'm')
