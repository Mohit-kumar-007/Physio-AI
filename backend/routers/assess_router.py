"""Symptom assessment. Works logged-out; persists history when logged in."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session, desc, select

from ..auth import optional_user
from ..db import get_session
from ..models import Assessment, User
from ..physio import diagnosis
from ..schemas import AssessIn, AssessOut

router = APIRouter(prefix="/api", tags=["assessment"])


@router.post("/assess", response_model=AssessOut)
def assess(
    body: AssessIn,
    session: Session = Depends(get_session),
    user: User | None = Depends(optional_user),
) -> AssessOut:
    result = diagnosis.analyze(body.text, body.lang)

    record_id = None
    if user:
        record = Assessment(
            user_id=user.id,
            input_text=body.text,
            lang=body.lang,
            condition_key=result.condition_key,
            condition=result.condition,
            condition_hi=result.condition_hi,
            category=result.category,
            confidence=result.confidence,
            symptoms=result.symptoms,
            red_flags=result.red_flags,
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        record_id = record.id

    return AssessOut(
        id=record_id,
        condition=result.condition,
        condition_hi=result.condition_hi,
        condition_key=result.condition_key,
        category=result.category,
        confidence=result.confidence,
        symptoms=result.symptoms,
        symptoms_hi=result.symptoms_hi,
        advice=result.advice,
        advice_hi=result.advice_hi,
        reply=result.reply(body.lang),
        red_flags=result.red_flags,
        alternatives=result.alternatives,
        is_confident=result.is_confident,
        matched_terms=result.matched_terms,
    )


@router.get("/assessments")
def history(
    session: Session = Depends(get_session),
    user: User = Depends(optional_user),
    limit: int = 20,
) -> dict:
    if not user:
        return {"items": []}
    rows = session.exec(
        select(Assessment)
        .where(Assessment.user_id == user.id)
        .order_by(desc(Assessment.created_at))
        .limit(min(limit, 100))
    ).all()
    return {"items": [r.model_dump() for r in rows]}
