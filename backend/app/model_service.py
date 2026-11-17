"""P2-02: layanan prediksi memakai artefak model terlatih hasil P2-01.

DATA SINTETIS / SIMULASI. Target belum disetujui dosen; keluaran bukan diagnosis.
Fitur inferensi dihitung dengan rumus yang sama dengan `baseline.make_training` (diuji paritasnya)
dan hanya memakai riwayat t-6..t. Tidak ada data masa depan dan tidak ada data buatan.
"""
import numpy as np
import pandas as pd
from .baseline import FEATURES, TARGET, daily_bp
from . import model_registry

HISTORY_DAYS = 7
HORIZON_DAYS = 7


class ModelUnavailable(Exception):
    """Artefak tidak ada, rusak, tidak cocok kontraknya, atau data aktif bukan sintetis (HTTP 409)."""
    def __init__(self, message, error_code='MODEL_UNAVAILABLE'):
        super().__init__(message)
        self.error_code = error_code


class InsufficientHistory(ValueError):
    """Riwayat responden tidak memenuhi syarat 7 hari kalender berturut-turut (HTTP 422)."""


class UnknownRespondent(LookupError):
    """ID responden tidak ditemukan atau tidak memiliki SBP valid (HTTP 404)."""


class ModelFailure(Exception):
    """Model gagal menghasilkan angka yang valid (HTTP 503)."""


def load_serving_model(folder, *, source_kind='synthetic', data_version=None):
    """Compatibility entry point; all validation is delegated to the P2 adapter."""
    try:
        return model_registry.load_model(folder, source_kind=source_kind, data_version=data_version)
    except model_registry.RegistryError as exc:
        raise ModelUnavailable(str(exc), exc.code) from exc


def load_serving_metadata(folder, *, source_kind='synthetic', data_version=None):
    try:
        return model_registry.load_metadata(folder, source_kind=source_kind, data_version=data_version)
    except model_registry.RegistryError as exc:
        raise ModelUnavailable(str(exc), exc.code) from exc


def inference_features(profiles, days, sessions, respondent_id, asof=None):
    """Hitung vektor fitur satu origin (akhir hari t) dari riwayat t-6..t.

    profiles/days/sessions adalah frame dari `analytics_v2.frames` (profil, harian, sesi BP).
    """
    daily = daily_bp(sessions)
    daily = daily[(daily.respondent_id == respondent_id) & daily.sbp.notna()].sort_values('date')
    if daily.empty:
        raise UnknownRespondent('ID responden tidak tersedia atau tidak punya SBP valid.')
    if asof is not None:
        origin = pd.Timestamp(asof).normalize()
        if origin not in set(daily.date):
            raise InsufficientHistory('Tanggal prediksi tidak memiliki SBP yang tersedia.')
    else:
        origin = daily.date.iloc[-1]
    dates = pd.date_range(origin - pd.Timedelta(days=HISTORY_DAYS - 1), origin)
    window = daily[daily.date.isin(dates)]
    if len(window) != HISTORY_DAYS:
        raise InsufficientHistory(f'Dibutuhkan {HISTORY_DAYS} hari kalender berturut-turut dengan SBP valid; tersedia {len(window)}.')
    behavior = pd.DataFrame(days).copy()
    behavior = behavior[behavior.respondent_id == respondent_id]
    behavior['date'] = pd.to_datetime(behavior.date).dt.normalize()
    window = window.merge(behavior, on=['respondent_id', 'date'], how='left')
    profile = pd.DataFrame(profiles)
    profile = profile[profile.respondent_id == respondent_id]
    if profile.empty:
        raise UnknownRespondent('Profil responden tidak tersedia.')
    profile = profile.iloc[0]
    features = dict(past_7d_sbp=float(window.sbp.mean()), past_7d_dbp=float(window.dbp.mean()), past_7d_sbp_std=float(window.sbp.std(ddof=0)),
                    age=profile['age'], bmi=profile['bmi'], past_7d_activity=float(window.activity_minutes.mean()),
                    past_7d_sleep=float(window.sleep_hours.mean()), past_7d_stress=float(window.stress.mean()))
    features = {name: (None if pd.isna(features[name]) else float(features[name])) for name in FEATURES}
    history = [dict(date=str(day.date.date()), sbp=float(day.sbp),
                    dbp=None if pd.isna(day.dbp) else float(day.dbp)) for day in window.itertuples()]
    return dict(features=features, history_daily=history, origin=origin, history_start=dates[0], forecast_start=origin + pd.Timedelta(days=1),
                forecast_end=origin + pd.Timedelta(days=HORIZON_DAYS))


def predict(model, info, profiles, days, sessions, respondent_id, asof=None):
    built = inference_features(profiles, days, sessions, respondent_id, asof)
    row = pd.DataFrame([built['features']], columns=FEATURES, dtype=float)
    try:
        value = float(model.predict(row)[0])
    except Exception as exc:
        raise ModelFailure('Model gagal menghitung prediksi.') from exc
    if not np.isfinite(value):
        raise ModelFailure('Model menghasilkan nilai tidak valid.')
    ranges = info.get('feature_ranges') or {}
    outside = [name for name, v in built['features'].items()
               if v is not None and name in ranges and not (ranges[name]['min'] <= v <= ranges[name]['max'])]
    imputed = [name for name, v in built['features'].items() if v is None]
    notes = []
    if outside:
        notes.append('Sebagian fitur berada di luar rentang data training: ' + ', '.join(outside) + '. Prediksi merupakan ekstrapolasi.')
    if imputed:
        notes.append('Fitur kosong diisi median training: ' + ', '.join(imputed) + '.')
    if not info['selection']['beats_naive_on_validation']:
        notes.append('Pada validasi, model ini tidak lebih baik dari baseline naif; gunakan angka naif sebagai pembanding.')
    if info.get('compatibility_status') == 'batch_unverified':
        notes.append('Fingerprint batch warehouse belum tersedia; kecocokan batch training belum terverifikasi.')
    return dict(
        respondent_id=respondent_id, last_date=str(built['origin'].date()), history_start=str(built['history_start'].date()),
        forecast_start=str(built['forecast_start'].date()), forecast_end=str(built['forecast_end'].date()),
        history_daily=built['history_daily'], history_grain='respondent-date',
        prediction_mmHg=round(value, 2), reference_naive_mmHg=round(built['features']['past_7d_sbp'], 2),
        features_used=built['features'], features_imputed=imputed, features_out_of_range=outside, notes=notes,
        model=dict(algorithm=info['selected_model'], version=info['run_id'], trained_on=info['as_of'], target=info['target'],
                   horizon_days=info['horizon_days'], features=info['features'], data_source=info['dataset'],
                   target_approved=info['target_approved'], model_sha256=info['model_sha256'],
                   beats_naive_on_validation=info['selection']['beats_naive_on_validation']),
        is_synthetic=True, is_diagnosis=False, target_approved=False,
        source_kind=info.get('source_kind', 'synthetic'),
        data_version=info.get('data_version'), training_data_version=info.get('training_data_version'),
        feature_schema_version=info.get('feature_schema_version'),
        warehouse_batch_match=info.get('warehouse_batch_match'),
        compatibility_status=info.get('compatibility_status'), metrics_scope=info.get('metrics_scope'),
        status='DATA SINTETIS / SIMULASI - BUKAN DIAGNOSIS')
