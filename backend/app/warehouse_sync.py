"""Narrow synthetic CP3 reconciliation: no DELETE, INSERT, schema or model changes."""
import hashlib
import json
import re
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session
from .db import Base
from .models import Participant, CalendarDate, SessionType, BPSession, DailyBehavior, SourceState
from .pipeline import DataQualityError, load_warehouse
from .warehouse_audit import audit_warehouse


def _snapshot(db):
    profiles={p.id:p for p in db.scalars(select(Participant))}
    dates={r.id:r for r in db.scalars(select(CalendarDate))}
    sessions={r.id:r for r in db.scalars(select(SessionType))}
    def values(row,exclude):
        return {c.name:getattr(row,c.name) for c in row.__table__.columns if c.name not in exclude}
    result=dict(profiles={p.respondent_id:values(p,{'id'}) for p in profiles.values()},
                dates={str(r.date):values(r,{'id'}) for r in dates.values()},
                sessions=sorted(r.name for r in sessions.values()),daily={},bp={})
    identities={}
    for model,key in [(DailyBehavior,'daily'),(BPSession,'bp')]:
        ids={}
        for row in db.scalars(select(model)):
            natural=(profiles[row.participant_id].respondent_id,str(dates[row.date_id].date))
            if key=='bp':natural+= (sessions[row.session_id].name,)
            name='|'.join(natural)
            result[key][name]=values(row,{'id','participant_id','date_id','session_id'})
            ids[name]=row.id
        identities[key]=ids
    identities['profiles']={p.respondent_id:p.id for p in profiles.values()}
    identities['dates']={str(r.date):r.id for r in dates.values()}
    identities['sessions']={r.name:r.id for r in sessions.values()}
    return result,identities


def reconcile_synthetic(db,prepared,*,commit=False,expected_current_hash=None):
    """Fill weekly activity, normalize HH:MM to HH:MM:00, refresh ETL metadata.

    Any other difference from the exact two CSV fixtures aborts before writes.
    Caller must provide the explicitly reviewed content hash for commit.
    """
    profiles,days,sessions,quality=prepared
    if quality.get('source_kind')!='synthetic' or not quality.get('prepared_content_sha256'):
        raise DataQualityError('Only a fingerprinted synthetic fixture can be reconciled')
    if commit and not expected_current_hash:
        raise DataQualityError('Commit requires the reviewed current warehouse hash')
    try:
        if commit and db.bind.dialect.name=='postgresql':
            db.execute(text('SELECT pg_advisory_xact_lock(73421031)'))
            names=[m.__tablename__ for m in (Participant,CalendarDate,SessionType,BPSession,DailyBehavior,SourceState)]
            db.execute(text('LOCK TABLE '+', '.join(names)+' IN SHARE ROW EXCLUSIVE MODE'))
        before=audit_warehouse(db)
        if expected_current_hash and before['natural_content_sha256']!=expected_current_hash:
            raise DataQualityError('Warehouse changed since the reviewed snapshot')
        states=list(db.scalars(select(SourceState)))
        if len(states)!=1 or states[0].id!=1 or states[0].source_kind!='synthetic' or states[0].row_count!=len(days):
            raise DataQualityError('Existing source must be the same occupied synthetic dataset')
        actual,identities=_snapshot(db)
        memory=create_engine('sqlite://')
        try:
            Base.metadata.create_all(memory)
            with Session(memory) as reference:
                load_warehouse(reference,profiles,days,sessions,quality)
                expected,_=_snapshot(reference)
                expected_audit=audit_warehouse(reference)
        finally:memory.dispose()
        patches={}
        for rid,row in actual['profiles'].items():
            target=expected['profiles'].get(rid,{})
            if row['active_days_week'] is None and target.get('active_days_week') is not None:
                patches[rid]=target['active_days_week']
                row['active_days_week']=target['active_days_week']
        time_patches={}
        for key,row in actual['bp'].items():
            old=row['measured_at'];target=expected['bp'].get(key,{}).get('measured_at')
            if isinstance(old,str) and re.fullmatch(r'\d{2}:\d{2}',old) and target==old+':00':
                time_patches[identities['bp'][key]]=target
                row['measured_at']=target
        if actual!=expected:
            raise DataQualityError('Source differs beyond missing weekly activity / equivalent time format; no automatic overwrite allowed')
        report=dict(source_kind='synthetic',before=before,
                    expected_content_sha256=expected_audit['natural_content_sha256'],
                    prepared_content_sha256=quality['prepared_content_sha256'],
                    weekly_activity_rows_to_fill=len(patches),
                    equivalent_time_formats_to_normalize=len(time_patches),
                    metadata_refresh_needed=json.loads(states[0].quality_json or '{}')!=quality,
                    surrogate_ids_preserved=True,committed=False)
        if commit:
            for row in db.scalars(select(Participant)):
                if row.respondent_id in patches:row.active_days_week=patches[row.respondent_id]
            for row in db.scalars(select(BPSession)):
                if row.id in time_patches:row.measured_at=time_patches[row.id]
            states[0].quality_json=json.dumps(quality,ensure_ascii=False)
            states[0].source_name='Dua formulir sintetis CP2 - sinkronisasi CP3 terverifikasi'
            db.flush()
            after=audit_warehouse(db)
            if after['natural_content_sha256']!=expected_audit['natural_content_sha256'] or _snapshot(db)[1]!=identities:
                raise DataQualityError('Post-update equivalence failed; rolling back')
            if after['counts']!=before['counts'] or any(after['orphans'].values()):
                raise DataQualityError('Warehouse counts or relations changed; rolling back')
            db.commit()
            report.update(committed=True,after=after)
        return report
    except Exception:
        db.rollback()
        raise
