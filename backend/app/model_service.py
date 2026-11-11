"""P2-02: layanan prediksi memakai artefak model terlatih hasil P2-01.

DATA SINTETIS / SIMULASI. Target belum disetujui dosen; keluaran bukan diagnosis.
Fitur inferensi dihitung dengan rumus yang sama dengan `baseline.make_training` (diuji paritasnya)
dan hanya memakai riwayat t-6..t. Tidak ada data masa depan dan tidak ada data buatan.
"""
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from .baseline import FEATURES, TARGET, daily_bp
from .model_comparison import NAIVE, load_comparison

HISTORY_DAYS = 7
HORIZON_DAYS = 7


class ModelUnavailable(Exception):
    """Artefak tidak ada, rusak, tidak cocok kontraknya, atau data aktif bukan sintetis (HTTP 409)."""


class InsufficientHistory(ValueError):
    """Riwayat responden tidak memenuhi syarat 7 hari kalender berturut-turut (HTTP 422)."""


class UnknownRespondent(LookupError):
    """ID responden tidak ditemukan atau tidak memiliki SBP valid (HTTP 404)."""


class ModelFailure(Exception):
    """Model gagal menghasilkan angka yang valid (HTTP 503)."""


def load_serving_model(folder):
    """Muat model terpilih dengan verifikasi hash dan kontrak fitur. Gagal tertutup."""
    info = load_comparison(folder)
    if not info['available']:
        raise ModelUnavailable(info['message'])
    if info.get('target') != TARGET or info.get('features') != FEATURES:
        raise ModelUnavailable('Kontrak fitur/target artefak tidak cocok dengan kode aktif.')
    path = Path(folder) / info['model_file']
    try:
        model = joblib.load(path)
    except Exception as exc:  # artefak rusak yang lolos hash tidak boleh menjatuhkan server
        raise ModelUnavailable('Artefak model tidak dapat dimuat.') from exc
    names = list(getattr(model, 'feature_names_in_', []))
    if names != FEATURES:
        raise ModelUnavailable('Nama fitur pada model tidak cocok dengan kontrak inferensi.')
    return model, info


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
    return dict(features=features, origin=origin, history_start=dates[0], forecast_start=origin + pd.Timedelta(days=1),
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
    return dict(
        respondent_id=respondent_id, last_date=str(built['origin'].date()), history_start=str(built['history_start'].date()),
        forecast_start=str(built['forecast_start'].date()), forecast_end=str(built['forecast_end'].date()),
        prediction_mmHg=round(value, 2), reference_naive_mmHg=round(built['features']['past_7d_sbp'], 2),
        features_used=built['features'], features_imputed=imputed, features_out_of_range=outside, notes=notes,
        model=dict(algorithm=info['selected_model'], version=info['run_id'], trained_on=info['as_of'], target=info['target'],
                   horizon_days=info['horizon_days'], features=info['features'], data_source=info['dataset'],
                   target_approved=info['target_approved'], model_sha256=info['model_sha256'],
                   beats_naive_on_validation=info['selection']['beats_naive_on_validation']),
        is_synthetic=True, is_diagnosis=False, target_approved=False,
        status='DATA SINTETIS / SIMULASI - BUKAN DIAGNOSIS')
