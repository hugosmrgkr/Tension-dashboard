"""Explicit CLI-only promotion. The web application never calls this module."""
from sqlalchemy import text
from .pipeline import load_warehouse, DataQualityError
from .warehouse_audit import audit_warehouse


def apply_validated(db,profiles,days,sessions,quality,*,kind,expected_current_hash=None,allow_source_change=False):
    if kind not in ('synthetic','actual'):
        raise DataQualityError('Jenis sumber harus synthetic atau actual')
    if kind=='actual' and (quality.get('rejected_profiles',0) or quality.get('rejected_daily',0) or
                          quality.get('issues') or quality.get('pressure_anomalies',{}).get('flagged_sessions',0)):
        raise DataQualityError('Quality gate aktual: pending review; selesaikan keputusan dan koreksi sumber berversi sebelum commit. Tidak ada override diam-diam.')
    if db.bind.dialect.name=='postgresql':
        db.execute(text('SELECT pg_advisory_xact_lock(73421031)'))
    current=audit_warehouse(db)
    occupied=any(current['counts'][name] for name in
                 ('dim_participant_v2','fact_daily_behavior_v2','fact_bp_session_v2'))
    if occupied and not expected_current_hash:
        raise DataQualityError('Warehouse berisi data. Persetujuan manual diperlukan: periksa verify_warehouse lalu berikan --expected-current-hash.')
    if expected_current_hash and expected_current_hash!=current['natural_content_sha256']:
        raise DataQualityError('Isi warehouse berbeda dari hash yang disetujui. Validasi ulang target sebelum menerapkan ETL.')
    if occupied and current['source_kind']!=kind and not allow_source_change:
        raise DataQualityError('Pergantian jenis sumber memerlukan --allow-source-change secara eksplisit; sintetis dan aktual tidak digabungkan.')
    quality={**quality,'source_kind':kind}
    load_warehouse(db,profiles,days,sessions,quality,
                   source_name='Dua formulir sintetis CP2' if kind=='synthetic' else 'Dua formulir aktual - akses terbatas',kind=kind)
    return audit_warehouse(db)
