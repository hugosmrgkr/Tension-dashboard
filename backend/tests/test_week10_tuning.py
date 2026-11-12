"""Selection integrity, grouped preprocessing, artifact integrity and serving guards."""
import json

import numpy as np
import pytest

from app.baseline import TARGET, make_training, partitions, sha256, text_sha256
from app.model_comparison import HYPERPARAMETERS, metrics
from app.model_tuning import candidates, grouped_search, load_tuning, run_tuning


@pytest.fixture(scope='module')
def search():
    from pathlib import Path
    import pandas as pd
    from app.pipeline import prepare
    root = Path(__file__).resolve().parents[2]
    frames = [pd.read_csv(root / 'data/sample' / name, dtype=str, keep_default_na=False)
              for name in ['Data_Responden_Sintetis.csv', 'Data_Harian_Sintetis.csv']]
    parts = partitions(make_training(*prepare(*frames)[:3]))
    return parts, grouped_search(parts['train'])


def test_bounded_grid_contains_original_configurations():
    settings = candidates()
    assert [len(settings[name]) for name in settings] == [1, 8, 8]
    for name in settings:
        assert HYPERPARAMETERS[name] in settings[name]


def test_validation_ids_never_share_fit_or_outer_test(search):
    parts, result = search
    seen = []
    for fold in result['folds']:
        assert not set(fold['fit_ids']) & set(fold['validation_ids'])
        assert not set(fold['validation_ids']) & set(parts['test'].respondent_id)
        seen.extend(fold['validation_ids'])
    assert sorted(seen) == sorted(parts['train'].respondent_id.unique())
    # Temporal limitation is exposed, not misrepresented as strict forecasting CV.
    assert not any(fold['chronological'] for fold in result['folds'])


def test_trial_metrics_recompute_from_real_out_of_fold_predictions(search):
    parts, result = search
    for trial in result['trials']:
        predicted = result['predictions'][trial['key']]
        assert len(predicted) == len(parts['train']) and np.isfinite(predicted).all()
        recomputed = metrics(parts['train'].target, predicted)
        assert trial['validation'] == recomputed
        assert sum(fold['n'] for fold in trial['folds']) == len(parts['train'])


def test_choice_uses_only_validation_and_never_worse_than_included_original(search):
    _, result = search
    rank = lambda row: (row['validation']['rmse'], row['validation']['mae'], row['key'])
    assert result['selected']['key'] == min(result['trials'], key=rank)['key']
    for name, best in result['best'].items():
        original = next(row for row in result['trials'] if row['model'] == name and row['original'])
        assert best['validation']['rmse'] <= original['validation']['rmse']
    assert all('test' not in row for row in result['trials'])


def test_search_refuses_too_few_subjects(search):
    parts, _ = search
    train = parts['train']
    with pytest.raises(ValueError, match='4 ID'):
        grouped_search(train[train.respondent_id.isin(train.respondent_id.unique()[:3])])


def test_output_path_guard_protects_active_models(tmp_path):
    with pytest.raises(ValueError, match='artefak aktif'):
        run_tuning('never_read.csv', 'never_read.csv', tmp_path, tmp_path)
    assert not list(tmp_path.iterdir())


def test_manifest_checks_crlf_and_rejects_metrics_or_binary_tampering(tmp_path):
    data = dict(schema_version=1, target=TARGET, run_id='integrity-test')
    metrics_file = tmp_path / 'tuning_metrics.json'
    metrics_file.write_bytes((json.dumps(data, indent=2)+'\n').encode())
    model_file = tmp_path / 'selected_model.joblib'
    model_file.write_bytes(b'integrity-fixture-not-loaded-as-model')
    manifest = dict(run_id=data['run_id'], metrics_hash_mode='utf8-lf-v1', metrics_sha256=text_sha256(metrics_file),
                    model_file=model_file.name, model_sha256=sha256(model_file))
    (tmp_path / 'tuning_manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
    assert load_tuning(tmp_path) == data
    metrics_file.write_bytes(metrics_file.read_bytes().replace(b'\n', b'\r\n'))
    assert load_tuning(tmp_path) == data
    original = metrics_file.read_bytes()
    metrics_file.write_bytes(original.replace(b'integrity-test', b'tampered'))
    with pytest.raises(ValueError, match='Hash metrik'):
        load_tuning(tmp_path)
    metrics_file.write_bytes(original)
    model_file.write_bytes(b'tampered')
    with pytest.raises(ValueError, match='Hash model'):
        load_tuning(tmp_path)
