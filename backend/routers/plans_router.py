"""Recovery plan generation and retrieval."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, desc, select

from ..auth import current_user
from ..db import get_session
from ..models import Assessment, Plan, User
from ..physio import diagnosis, planner
from ..schemas import PlanIn, PlanOut

router = APIRouter(prefix="/api/plans", tags=["plans"])


@router.post("", response_model=PlanOut, status_code=201)
def create_plan(
    body: PlanIn,
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
) -> PlanOut:
    """Build a plan from a named assessment, or the user's most recent one."""
    query = select(Assessment).where(Assessment.user_id == user.id)
    if body.assessment_id is not None:
        query = query.where(Assessment.id == body.assessment_id)
    else:
        query = query.order_by(desc(Assessment.created_at))
    assessment = session.exec(query).first()

    if assessment is None:
        raise HTTPException(
            404,
            "No assessment found. Describe your symptoms in the AI Assistant first.",
        )

    # Rebuild the diagnosis object the planner expects from the stored row.
    result = diagnosis.from_condition_key(
        assessment.condition_key, assessment.confidence, assessment.red_flags
    )
    content = planner.build_plan(result, body.lang)

    # Only one active plan at a time; older ones stay as history.
    for old in session.exec(
        select(Plan).where(Plan.user_id == user.id, Plan.is_active == True)  # noqa: E712
    ).all():
        old.is_active = False
        session.add(old)

    plan = Plan(
        user_id=user.id,
        assessment_id=assessment.id,
        condition=assessment.condition,
        category=assessment.category,
        content=content,
        is_active=True,
    )
    session.add(plan)
    session.commit()
    session.refresh(plan)
    return PlanOut(**plan.model_dump())


@router.get("/active", response_model=PlanOut)
def active_plan(
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
) -> PlanOut:
    plan = session.exec(
        select(Plan)
        .where(Plan.user_id == user.id, Plan.is_active == True)  # noqa: E712
        .order_by(desc(Plan.created_at))
    ).first()
    if plan is None:
        raise HTTPException(404, "No active plan yet")
    return PlanOut(**plan.model_dump())


@router.get("", response_model=list[PlanOut])
def list_plans(
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
) -> list[PlanOut]:
    rows = session.exec(
        select(Plan).where(Plan.user_id == user.id).order_by(desc(Plan.created_at))
    ).all()
    return [PlanOut(**p.model_dump()) for p in rows]
