"""Request and response shapes. Validation happens here, at the boundary."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from .auth import MAX_PASSWORD_BYTES, MIN_PASSWORD_LENGTH


# --- auth -------------------------------------------------------------------
class SignupIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str
    lang: str = Field(default="en", pattern="^(en|hi)$")

    @field_validator("password")
    @classmethod
    def strong_enough(cls, v: str) -> str:
        if len(v) < MIN_PASSWORD_LENGTH:
            raise ValueError(
                f"Password must be at least {MIN_PASSWORD_LENGTH} characters"
            )
        if len(v.encode()) > MAX_PASSWORD_BYTES:
            raise ValueError("Password is too long (max 72 bytes)")
        return v

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        return v.strip()


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    lang: str
    created_at: datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# --- assessment -------------------------------------------------------------
class AssessIn(BaseModel):
    text: str = Field(min_length=2, max_length=4000)
    lang: str = Field(default="en", pattern="^(en|hi)$")

    @field_validator("text")
    @classmethod
    def not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Please describe your symptoms")
        return v


class AssessOut(BaseModel):
    id: int | None
    condition: str
    condition_hi: str
    condition_key: str
    category: str
    confidence: float
    symptoms: list[str]
    symptoms_hi: list[str]
    advice: str
    advice_hi: str
    reply: str
    red_flags: list[str]
    alternatives: list[dict]
    is_confident: bool
    matched_terms: list[str]


# --- plans ------------------------------------------------------------------
class PlanIn(BaseModel):
    assessment_id: int | None = None
    lang: str = Field(default="en", pattern="^(en|hi)$")


class PlanOut(BaseModel):
    id: int
    condition: str
    category: str
    is_active: bool
    content: dict
    created_at: datetime


# --- sessions ---------------------------------------------------------------
class Frame(BaseModel):
    t: float = Field(ge=0, description="milliseconds since session start")
    lm: list[list[float]]

    @field_validator("lm")
    @classmethod
    def shape_ok(cls, v: list[list[float]]) -> list[list[float]]:
        if len(v) != 33:
            raise ValueError("Each frame needs exactly 33 landmarks")
        for point in v:
            if not 3 <= len(point) <= 4:
                raise ValueError("Each landmark needs [x, y, z] or [x, y, z, vis]")
        return v


class SessionIn(BaseModel):
    """Posted when a session ends. `frames` carries keypoints only, no video."""

    exercise_slug: str = Field(min_length=1, max_length=64)
    frames: list[Frame] = Field(default_factory=list)
    completed: bool = False
    lang: str = Field(default="en", pattern="^(en|hi)$")

    # Fallback for clients without a camera: report counts directly. Scored
    # separately so simulated data can never masquerade as tracked data.
    client_reps: int | None = Field(default=None, ge=0, le=1000)


class SessionOut(BaseModel):
    # None when the session was scored but not stored (no account).
    id: int | None
    exercise_slug: str
    exercise_name: str
    reps: int
    target_reps: int
    quality: int
    rom_degrees: float
    duration_seconds: float
    tracked_ratio: float
    completed: bool
    adaptive: bool
    target_rom: float
    target_met: bool
    errors: list
    created_at: datetime


# --- analytics --------------------------------------------------------------
class TrendPoint(BaseModel):
    date: datetime
    value: float
    label: str


class AnalyticsOut(BaseModel):
    total_sessions: int
    total_reps: int
    average_quality: float
    latest_quality: int
    latest_rom: float
    quality_delta: float
    rom_delta: float
    streak_days: int
    quality_trend: list[TrendPoint]
    rom_trend: list[TrendPoint]
    common_errors: list[dict]
    summary: str
    summary_hi: str


# --- reports ----------------------------------------------------------------
class ReportOut(BaseModel):
    id: int | None
    filename: str
    ok: bool
    engine: str
    summary: str
    findings: list[dict]
    suggested_text: str
    message: str = ""
