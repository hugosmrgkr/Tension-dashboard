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
    return re.sub(r"\s+", " ", str(v).strip().lstrip("\ufeff")).casefold()

def verify_headers(df, expected, name):
    if len(df.columns)!=len(expected):
        raise DataQualityError(f"{name}: perlu {len(expected)} kolom, menemukan {len(df.columns)}")
    for i,(current,want) in enumerate(zip(df.columns,expected)):
        if header_key(current)!=header_key(want):
            raise DataQualityError(f"{name}: header kolom {i+1} berbeda (diharapkan {want[:45]!r}, didapat {str(current)[:45]!r})")


def clean_str(v):
    if v is None or pd.isna(v): return None
    s = str(v).strip()
    return s if s and s.lower() not in ('nan','none','nat') else None

def numeric(v, lo=None, hi=None):
    s=clean_str(v)
    if s is None: return None
    s=s.replace(',','.')
    match=re.fullmatch(r'\s*(-?\d+(?:\.\d+)?)\s*(?:cm|kg|menit|tahun)?\s*',s,re.I)
    if not match: return None
    n=float(match.group(1))
    return n if (lo is None or n >= lo) and (hi is None or n <= hi) else None

def sleep_hours(v, synthetic=True):
    s=clean_str(v)
    if not s: return None
    if re.fullmatch(r'\d{1,2}:\d{2}',s):
        if not synthetic: return None  # real survey field meaning requires confirmation
        h,m=map(int,s.split(':'))
        return round(h+m/60,3) if h<=18 and m<60 else None
    return numeric(s,0,18) if synthetic else None

def clean_date(v):
    try:
        dt=pd.to_datetime(v,errors='coerce')
        return dt.date() if pd.notna(dt) else None
    except (ValueError,TypeError): return None

def parse_profiles(df):
    verify_headers(df,EXPECTED_PROFILE_HEADERS,'Form Awal')
    if 'ID Responden' not in str(df.columns[1]): raise DataQualityError('Kolom kedua formulir awal bukan ID Responden')
    output=[]; errors=[]; seen=set()
    for i, record in enumerate(df.itertuples(index=False,name=None),start=2):
        rid=clean_str(record[1])
        if not rid: errors.append({'row':i,'reason':'ID responden kosong'}); continue
        if rid in seen: errors.append({'row':i,'reason':'ID responden duplikat'}); continue
        seen.add(rid)
        row={name:clean_str(record[idx]) for name,idx in PROFILE_INDEX.items()}
        row['age']=numeric(record[3],0,120)
        row['height_cm']=numeric(record[20],80,250)
        row['weight_kg']=numeric(record[21],15,300)
        row['bmi']=(round(row['weight_kg']/((row['height_cm']/100)**2),3) if row['height_cm'] and row['weight_kg'] else None)
        row['active_days_week']=numeric(record[23],0,7)
        row['conditions_json']=json.dumps(dict(zip(CONDITIONS,[clean_str(v) for v in record[9:20]])),ensure_ascii=False)
        output.append(row)
    return output,errors

def parse_days(df, profile_ids, synthetic=True):
    verify_headers(df,EXPECTED_DAILY_HEADERS,'Form Harian')
    if 'ID Responden' not in str(df.columns[1]): raise DataQualityError('Kolom kedua formulir harian bukan ID Responden')
    all_days=[]; sessions=[]; errors=[]; duplicates=set(); keys=set(); missing_sleep=0; missing_sitting=0; suspicious_dates=[]; invalid_bp=[]
    for i, rec in enumerate(df.itertuples(index=False,name=None),start=2):
        rid=clean_str(rec[1]); d=clean_date(rec[2])
        if not rid or not d or rid not in profile_ids:
            errors.append({'row':i,'reason':'ID kosong/tidak ditemukan di form awal atau tanggal tidak valid'}); continue
        key=(rid,d)
        if key in keys:
            duplicates.add(key); errors.append({'row':i,'reason':'Duplikasi ID + tanggal (ditahan untuk pemeriksaan)'});continue
        keys.add(key)
        if d.year<2024 or d.year>2030:
            suspicious_dates.append({'row':i,'date':str(d),'reason':'Tanggal di luar periode kerja yang diharapkan; periksa sumber'})
        day={'respondent_id':rid,'date':d}
        day.update({k:clean_str(rec[ix]) for k,ix in DAY_INDEX.items() if k not in ('respondent_id','date')})
        for col in ('activity_minutes','heavy_minutes','smoke_count'):
            val=numeric(day[col],0,1440 if col!='smoke_count' else 100)
            day[col]=int(val) if val is not None else None
        stress=clean_str(rec[27]); m=re.match(r'^([1-5])\b',stress or '')
        day['stress']=int(m.group(1)) if m else None
        day['sleep_hours']=sleep_hours(rec[19], synthetic=synthetic)
        if day['sleep_hours'] is None: missing_sleep+=1
        if day['sitting'] is None: missing_sitting+=1
        all_days.append({k:v for k,v in day.items() if k not in [n for n in DAY_INDEX if n.startswith('morning_') or n.startswith('evening_')] and k!='sleep'})
        for session,prefix in [('Pagi','morning'),('Malam','evening')]:
            part=[]
            for suffix,lo,hi in [('sbp1',60,260),('dbp1',35,170),('sbp2',60,260),('dbp2',35,170)]:
                v=numeric(day[f'{prefix}_{suffix}'],lo,hi)
                if clean_str(day[f'{prefix}_{suffix}']) is not None and v is None:
                    invalid_bp.append({'row':i,'session':session,'field':suffix,'raw':clean_str(day[f'{prefix}_{suffix}'])})
                part.append(v)
            a,b,c,e=part; sbp=[n for n in (a,c) if n is not None]; dbp=[n for n in (b,e) if n is not None]
            sessions.append({'respondent_id':rid,'date':d,'session':session,'measured_at':day[f'{prefix}_time'],
                'sbp1':a,'dbp1':b,'sbp2':c,'dbp2':e,'sbp_mean':float(np.mean(sbp)) if sbp else None,
                'dbp_mean':float(np.mean(dbp)) if dbp else None,'valid_sbp_count':len(sbp),'valid_dbp_count':len(dbp),
                'before_activity':day[f'{prefix}_context']})
    quality={'raw_profiles':len(profile_ids),'raw_daily':len(df),'accepted_daily':len(all_days),'rejected_daily':len(errors),
             'valid_sessions':sum(1 for x in sessions if x['sbp_mean'] is not None and x['dbp_mean'] is not None),
             'missing_sleep':missing_sleep,'missing_sitting':missing_sitting,'duplicate_pairs':len(duplicates),
             'rejections':errors[:40], 'suspicious_dates':suspicious_dates[:40], 'invalid_bp_readings':invalid_bp[:40],
             'invalid_bp_count':len(invalid_bp), 'assumption_sleep':'HH:MM pada CSV SINTETIS ditafsirkan durasi jam:menit; untuk data aktual tidak otomatis dikonversi.'}
    return all_days,sessions,quality

def prepare(profiles_df,days_df,synthetic=True):
    profiles,profile_errors=parse_profiles(profiles_df)
    days,sessions,quality=parse_days(days_df,{r['respondent_id'] for r in profiles},synthetic)
    quality['rejected_profiles']=len(profile_errors)
    quality['profile_rejections']=profile_errors[:40]
    quality['accepted_profiles']=len(profiles)
    if not profiles or not days: raise DataQualityError('Tidak ada data profil/harian valid yang dapat dimuat')
    return profiles,days,sessions,quality

def load_warehouse(db:Session,profiles,days,sessions,quality,source_name='CSV sintetis',kind='synthetic'):
    """Transaction with explicitly separated profile, daily and session facts."""
    for model in (BPSession,DailyBehavior,Participant,CalendarDate,SessionType,SourceState):
        db.execute(delete(model))
    db.flush()
    for row in profiles: db.add(Participant(**row))
    for d in sorted({x['date'] for x in days}): db.add(CalendarDate(date=d,year=d.year,month=d.month,day=d.day))
    db.add_all([SessionType(name='Pagi'),SessionType(name='Malam')]);db.flush()
    pids={p.respondent_id:p.id for p in db.scalars(select(Participant)).all()}
    dates={d.date:d.id for d in db.scalars(select(CalendarDate)).all()}
    sids={s.name:s.id for s in db.scalars(select(SessionType)).all()}
    for row in days:
        r=dict(row);rid=r.pop('respondent_id');d=r.pop('date')
        db.add(DailyBehavior(participant_id=pids[rid],date_id=dates[d],**r))
    for row in sessions:
        r=dict(row);rid=r.pop('respondent_id');d=r.pop('date');s=r.pop('session')
        db.add(BPSession(participant_id=pids[rid],date_id=dates[d],session_id=sids[s],**r))
    db.add(SourceState(id=1,source_name=source_name,source_kind=kind,row_count=len(days),quality_json=json.dumps(quality,ensure_ascii=False)))
    db.commit()
    return quality

def seed_if_empty(db:Session,root=None):
    if db.get(SourceState,1): return False
    folder=Path(root or __import__('os').getenv('SAMPLE_DATA_DIR','/app/data/sample'))
    a=folder/'Data_Responden_Sintetis.csv';b=folder/'Data_Harian_Sintetis.csv'
    if not a.exists() or not b.exists(): raise FileNotFoundError(f'Synthetic fixtures missing in {folder}')
    profiles,days,sessions,quality=prepare(pd.read_csv(a,dtype=str,keep_default_na=False),pd.read_csv(b,dtype=str,keep_default_na=False))
    load_warehouse(db,profiles,days,sessions,quality,'Data sintetis dua formulir (SIM001–SIM019)','synthetic')
    return True
