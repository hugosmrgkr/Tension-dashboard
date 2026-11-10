"""Migration guards: no row replacement, no data drift, no actual-source promotion."""
import json
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Participant,SourceState,DailyBehavior,BPSession
from app.pipeline import load_warehouse,DataQualityError
from app.warehouse_audit import audit_warehouse
from app.warehouse_sync import reconcile_synthetic


@pytest.fixture
def legacy(warehouse_engine,prepared):
    with Session(warehouse_engine) as db:
        load_warehouse(db,*prepared)
        for p in db.scalars(select(Participant)):p.active_days_week=None
        for row in db.scalars(select(BPSession)):row.measured_at=row.measured_at[:5]
        db.get(SourceState,1).quality_json='{}';db.commit()
    return warehouse_engine


def test_preview_preserves_database_and_commit_preserves_ids(legacy,prepared):
    with Session(legacy) as db:
        before=audit_warehouse(db);ids=dict(db.execute(select(Participant.respondent_id,Participant.id)).all())
        preview=reconcile_synthetic(db,prepared)
        assert preview['weekly_activity_rows_to_fill']==19 and not preview['committed']
        assert preview['equivalent_time_formats_to_normalize']==1140
        assert audit_warehouse(db)==before
        result=reconcile_synthetic(db,prepared,commit=True,expected_current_hash=before['natural_content_sha256'])
        assert result['after']['missing_active_days_week']==0 and result['after']['counts']==before['counts']
        assert dict(db.execute(select(Participant.respondent_id,Participant.id)).all())==ids
        again=reconcile_synthetic(db,prepared)
        assert again['weekly_activity_rows_to_fill']==0 and not again['metadata_refresh_needed']
        assert json.loads(db.get(SourceState,1).quality_json)['prepared_content_sha256']==prepared[3]['prepared_content_sha256']


@pytest.mark.parametrize('change',['daily','weekly','source','hash','time'])
def test_conflicts_abort_before_any_update(legacy,prepared,change):
    with Session(legacy) as db:
        if change=='daily':
            row=db.scalar(select(DailyBehavior));row.stress=1 if row.stress!=1 else 5
        if change=='weekly':db.scalar(select(Participant)).active_days_week=99
        if change=='time':db.scalar(select(BPSession)).measured_at='12:34:56'
        if change=='source':db.get(SourceState,1).source_kind='actual'
        db.commit();before=audit_warehouse(db)
        with pytest.raises(DataQualityError):
            reconcile_synthetic(db,prepared,commit=True,expected_current_hash='stale' if change=='hash' else before['natural_content_sha256'])
        assert audit_warehouse(db)==before


def test_failure_after_flush_rolls_back_all_updates(legacy,prepared,monkeypatch):
    import app.warehouse_sync as module
    original=module.audit_warehouse;calls=0
    def injected(db):
        nonlocal calls
        calls+=1
        result=original(db)
        if calls==3:result['natural_content_sha256']='injected-after-flush-failure'
        return result
    with Session(legacy) as db:
        before=audit_warehouse(db);monkeypatch.setattr(module,'audit_warehouse',injected)
        with pytest.raises(DataQualityError,match='rolling back'):
            reconcile_synthetic(db,prepared,commit=True,expected_current_hash=before['natural_content_sha256'])
        assert original(db)==before and db.get(SourceState,1).quality_json=='{}'
