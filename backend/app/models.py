"""Dimensional warehouse v2: new names avoid destructive changes to older installations."""
from datetime import date
from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base

class Participant(Base):
    __tablename__ = 'dim_participant_v2'
    id: Mapped[int] = mapped_column(primary_key=True)
    respondent_id: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    age: Mapped[int|None] = mapped_column(Integer, nullable=True)
    gender: Mapped[str|None] = mapped_column(String(35), nullable=True)
    province: Mapped[str|None] = mapped_column(String(100), nullable=True)
    city: Mapped[str|None] = mapped_column(String(100), nullable=True)
    occupation: Mapped[str|None] = mapped_column(String(220), nullable=True)
    education: Mapped[str|None] = mapped_column(String(150), nullable=True)
    height_cm: Mapped[float|None] = mapped_column(Float, nullable=True)
    weight_kg: Mapped[float|None] = mapped_column(Float, nullable=True)
    bmi: Mapped[float|None] = mapped_column(Float, nullable=True)
    usual_activity: Mapped[str|None] = mapped_column(Text, nullable=True)
    active_days_week: Mapped[int|None] = mapped_column(Integer, nullable=True)
    conditions_json: Mapped[str|None] = mapped_column(Text, nullable=True)

class CalendarDate(Base):
    __tablename__ = 'dim_date_v2'
    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[date] = mapped_column(Date, unique=True, index=True)
    year: Mapped[int] = mapped_column(Integer)
    month: Mapped[int] = mapped_column(Integer)
    day: Mapped[int] = mapped_column(Integer)

class SessionType(Base):
    __tablename__ = 'dim_session_v2'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(12), unique=True)

class BPSession(Base):
    __tablename__ = 'fact_bp_session_v2'
    __table_args__ = (UniqueConstraint('participant_id', 'date_id', 'session_id', name='uq_bp_session_v2'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    participant_id: Mapped[int] = mapped_column(ForeignKey('dim_participant_v2.id'), index=True)
    date_id: Mapped[int] = mapped_column(ForeignKey('dim_date_v2.id'), index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey('dim_session_v2.id'), index=True)
    measured_at: Mapped[str|None] = mapped_column(String(8), nullable=True)
    sbp1: Mapped[float|None] = mapped_column(Float, nullable=True)
    dbp1: Mapped[float|None] = mapped_column(Float, nullable=True)
    sbp2: Mapped[float|None] = mapped_column(Float, nullable=True)
    dbp2: Mapped[float|None] = mapped_column(Float, nullable=True)
    sbp_mean: Mapped[float|None] = mapped_column(Float, nullable=True)
    dbp_mean: Mapped[float|None] = mapped_column(Float, nullable=True)
    valid_sbp_count: Mapped[int] = mapped_column(Integer, default=0)
    valid_dbp_count: Mapped[int] = mapped_column(Integer, default=0)
    before_activity: Mapped[str|None] = mapped_column(String(220), nullable=True)
    participant: Mapped[Participant] = relationship()
    calendar: Mapped[CalendarDate] = relationship()
    session_type: Mapped[SessionType] = relationship()

class DailyBehavior(Base):
    __tablename__ = 'fact_daily_behavior_v2'
    __table_args__ = (UniqueConstraint('participant_id', 'date_id', name='uq_daily_behavior_v2'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    participant_id: Mapped[int] = mapped_column(ForeignKey('dim_participant_v2.id'), index=True)
    date_id: Mapped[int] = mapped_column(ForeignKey('dim_date_v2.id'), index=True)
    activity_type: Mapped[str|None] = mapped_column(Text, nullable=True)
    activity_minutes: Mapped[int|None] = mapped_column(Integer, nullable=True)
    heavy_minutes: Mapped[int|None] = mapped_column(Integer, nullable=True)
    sitting: Mapped[str|None] = mapped_column(String(90), nullable=True)
    sleep_hours: Mapped[float|None] = mapped_column(Float, nullable=True)
    salty_food: Mapped[str|None] = mapped_column(String(90), nullable=True)
    fruit: Mapped[str|None] = mapped_column(String(90), nullable=True)
    vegetable: Mapped[str|None] = mapped_column(String(90), nullable=True)
    caffeine: Mapped[str|None] = mapped_column(String(90), nullable=True)
    smoked: Mapped[str|None] = mapped_column(String(110), nullable=True)
    smoke_count: Mapped[int|None] = mapped_column(Integer, nullable=True)
    medication: Mapped[str|None] = mapped_column(String(180), nullable=True)
    stress: Mapped[int|None] = mapped_column(Integer, nullable=True)
    participant: Mapped[Participant] = relationship()
    calendar: Mapped[CalendarDate] = relationship()

class SourceState(Base):
    __tablename__ = 'dataset_state_v2'
    id: Mapped[int] = mapped_column(primary_key=True)
    source_name: Mapped[str] = mapped_column(String(240))
    source_kind: Mapped[str] = mapped_column(String(30), default='synthetic')
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    quality_json: Mapped[str|None] = mapped_column(Text, nullable=True)
