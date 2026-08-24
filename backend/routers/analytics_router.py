"""Recovery analytics: trends, streaks, and the most frequent form errors."""

from __future__ import annotations

from collections import Counter
from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from ..auth import current_user
from ..db import get_session
from ..models import ExerciseSession, User
from ..schemas import AnalyticsOut, TrendPoint

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

# Sessions with no pose tracking carry no quality signal, so they are counted
# for reps but excluded from quality and ROM trends.
TRACKED_THRESHOLD = 0.6


def _streak(days: set[date]) -> int:
    """Consecutive days ending today or yesterday (today may not be done yet)."""
    if not days:
        return 0
    today = date.today()
    cursor = today if today in days else today - timedelta(days=1)
    if cursor not in days:
        return 0
    count = 0
    while cursor in days:
        count += 1
        cursor -= timedelta(days=1)
    return count


@router.get("", response_model=AnalyticsOut)
def analytics(
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
) -> AnalyticsOut:
    rows = session.exec(
        select(ExerciseSession)
        .where(ExerciseSession.user_id == user.id)
        .order_by(ExerciseSession.created_at)
    ).all()

    if not rows:
        return AnalyticsOut(
            total_sessions=0, total_reps=0, average_quality=0.0, latest_quality=0,
            latest_rom=0.0, quality_delta=0.0, rom_delta=0.0, streak_days=0,
            quality_trend=[], rom_trend=[], common_errors=[],
            summary="No sessions recorded yet. Complete an exercise to start tracking.",
            summary_hi="अभी कोई सत्र दर्ज नहीं। ट्रैकिंग शुरू करने के लिए व्यायाम पूरा करें।",
        )

    tracked = [r for r in rows if r.tracked_ratio >= TRACKED_THRESHOLD]

    quality_trend = [
        TrendPoint(date=r.created_at, value=r.quality, label=r.exercise_name)
        for r in tracked
    ]
    rom_trend = [
        TrendPoint(date=r.created_at, value=r.rom_degrees, label=r.exercise_name)
        for r in tracked
    ]

    qualities = [r.quality for r in tracked]
    roms = [r.rom_degrees for r in tracked]

    latest_quality = qualities[-1] if qualities else 0
    latest_rom = roms[-1] if roms else 0.0
    quality_delta = (qualities[-1] - qualities[0]) if len(qualities) >= 2 else 0.0
    rom_delta = (roms[-1] - roms[0]) if len(roms) >= 2 else 0.0
    average_quality = round(sum(qualities) / len(qualities), 1) if qualities else 0.0

    counter = Counter()
    labels: dict[str, str] = {}
    labels_hi: dict[str, str] = {}
    for r in rows:
        for err in r.errors or []:
            rule_id = err.get("id", "unknown")
            if rule_id == "untracked":
                continue
            counter[rule_id] += 1
            labels[rule_id] = err.get("message", rule_id)
            labels_hi[rule_id] = err.get("message_hi", rule_id)

    denominator = len(tracked) or 1
    common_errors = [
        {
            "id": rule_id,
            "message": labels.get(rule_id, rule_id),
            "message_hi": labels_hi.get(rule_id, rule_id),
            "count": count,
            "percent": round(count / denominator * 100),
        }
        for rule_id, count in counter.most_common(4)
    ]

    summary, summary_hi = _summarize(
        len(rows), len(tracked), quality_delta, rom_delta, common_errors, labels,
        labels_hi,
    )

    return AnalyticsOut(
        total_sessions=len(rows),
        total_reps=sum(r.reps for r in rows),
        average_quality=average_quality,
        latest_quality=latest_quality,
        latest_rom=latest_rom,
        quality_delta=round(quality_delta, 1),
        rom_delta=round(rom_delta, 1),
        streak_days=_streak({r.created_at.date() for r in rows}),
        quality_trend=quality_trend,
        rom_trend=rom_trend,
        common_errors=common_errors,
        summary=summary,
        summary_hi=summary_hi,
    )


def _summarize(total, tracked, q_delta, rom_delta, errors, labels, labels_hi):
    if tracked == 0:
        return (
            f"{total} session(s) recorded, but none had pose tracking. "
            "Enable your camera to get form quality and range-of-motion data.",
            f"{total} सत्र दर्ज हुए, पर किसी में पोज़ ट्रैकिंग नहीं थी। "
            "फॉर्म गुणवत्ता और गति सीमा के लिए कैमरा चालू करें।",
        )
    if tracked == 1:
        return (
            "First tracked session recorded. Complete a few more to see your trend.",
            "पहला ट्रैक किया गया सत्र दर्ज। रुझान देखने के लिए कुछ और सत्र करें।",
        )

    if q_delta >= 0:
        en = f"Your form quality improved by {abs(q_delta):.0f}% across {tracked} tracked sessions."
        hi = f"{tracked} ट्रैक किए गए सत्रों में आपकी फॉर्म गुणवत्ता {abs(q_delta):.0f}% बेहतर हुई।"
    else:
        en = f"Form quality dropped {abs(q_delta):.0f}%. Slow down and focus on control."
        hi = f"फॉर्म गुणवत्ता {abs(q_delta):.0f}% गिरी है। गति धीमी करें और नियंत्रण पर ध्यान दें।"

    if rom_delta > 2:
        en += f" Range of motion is up {rom_delta:.0f} degrees - good progress."
        hi += f" गति सीमा {rom_delta:.0f} डिग्री बढ़ी है - अच्छी प्रगति।"

    if errors:
        top = errors[0]
        en += f" Most frequent issue: {top['message'].lower()}."
        hi += f" सबसे आम समस्या: {top['message_hi']}।"

    return en, hi
