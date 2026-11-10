"""Read-only checks for dimensional keys, grain, counts and ETL equivalence."""
import hashlib
import json
from sqlalchemy import select, func, inspect
from .models import Participant, CalendarDate, SessionType, BPSession, DailyBehavior, SourceState


def audit_warehouse(db):
    tables=[Participant,CalendarDate,SessionType,BPSession,DailyBehavior,SourceState]
    # Inspect within this transaction; a separate Engine inspection can roll
    # back an uncommitted SQLite connection shared by an in-memory test pool.
    inspector=inspect(db.connection())
    counts={m.__tablename__:db.scalar(select(func.count()).select_from(m)) for m in tables}
    keys={m.__tablename__:dict(pk=inspector.get_pk_constraint(m.__tablename__)['constrained_columns'],
                              foreign_keys=[dict(columns=f['constrained_columns'],table=f['referred_table'],referred=f['referred_columns']) for f in inspector.get_foreign_keys(m.__tablename__)],
                              unique=[u['column_names'] for u in inspector.get_unique_constraints(m.__tablename__)],
                              unique_indexes=[u['column_names'] for u in inspector.get_indexes(m.__tablename__) if u.get('unique')]) for m in tables}
    orphans={}
    for fact,dims in [(BPSession,[(Participant,'participant_id'),(CalendarDate,'date_id'),(SessionType,'session_id')]),
                      (DailyBehavior,[(Participant,'participant_id'),(CalendarDate,'date_id')])]:
        for dimension,fk in dims:
            orphans[f'{fact.__tablename__}.{fk}']=db.scalar(select(func.count()).select_from(fact).outerjoin(dimension,getattr(fact,fk)==dimension.id).where(dimension.id.is_(None)))
    bp=select(Participant.respondent_id,CalendarDate.date,SessionType.name,BPSession.sbp1,BPSession.dbp1,
              BPSession.sbp2,BPSession.dbp2,BPSession.sbp_mean,BPSession.dbp_mean,BPSession.measured_at,
              BPSession.valid_sbp_count,BPSession.valid_dbp_count,BPSession.before_activity).select_from(BPSession).join(
              Participant,BPSession.participant_id==Participant.id).join(CalendarDate,BPSession.date_id==CalendarDate.id).join(SessionType,BPSession.session_id==SessionType.id)
    daily=select(Participant.respondent_id,CalendarDate.date,*[getattr(DailyBehavior,c) for c in
                 ['activity_type','activity_minutes','heavy_minutes','sitting','sleep_hours','salty_food','fruit','vegetable','caffeine','smoked','smoke_count','medication','stress']]).select_from(DailyBehavior).join(
                 Participant,DailyBehavior.participant_id==Participant.id).join(CalendarDate,DailyBehavior.date_id==CalendarDate.id)
    profiles=select(*[c for c in Participant.__table__.columns if c.name!='id'])
    def rows(query):
        return sorted([list(r) for r in db.execute(query)],key=lambda r:json.dumps(r,default=str,ensure_ascii=False))
    content=dict(profiles=rows(profiles),daily=rows(daily),sessions=rows(bp))
    state=db.get(SourceState,1)
    return dict(counts=counts,keys=keys,orphans=orphans,
                missing_active_days_week=db.scalar(select(func.count()).select_from(Participant).where(Participant.active_days_week.is_(None))),
                source_kind=state.source_kind if state else None,
                natural_content_sha256=hashlib.sha256(json.dumps(content,default=str,ensure_ascii=False).encode()).hexdigest())
