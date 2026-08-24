"""Database tables."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, Index
from sqlalchemy.types import JSON
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True, max_length=255)
    password_hash: str
    name: str = Field(max_length=120)
    lang: str = Field(default="en", max_length=5)
    created_at: datetime = Field(default_factory=utcnow)


class Assessment(SQLModel, table=True):
    __tablename__ = "assessments"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    input_text: str
    lang: str = Field(default="en", max_length=5)
    condition_key: str = Field(max_length=64)
    condition: str
    condition_hi: str
    category: str = Field(max_length=32)
    confidence: float
    symptoms: list = Field(default_factory=list, sa_column=Column(JSON))
    red_flags: list = Field(default_factory=list, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utcnow)


class Plan(SQLModel, table=True):
    __tablename__ = "plans"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    assessment_id: int | None = Field(default=None, foreign_key="assessments.id")
    condition: str
    category: str = Field(max_length=32)
    is_active: bool = Field(default=True, index=True)
    content: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utcnow)


class ExerciseSession(SQLModel, table=True):
    """One completed (or abandoned) attempt at an exercise."""

    __tablename__ = "sessions"
    __table_args__ = (Index("ix_sessions_user_created", "user_id", "created_at"),)

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    exercise_slug: str = Field(max_length=64, index=True)
    exercise_name: str

    reps: int = 0
    target_reps: int = 0
    quality: int = 0                 # 0-100
    rom_degrees: float = 0.0
    duration_seconds: float = 0.0
    tracked_ratio: float = 0.0
    mean_tempo_seconds: float = 0.0
    completed: bool = False
    # Whether rep thresholds were calibrated to this patient's own range, and
    # whether they reached the exercise's clinical target range.
    adaptive: bool = False
    target_rom: float = 0.0
    target_met: bool = False

    errors: list = Field(default_factory=list, sa_column=Column(JSON))
    angle_series: list = Field(default_factory=list, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utcnow)


class Report(SQLModel, table=True):
    __tablename__ = "reports"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    filename: str = Field(max_length=255)
    stored_name: str = Field(max_length=255)
    content_type: str = Field(max_length=100)
    size_bytes: int = 0
    extracted_text: str = ""
    findings: list = Field(default_factory=list, sa_column=Column(JSON))
    engine: str = Field(default="none", max_length=32)
    created_at: datetime = Field(default_factory=utcnow)
