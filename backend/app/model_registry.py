"""Stage 2: explicit adapter for trusted P2 synthetic artifacts, not a release scanner.

Only the configured folder is read. No training, artifact promotion or actual-data
activation. A future release format requires a separately reviewed adapter.
"""
import hashlib
from io import BytesIO
import json
import math
from pathlib import Path
import re

import joblib

from .baseline import FEATURES, TARGET

FEATURE_SCHEMA_VERSION = 'cp3-history7-v1'
HEX64 = re.compile(r'^[0-9a-f]{64}$')
MODEL_NAME = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.-]*\.joblib$')


class RegistryError(ValueError):
    def __init__(self, message, code='MODEL_UNAVAILABLE'):
        super().__init__(message)
        self.code = code


def _file(folder, name):
    if not isinstance(name, str) or '/' in name or '\\' in name or ':' in name or name in ('.', '..'):
        raise RegistryError('Lokasi file artefak tidak valid.', 'MODEL_INCOMPATIBLE')
    path = folder / name
    if path.resolve().parent != folder:
        raise RegistryError('File artefak berada di luar folder yang diizinkan.', 'MODEL_INCOMPATIBLE')
    return path


def _json(raw):
    value = json.loads(raw.decode('utf-8'))
    if not isinstance(value, dict):
        raise RegistryError('Struktur metadata model tidak valid.', 'MODEL_INCOMPATIBLE')
    return value


def _digest(raw):
    return hashlib.sha256(raw).hexdigest()


def _hash_value(value):
    return isinstance(value, str) and HEX64.fullmatch(value) is not None


def _number(value):
    return type(value) in (int, float) and math.isfinite(value)


def _validate_details(info):
    ranges = info.get('feature_ranges', {})
    if not isinstance(ranges, dict):
        raise RegistryError('Rentang fitur model tidak valid.', 'MODEL_INCOMPATIBLE')
    for name, limits in ranges.items():
        if (name not in FEATURES or not isinstance(limits, dict) or
                not _number(limits.get('min')) or not _number(limits.get('max')) or limits['min'] > limits['max']):
            raise RegistryError('Rentang fitur model tidak valid.', 'MODEL_INCOMPATIBLE')
    models = []
    for row in info['comparison']:
        if not isinstance(row, dict) or not isinstance(row.get('model'), str):
            raise RegistryError('Tabel metrik model tidak valid.', 'MODEL_INCOMPATIBLE')
        models.append(row['model'])
        for split in ('validation', 'test'):
            score = row.get(split)
            if (not isinstance(score, dict) or type(score.get('n')) is not int or score['n'] < 1 or
                    any(not _number(score.get(metric)) or score[metric] < 0 for metric in ('mae', 'rmse')) or
                    (score.get('r2') is not None and not _number(score['r2']))):
                raise RegistryError('Nilai metrik model tidak valid.', 'MODEL_INCOMPATIBLE')
    if info['selected_model'] not in models:
        raise RegistryError('Model terpilih tidak ada dalam evaluasi.', 'MODEL_INCOMPATIBLE')


def _verified_bundle(folder, *, source_kind, data_version):
    if source_kind != 'synthetic':
        raise RegistryError('Loader Tahap 2 hanya tersedia untuk DATA SINTETIS / SIMULASI.', 'SOURCE_RESTRICTED')
    if data_version is not None and not _hash_value(data_version):
        raise RegistryError('Fingerprint batch warehouse tidak valid.', 'DATASET_METADATA_INVALID')
    folder = Path(folder).resolve()
    try:
        manifest = _json(_file(folder, 'comparison_manifest.json').read_bytes())
        if type(manifest.get('schema_version')) is not int or manifest['schema_version'] != 1:
            raise RegistryError('Versi manifest P2 tidak didukung.', 'MODEL_INCOMPATIBLE')
        if manifest.get('metrics_hash_mode') != 'utf8-lf-v1':
            raise RegistryError('Mode hash metrik tidak didukung.', 'MODEL_INCOMPATIBLE')
        name = manifest.get('model_file')
        if not isinstance(name, str) or not MODEL_NAME.fullmatch(name):
            raise RegistryError('Nama file model tidak valid.', 'MODEL_INCOMPATIBLE')
        metrics_raw = _file(folder, 'comparison_metrics.json').read_bytes()
        # Validate UTF-8 and normalize physical CRLF only; same policy as CP3/P2.
        metrics_raw.decode('utf-8')
        if not _hash_value(manifest.get('metrics_sha256')) or _digest(metrics_raw.replace(b'\r\n', b'\n')) != manifest['metrics_sha256']:
            raise RegistryError('Hash metrik model tidak cocok.')
        info = _json(metrics_raw)
        model_raw = _file(folder, name).read_bytes()
        if not _hash_value(manifest.get('model_sha256')) or _digest(model_raw) != manifest['model_sha256']:
            raise RegistryError('Hash model tidak cocok.')
        if (type(info.get('schema_version')) is not int or info['schema_version'] != 1 or
                not isinstance(info.get('run_id'), str) or not info['run_id'] or
                info['run_id'] != manifest.get('run_id') or info.get('model_file') != name or
                info.get('model_sha256') != manifest['model_sha256']):
            raise RegistryError('Manifest dan metadata model tidak konsisten.', 'MODEL_INCOMPATIBLE')
        if (info.get('target') != TARGET or info.get('features') != FEATURES or
                type(info.get('horizon_days')) is not int or info['horizon_days'] != 7 or
                type(info.get('history_days', 7)) is not int or info.get('history_days', 7) != 7 or
                info.get('feature_schema_version', FEATURE_SCHEMA_VERSION) != FEATURE_SCHEMA_VERSION):
            raise RegistryError('Kontrak fitur, target atau horizon tidak cocok.', 'MODEL_INCOMPATIBLE')
        if (info.get('is_synthetic') is not True or info.get('is_diagnosis') is not False or
                info.get('real_model_validated') is not False or
                info.get('source_kind', 'synthetic') != 'synthetic' or
                info.get('target_approved') is not False or manifest.get('target_approved') is not False):
            raise RegistryError('Kontrak sumber/status artefak P2 sintetis tidak cocok.', 'MODEL_INCOMPATIBLE')
        provenance, selection = info.get('provenance'), info.get('selection')
        if not isinstance(provenance, dict) or not _hash_value(provenance.get('prepared_content_sha256')):
            raise RegistryError('Provenance batch training tidak valid.', 'MODEL_INCOMPATIBLE')
        if (not isinstance(selection, dict) or type(selection.get('beats_naive_on_validation')) is not bool or
                not isinstance(info.get('selected_model'), str) or not info['selected_model'] or
                selection.get('selected') != info['selected_model'] or
                any(not isinstance(info.get(key), str) for key in ('as_of', 'dataset')) or
                not isinstance(info.get('comparison'), list) or not info['comparison']):
            raise RegistryError('Metadata pemilihan/hasil model tidak lengkap.', 'MODEL_INCOMPATIBLE')
        _validate_details(info)
        training_version = provenance['prepared_content_sha256']
        if data_version is not None and data_version != training_version:
            raise RegistryError('Batch warehouse berbeda dari batch training. Review kompatibilitas diperlukan; model tidak diganti otomatis.', 'DATASET_MISMATCH')
        return {**info, 'available': True, 'artifact_integrity_verified': True,
                'artifact_format': 'p2-comparison-v1', 'source_kind': 'synthetic',
                'feature_schema_version': FEATURE_SCHEMA_VERSION, 'history_days': 7,
                'training_data_version': training_version, 'data_version': data_version,
                'warehouse_batch_match': True if data_version is not None else None,
                'compatibility_status': 'matched' if data_version is not None else 'batch_unverified',
                'metrics_scope': 'synthetic_historical_test'}, model_raw
    except RegistryError:
        raise
    except (OSError, ValueError, TypeError, KeyError, RuntimeError) as exc:
        raise RegistryError('Artefak model belum tersedia atau metadata tidak valid.') from exc


def load_metadata(folder, *, source_kind='synthetic', data_version=None):
    """Verify metadata and binary hash without unpickling executable model data."""
    return _verified_bundle(folder, source_kind=source_kind, data_version=data_version)[0]


def load_model(folder, *, source_kind='synthetic', data_version=None):
    info, raw = _verified_bundle(folder, source_kind=source_kind, data_version=data_version)
    try:
        # Deserialize exactly the bytes whose hash was checked, not a second file read.
        model = joblib.load(BytesIO(raw))
        if (list(getattr(model, 'feature_names_in_', [])) != FEATURES or
                getattr(model, 'n_features_in_', None) != len(FEATURES) or not callable(getattr(model, 'predict', None))):
            raise RegistryError('Nama/jumlah fitur model tidak cocok.', 'MODEL_INCOMPATIBLE')
        return model, info
    except RegistryError:
        raise
    except Exception as exc:
        raise RegistryError('Artefak model tidak dapat dimuat.') from exc
