"""Exercise session submission and history.

The client posts a keypoint timeline (numbers only - the webcam video never
leaves the device) and the server produces the authoritative score.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, desc, select

from ..auth import current_user
from ..config import MAX_SESSION_FRAMES
from ..db import get_session
from ..models import ExerciseSession, User
from ..physio.exercise_data import BY_SLUG
from ..physio.pose import analyze_session
from ..schemas import SessionIn, SessionOut

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("", response_model=SessionOut, status_code=201)
def submit_session(
    body: SessionIn,
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
) -> SessionOut:
    exercise = BY_SLUG.get(body.exercise_slug)
    if exercise is None:
        raise HTTPException(404, f"Unknown exercise: {body.exercise_slug}")

    if len(body.frames) > MAX_SESSION_FRAMES:
        raise HTTPException(
            413,
            f"Too many frames ({len(body.frames)}). Maximum is {MAX_SESSION_FRAMES}.",
        )

    if body.frames:
        frames = [{"t": f.t, "lm": f.lm} for f in body.frames]
        analysis = analyze_session(frames, exercise["pose"])
        record = ExerciseSession(
            user_id=user.id,
            exercise_slug=body.exercise_slug,
            exercise_name=exercise["name"],
            reps=analysis.reps,
            target_reps=exercise["target_reps"],
            quality=analysis.quality,
            rom_degrees=analysis.rom_degrees,
            duration_seconds=analysis.duration_seconds,
            tracked_ratio=analysis.tracked_ratio,
            mean_tempo_seconds=analysis.mean_tempo_seconds,
            completed=body.completed and analysis.reps >= exercise["target_reps"],
            adaptive=analysis.adaptive,
            target_rom=analysis.target_rom,
            target_met=analysis.target_met,
            errors=[
                {"id": e.rule_id, "message": e.message_en,
                 "message_hi": e.message_hi, "rate": e.rate}
                for e in analysis.errors
            ],
            angle_series=analysis.angle_series,
        )
    else:
        # No camera. Record the attempt but mark it untracked so it can never
        # be mistaken for a pose-verified session in the analytics.
        if body.client_reps is None:
            raise HTTPException(
                422, "Send either pose frames or client_reps for an untracked session."
            )
        record = ExerciseSession(
            user_id=user.id,
            exercise_slug=body.exercise_slug,
            exercise_name=exercise["name"],
            reps=body.client_reps,
            target_reps=exercise["target_reps"],
            quality=0,
            tracked_ratio=0.0,
            completed=body.completed,
            errors=[{"id": "untracked", "message": "Recorded without pose tracking",
                     "message_hi": "पोज़ ट्रैकिंग के बिना दर्ज किया गया", "rate": 1.0}],
        )

    session.add(record)
    session.commit()
    session.refresh(record)
    return SessionOut(**record.model_dump())


@router.get("", response_model=list[SessionOut])
def list_sessions(
    limit: int = 50,
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
) -> list[SessionOut]:
    rows = session.exec(
        select(ExerciseSession)
        .where(ExerciseSession.user_id == user.id)
        .order_by(desc(ExerciseSession.created_at))
        .limit(min(limit, 200))
    ).all()
    return [SessionOut(**r.model_dump()) for r in rows]


@router.get("/{session_id}", response_model=SessionOut)
def get_one(
    session_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
) -> SessionOut:
    row = session.get(ExerciseSession, session_id)
    # Same 404 for missing and not-yours, so ids cannot be probed.
    if row is None or row.user_id != user.id:
        raise HTTPException(404, "Session not found")
    return SessionOut(**row.model_dump())
