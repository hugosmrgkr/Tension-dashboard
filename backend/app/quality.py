"""Reproducible quality measurements, without names or raw free-text values."""
from collections import Counter
import hashlib
import json
import pandas as pd
from .survey_schema import PROFILE_FIELDS, DAILY_FIELDS, text, parse_value


def missing(value):
    return value is None or pd.isna(value) or text(value) is None


def completeness(raw, clean, specs, source, issues, synthetic):
    before, after = [], []
    for index, spec in enumerate(specs):
        name = spec['technical']
        values = raw.iloc[:, index].tolist()
        missing_count = sum(missing(v) for v in values)
        invalid = sum(i['field'] == name and i['action'] == 'set_null' for i in issues)
        canonical = spec['categories']
        noncanonical = sum(text(v) is not None and str(v).strip() not in canonical for v in values) if canonical else 0
        common = dict(source=source, column=index+1, original_name=str(raw.columns[index]), field=name,
                      policy='excluded_identity' if spec['kind']=='excluded' else 'audit_metadata' if spec['kind']=='timestamp' else 'analytic')
        before.append(dict(**common, rows=len(values), missing=missing_count,
                           missing_percent=round(100*missing_count/len(values),3) if values else 0,
                           invalid=invalid, noncanonical=noncanonical))
        if common['policy'] == 'excluded_identity':
            after.append(dict(**common,rows=len(clean),missing=None,missing_percent=None,invalid=None,noncanonical=None))
            continue
        cleaned = [row.get(name) for row in clean]
        absent = sum(missing(v) for v in cleaned)
        # Validity is measured on non-missing observations; removed invalid values
        # remain visible as missing and as issues, never counted as repaired answers.
        invalid_after = sum(not missing(v) and parse_value(v,spec,synthetic)[1] not in (None,'unmapped_other_category_review') for v in cleaned)
        after.append(dict(**common, rows=len(clean), missing=absent,
                          missing_percent=round(100*absent/len(clean),3) if clean else 0,
                          invalid=invalid_after, noncanonical=0 if canonical else None))
    return before, after


def pressure_anomalies(sessions, source_rows):
    summaries, flags = [], []
    for session in ('Pagi','Malam'):
        for field in ('sbp_mean','dbp_mean'):
            values=pd.Series([row[field] for row in sessions if row['session']==session],dtype=float).dropna()
            q1,q3=(float(values.quantile(.25)),float(values.quantile(.75))) if len(values) else (None,None)
            low,high=(q1-1.5*(q3-q1),q3+1.5*(q3-q1)) if q1 is not None else (None,None)
            found=[]
            if len(values)>=4:
                for index,row in enumerate(sessions,start=1):
                    value=row[field]
                    if row['session']==session and value is not None and (value<low or value>high):
                        found.append(dict(session_index=index,source_row=source_rows[index-1],session=session,field=field,value=value,
                                          action='retain_for_review',method='1.5 IQR within session'))
            summaries.append(dict(session=session,field=field,n=len(values),q1=q1,q3=q3,lower=low,upper=high,flagged=len(found)))
            flags.extend(found)
    return dict(method='1.5 IQR pada rerata per sesi; statistik eksploratif, bukan ambang diagnosis',
                summaries=summaries, flags=flags, flagged_values=len(flags),
                flagged_sessions=len({row['session_index'] for row in flags}), removed_sessions=0)


def build_quality(profiles_raw, daily_raw, profiles, days, sessions, audit, legacy, synthetic):
    before, after = [], []
    for raw, specs, source in [(profiles_raw,PROFILE_FIELDS,'profiles'),(daily_raw,DAILY_FIELDS,'daily')]:
        b,a=completeness(raw,audit['profile_clean' if source=='profiles' else 'daily_clean'],
                         specs,source,audit['profile_issues' if source=='profiles' else 'daily_issues'],synthetic)
        before.extend(b); after.extend(a)
    issues=audit['profile_issues']+audit['daily_issues']+audit['consistency_issues']
    accepted_profile_ids={row['respondent_id'] for row in profiles}
    # Raw input checks do not disclose the values of invalid identifiers.
    ids=profiles_raw.iloc[:,1].map(text)
    raw_days=pd.DataFrame({'id':daily_raw.iloc[:,1].map(text),
                          'date':daily_raw.iloc[:,2].map(lambda v:parse_value(v,DAILY_FIELDS[2],synthetic)[0])})
    valid_keys=raw_days.dropna()
    normalizations=audit['profile_changes']+audit['daily_changes']
    return dict(
        audit_version='cp2-1',bp_policy_version='paired-reading-review-v1',
        prepared_content_sha256=hashlib.sha256(json.dumps(dict(profiles=profiles,days=days,sessions=sessions),
                                                         default=str,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),
        schema_fingerprint=hashlib.sha256(json.dumps([list(profiles_raw.columns),list(daily_raw.columns)],ensure_ascii=False).encode()).hexdigest(),
        before=before, after=after,
        issues=issues, issue_counts=dict(Counter(i['code'] for i in issues)),
        normalizations_by_field=dict(Counter(i['field'] for i in normalizations)),
        row_outcomes={
            'profiles':dict(raw=len(profiles_raw),accepted=len(profiles),quarantined=legacy['rejected_profiles'],rejected_schema=0),
            'daily':dict(raw=len(daily_raw),accepted=len(days),quarantined=legacy['rejected_daily'],rejected_schema=0),
            'sessions':dict(derived=len(sessions),valid=legacy['valid_sessions'],incomplete=len(sessions)-legacy['valid_sessions'])},
        uniqueness=dict(profile_duplicate_excess=int(ids.dropna().duplicated().sum()),
                        daily_duplicate_excess=int(valid_keys.duplicated(['id','date']).sum()),
                        clean_profile_duplicate_excess=len(profiles)-len(accepted_profile_ids),
                        clean_daily_duplicate_excess=len(days)-len({(r['respondent_id'],r['date']) for r in days})),
        consistency=dict(unmatched_daily_rows=int((raw_days.id.notna() & ~raw_days.id.isin(accepted_profile_ids)).sum()),
                         clean_unmatched_daily_rows=sum(d['respondent_id'] not in accepted_profile_ids for d in days),
                         issues=audit['consistency_issues'],
                         units='tahun; cm; kg; mmHg; menit; hari/minggu; stres 1–5; tidur asumsi simulasi'),
        pressure_anomalies=pressure_anomalies(sessions,audit['session_source_rows']),
        policies=dict(invalid_cell='NA + issue; raw CSV tidak diubah',
                      duplicate='Identik: pertama diterima; konflik: semua versi dikarantina tanpa memilih urutan. Koreksi perlu versi sumber/decision log',
                      quarantine='Laporan menyimpan nomor baris/reason; raw lengkap tetap pada sumber privat, tidak disalin ke laporan publik',
                      categories='Enum yang diketahui dinormalisasi kapital/spasi; pilihan terbuka ditahan untuk review tanpa menebak kategori',
                      suspicious_date='Tanggal mencurigakan dikarantina untuk keputusan sumber; raw dipertahankan',
                      outliers='IQR saja: flag, tanpa vonis klinis; pasangan BP ambigu/SBP<=DBP: pending_review, dikecualikan dari mean/model; raw dipertahankan'),
    )
