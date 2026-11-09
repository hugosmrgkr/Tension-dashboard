"""ETL for the two *distinct* survey sources. Never import names into the warehouse."""
import json
import re
from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from .models import Participant, CalendarDate, SessionType, BPSession, DailyBehavior, SourceState

PROFILE_INDEX = {
 'respondent_id':1,'age':3,'gender':4,'province':5,'city':6,'occupation':7,'education':8,
 'height_cm':20,'weight_kg':21,'usual_activity':22,'active_days_week':23
}
DAY_INDEX = {'respondent_id':1,'date':2,'morning_time':3,'morning_sbp1':4,'morning_dbp1':5,'morning_sbp2':6,'morning_dbp2':7,'morning_context':8,
 'evening_time':9,'evening_sbp1':10,'evening_dbp1':11,'evening_sbp2':12,'evening_dbp2':13,'evening_context':14,
 'activity_type':15,'activity_minutes':16,'heavy_minutes':17,'sitting':18,'sleep':19,'salty_food':20,'fruit':21,'vegetable':22,'caffeine':23,'smoked':24,'smoke_count':25,'medication':26,'stress':27}
CONDITIONS = ['diagnosed_bp','bp_medication','diabetes','kidney','cholesterol','heart','stroke','mother_bp','father_bp','family_diabetes','family_heart']

class DataQualityError(ValueError):
    pass

EXPECTED_PROFILE_HEADERS = ['Timestamp', '1. ID Responden', '2. Nama lengkap', '3. Berapa usia anda saat ini (Contoh: 22 tahun)', '4. Apa jenis kelamin anda?', '5. Di provinsi mana Anda tinggal saat ini? (Contoh: Sumatera Utara)', '6. Di kabupaten atau kota mana Anda tinggal saat ini? (Contoh: Toba Samosir)', '7. Apa pekerjaan atau kegiatan utama Anda saat ini?', '9. Apa pendidikan terakhir yang telah Anda selesaikan?', '10. Apakah Anda pernah didiagnosis memiliki tekanan darah tinggi oleh tenaga kesehatan?', '11. Apakah saat ini Anda menggunakan obat yang diresepkan untuk tekanan darah tinggi?', '12. Apakah Anda pernah didiagnosis diabetes oleh tenaga kesehatan?', '13. Apakah Anda pernah didiagnosis penyakit ginjal oleh tenaga kesehatan?', '14. Apakah Anda pernah didiagnosis kolesterol tinggi atau gangguan lemak darah oleh tenaga kesehatan?', '15. Apakah Anda pernah didiagnosis penyakit jantung oleh tenaga kesehatan?', '16. Apakah Anda pernah didiagnosis mengalami stroke oleh tenaga kesehatan?', '17. Apakah ibu kandung Anda pernah didiagnosis memiliki tekanan darah tinggi?', '18. Apakah ayah kandung Anda pernah didiagnosis memiliki tekanan darah tinggi?', '20. Apakah orang tua kandung atau saudara kandung Anda pernah didiagnosis diabetes?', '21. Apakah orang tua kandung atau saudara kandung Anda pernah didiagnosis penyakit jantung atau mengalami stroke?', '22. Berapa tinggi badan Anda? (Masukkan dalam sentimeter (cm), misalnya 165 cm)', '23. Berapa berat badan Anda? (Masukkan dalam kilogram misalnya 45 kg)', '24. Aktivitas fisik atau olahraga apa yang biasanya Anda lakukan? (boleh memilih lebih dari satu)', '25. Dalam satu minggu biasa, berapa hari Anda melakukan aktivitas fisik yang membuat napas atau denyut jantung sedikit lebih cepat?']
EXPECTED_DAILY_HEADERS = ['Timestamp', '1. ID Responden', '2. Tanggal pengamatan', '3. Pukul berapa Anda mengukur tekanan darah pagi ini?', '4. Berapa angka atas (sistolik) pada pembacaan pertama?', '6. Berapa angka bawah (diastolik) pada pembacaan pertama?', '7. Berapa angka atas (sistolik) pada pembacaan kedua?', '8. Berapa angka bawah (diastolik) pada pembacaan kedua?', '9. Dalam 30 menit sebelum pengukuran pagi, apakah Anda melakukan salah satu kegiatan berikut?', '10. Pukul berapa Anda mengukur tekanan darah malam ini?', '11. Berapa angka atas (sistolik) pada pembacaan pertama?', '12. Berapa angka bawah (diastolik) pada pembacaan pertama?', '13. Berapa angka atas (sistolik) pada pembacaan kedua?', '14. Berapa angka bawah (diastolik) pada pembacaan kedua?', '15. Dalam 30 menit sebelum pengukuran malam, apakah Anda melakukan salah satu kegiatan berikut?', '16. Aktivitas fisik atau olahraga apa yang Anda lakukan hari ini?', '17. Berapa total menit yang Anda gunakan untuk aktivitas fisik hari ini? \nContoh: Jalan cepat atau kegiatan yang membuat napas sedikit lebih cepat, tetapi Anda masih bisa berbicara. Hitung total waktu dan jangan menghitung menit yang sama dua kali. Jika tidak ada, isi 0.', '18. Berapa total menit yang Anda gunakan untuk aktivitas fisik berat hari ini?\n(contoh: lari cepat atau aktivitas fisik yang membuat napas jauh lebih cepat dan membuat Anda sulit berbicara panjang. Jika tidak ada, isi 0. Jika tidak tahu, jangan mengira-ngira.)', '19. Kira-kira berapa lama total Anda duduk atau hanya sedikit bergerak hari ini, di luar waktu tidur?', '20. Berapa jam Anda tidur tadi malam?', '21. Hari ini, berapa kali Anda makan makanan asin atau makanan olahan?', '22. Hari ini, berapa porsi buah yang Anda makan?', '23. Hari ini, berapa porsi sayur yang Anda makan?', '24. Hari ini, berapa gelas atau cangkir minuman berkafein yang Anda konsumsi?\nContoh: kopi, teh, atau minuman energi.', '25. Apakah anda merokok hari ini?', 'Berapa kali anda merokok hari ini?', '26. Jika Anda menggunakan obat yang diresepkan untuk tekanan darah, apakah Anda minum obat sesuai petunjuk hari ini?', '27. Seberapa besar stres yang Anda rasakan hari ini?']

def header_key(v):
    return re.sub(r"\s+", " ", str(v).strip().lstrip("\ufeff").strip()).casefold()

def verify_headers(df, expected, name):
    if len(df.columns)!=len(expected):
        raise DataQualityError(f"{name}: perlu {len(expected)} kolom, menemukan {len(df.columns)}")
    for i,(current,want) in enumerate(zip(df.columns,expected)):
        if header_key(current)!=header_key(want):
            raise DataQualityError(f"{name}: header kolom {i+1} berbeda (diharapkan {want[:45]!r}, didapat {str(current)[:45]!r})")


from .survey_schema import PROFILE_FIELDS, DAILY_FIELDS, CONDITION_NAMES, parse_value, parse_numeric, text

def clean_str(v):
    return text(v)


def numeric(v, lo=None, hi=None, unit=None, integer=False):
    return parse_numeric(v, unit, [lo, hi] if lo is not None and hi is not None else None, integer)


def sleep_hours(v, synthetic=True):
    return parse_value(v, DAILY_FIELDS[19], synthetic)[0]


def clean_date(v):
    return parse_value(v, DAILY_FIELDS[2])[0]


def _canonical_rows(df, specs, source, synthetic=True):
    rows, issues, changes = [], [], []
    for number, values in enumerate(df.itertuples(index=False, name=None), start=2):
        row = {}
        for index, spec in enumerate(specs):
            value, code = parse_value(values[index], spec, synthetic)
            row[spec['technical']] = value
            if code:
                issues.append({'source':source, 'row':number, 'column':index+1,
                               'field':spec['technical'], 'code':code,
                               'action':'retain_for_review' if code == 'unmapped_other_category_review' else 'set_null'})
            if value is not None and str(values[index]) != str(value):
                changes.append({'source':source, 'row':number, 'field':spec['technical']})
        rows.append((number, row))
    return rows, issues, changes


def parse_profiles(df, audit=None, synthetic=True):
    verify_headers(df, EXPECTED_PROFILE_HEADERS, 'Form Awal')
    canonical, issues, changes = _canonical_rows(df, PROFILE_FIELDS, 'profiles', synthetic)
    from collections import defaultdict
    grouped=defaultdict(list)
    for number,row in canonical:
        if row['respondent_id']:grouped[row['respondent_id']].append(row)
    conflicts={key for key,rows in grouped.items() if len({json.dumps({k:v for k,v in r.items() if k not in ('submitted_at','direct_identity')},default=str,sort_keys=True) for r in rows})>1}

    output, errors, accepted, seen = [], [], [], set()
    for number, row in canonical:
        rid = row['respondent_id']
        reason = 'ID responden kosong/tidak valid' if not rid else 'Konflik profil: semua versi ID dikarantina' if rid in conflicts else 'ID responden duplikat identik' if rid in seen else None
        if reason:
            errors.append({'row':number, 'reason':reason}); continue
        seen.add(rid)
        profile = {key:row[key] for key in PROFILE_INDEX}
        profile['bmi'] = (round(profile['weight_kg'] / (profile['height_cm']/100)**2, 3)
                          if profile['weight_kg'] and profile['height_cm'] else None)
        profile['conditions_json'] = json.dumps({key:row[key] for key in CONDITION_NAMES}, ensure_ascii=False)
        output.append(profile); accepted.append(row)
    if audit is not None:
        audit.update(profile_clean=accepted, profile_issues=issues, profile_changes=changes)
    return output, errors


def parse_days(df, profile_ids, synthetic=True, audit=None):
    verify_headers(df, EXPECTED_DAILY_HEADERS, 'Form Harian')
    canonical, issues, changes = _canonical_rows(df, DAILY_FIELDS, 'daily', synthetic)
    from collections import defaultdict
    grouped=defaultdict(list)
    for number,row in canonical:
        if row['respondent_id'] and row['date']:grouped[(row['respondent_id'],row['date'])].append(row)
    conflicts={key for key,rows in grouped.items() if len({json.dumps({k:v for k,v in r.items() if k!='submitted_at'},default=str,sort_keys=True) for r in rows})>1}

    days, sessions, errors, accepted, suspicious, consistency = [], [], [], [], [], []
    session_source_rows = []
    keys, duplicate_keys = set(), set()
    for number, row in canonical:
        rid, day = row['respondent_id'], row['date']
        if not rid or not day or rid not in profile_ids:
            errors.append({'row':number, 'reason':'ID kosong/tidak cocok profil diterima atau tanggal tidak valid'}); continue
        key = rid, day
        if key in conflicts:
            duplicate_keys.add(key)
            errors.append({'row':number,'reason':'Konflik ID-tanggal: seluruh versi dikarantina; keputusan koreksi sumber diperlukan'})
            continue
        if key in keys:
            duplicate_keys.add(key)
            errors.append({'row':number, 'reason':'Duplikasi ID-tanggal: baris berikutnya dikarantina; baris pertama dipertahankan'})
            continue
        keys.add(key)
        if day.year < 2024 or day.year > 2030:
            suspicious.append({'row':number,'date':str(day),'reason':'Tanggal di luar rentang audit teknis lama 2024-2030: pending review'})
            errors.append({'row':number,'reason':'Tanggal pending review; raw tidak diubah'});continue
        if row['submitted_at'] and day > datetime.fromisoformat(row['submitted_at']).date():
            consistency.append({'source':'daily','row':number,'field':'date','code':'observation_after_submission','action':'quarantine_pending_review'})
            errors.append({'row':number,'reason':'Tanggal pengamatan sesudah pengiriman: pending review'});continue
        if row['smoked'] in ('Tidak', 'Tidak berlaku karena saya tidak merokok') and (row['smoke_count'] or 0) > 0:
            consistency.append({'source':'daily','row':number,'field':'smoke_count','code':'smoking_status_count_conflict','action':'retain_for_review'})
        if row['smoked'] == 'Ya' and row['smoke_count'] is None:
            consistency.append({'source':'daily','row':number,'field':'smoke_count','code':'smoker_count_missing','action':'retain_for_review'})
        days.append({key:row[key] for key in ['respondent_id','date','activity_type','activity_minutes','heavy_minutes',
            'sitting','sleep_hours','salty_food','fruit','vegetable','caffeine','smoked','smoke_count','medication','stress']})
        accepted.append(row)
        for session, prefix in [('Pagi','morning'), ('Malam','evening')]:
            session_source_rows.append(number)
            sbp1, dbp1, sbp2, dbp2 = [row[f'{prefix}_{x}'] for x in ('sbp1','dbp1','sbp2','dbp2')]
            sbp = [v for v in (sbp1,sbp2) if v is not None]
            dbp = [v for v in (dbp1,dbp2) if v is not None]
            for reading, a, b in [(1,sbp1,dbp1),(2,sbp2,dbp2)]:
                if a is not None and b is not None and a <= b:
                    consistency.append({'source':'daily','row':number,'field':f'{prefix}_reading{reading}',
                                        'code':'sbp_not_above_dbp','action':'retain_for_review'})
            from .bp_policy import assess_session
            invalid=[i['field'] for i in issues if i['row']==number and i['field'].startswith(prefix+'_') and re.search(r'(sbp|dbp)[12]$',i['field'])]
            assessed=assess_session(dict(sbp1=sbp1,dbp1=dbp1,sbp2=sbp2,dbp2=dbp2),invalid)
            if assessed['review_status']=='pending_review':
                consistency.append({'source':'daily','row':number,'field':prefix+'_session','code':'bp_session_pending_review','action':'exclude_derived_pending_decision','reasons':assessed['review_reasons']})
            sessions.append(dict(respondent_id=rid,date=day,session=session,measured_at=row[f'{prefix}_time'],
                sbp1=sbp1,dbp1=dbp1,sbp2=sbp2,dbp2=dbp2,
                sbp_mean=assessed['sbp_mean'], dbp_mean=assessed['dbp_mean'],
                valid_sbp_count=len(sbp),valid_dbp_count=len(dbp),before_activity=row[f'{prefix}_context']))
    invalid_bp = [i for i in issues if re.fullmatch(r'(morning|evening)_(sbp|dbp)[12]',i['field'])]
    quality = dict(raw_daily=len(df), accepted_daily=len(days), rejected_daily=len(errors),
        valid_sessions=sum(s['sbp_mean'] is not None and s['dbp_mean'] is not None for s in sessions),
        missing_sleep=sum(d['sleep_hours'] is None for d in days), missing_sitting=sum(d['sitting'] is None for d in days),
        duplicate_pairs=len(duplicate_keys), rejections=errors, suspicious_dates=suspicious,
        invalid_bp_readings=invalid_bp, invalid_bp_count=len(invalid_bp),
        assumption_sleep='HH:MM sintetis = durasi jam:menit; data aktual tetap NA sampai definisi disetujui.')
    if audit is not None:
        audit.update(daily_clean=accepted, daily_issues=issues, daily_changes=changes,
                     consistency_issues=consistency, session_source_rows=session_source_rows)
    return days, sessions, quality


def prepare(profiles_df, days_df, synthetic=True):
    audit = {}
    profiles, profile_errors = parse_profiles(profiles_df, audit, synthetic)
    days, sessions, quality = parse_days(days_df, {r['respondent_id'] for r in profiles}, synthetic, audit)
    quality.update(raw_profiles=len(profiles_df), rejected_profiles=len(profile_errors),
                   profile_rejections=profile_errors, accepted_profiles=len(profiles),
                   source_kind='synthetic' if synthetic else 'uploaded')
    from .quality import build_quality
    quality.update(build_quality(profiles_df, days_df, profiles, days, sessions, audit, quality, synthetic))
    if not profiles or not days:
        error = DataQualityError('Tidak ada data profil/harian valid yang dapat dimuat')
        error.quality = quality
        raise error
    return profiles, days, sessions, quality


def load_warehouse(db:Session, profiles, days, sessions, quality, source_name='CSV sintetis', kind='synthetic'):
    """Replace only v2 data, atomically. Call only on an explicitly selected database.

    Idempotency means the same natural keys/values/counts after reloading, not stable
    surrogate IDs. Invalid input and DB errors roll the entire replacement back.
    """
    try:
        if not profiles or not days:
            raise DataQualityError('Menolak memuat dataset kosong')
        if kind == 'synthetic' and any(not p['respondent_id'].startswith('SIM') for p in profiles):
            raise DataQualityError('Sumber sintetis wajib memakai ID SIM; jangan labeli data aktual sebagai simulasi')
        for model in (BPSession,DailyBehavior,Participant,CalendarDate,SessionType,SourceState):
            db.execute(delete(model))
        db.flush()
        db.add_all([Participant(**row) for row in profiles])
        db.add_all([CalendarDate(date=d,year=d.year,month=d.month,day=d.day) for d in sorted({r['date'] for r in days})])
        db.add_all([SessionType(name='Pagi'),SessionType(name='Malam')]); db.flush()
        pids={p.respondent_id:p.id for p in db.scalars(select(Participant)).all()}
        dates={d.date:d.id for d in db.scalars(select(CalendarDate)).all()}
        sids={s.name:s.id for s in db.scalars(select(SessionType)).all()}
        for row in days:
            r=dict(row); rid=r.pop('respondent_id'); day=r.pop('date')
            db.add(DailyBehavior(participant_id=pids[rid],date_id=dates[day],**r))
        for row in sessions:
            r=dict(row); rid=r.pop('respondent_id'); day=r.pop('date'); session=r.pop('session')
            db.add(BPSession(participant_id=pids[rid],date_id=dates[day],session_id=sids[session],**r))
        db.add(SourceState(id=1,source_name=source_name,source_kind=kind,row_count=len(days),quality_json=json.dumps(quality,ensure_ascii=False)))
        db.commit()
    except Exception:
        db.rollback()
        raise
    return quality


def seed_if_empty(db:Session, root=None):
    if db.get(SourceState,1): return False
    folder=Path(root or __import__('os').getenv('SAMPLE_DATA_DIR','/app/data/sample'))
    a=folder/'Data_Responden_Sintetis.csv'; b=folder/'Data_Harian_Sintetis.csv'
    if not a.exists() or not b.exists(): raise FileNotFoundError(f'Synthetic fixtures missing in {folder}')
    profiles,days,sessions,quality=prepare(pd.read_csv(a,dtype=str,keep_default_na=False),pd.read_csv(b,dtype=str,keep_default_na=False))
    load_warehouse(db,profiles,days,sessions,quality,'Data sintetis dua formulir (SIM001?SIM019)','synthetic')
    return True
