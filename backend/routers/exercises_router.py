"""Exercise catalogue and the pose configs that drive live tracking."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ..physio.exercise_data import BY_SLUG, CATEGORIES, EXERCISES

router = APIRouter(prefix="/api/exercises", tags=["exercises"])


def _public(ex: dict) -> dict:
    """Catalogue view: everything except the raw biomechanics config.

    `pose_mode` is surfaced because the UI labels holds differently from reps,
    but the thresholds and landmark indices stay behind /pose-config.
    """
    out = {k: v for k, v in ex.items() if k != "pose"}
    out["pose_mode"] = ex["pose"].get("mode", "range")
    return out


@router.get("")
def list_exercises(
    category: str | None = Query(default=None),
    difficulty: str | None = Query(default=None),
) -> dict:
    items = EXERCISES
    if category and category != "all":
        if category not in CATEGORIES:
            raise HTTPException(404, f"Unknown category: {category}")
        items = [e for e in items if e["category"] == category]
    if difficulty:
        items = [e for e in items if e["difficulty"] == difficulty]
    return {"categories": CATEGORIES, "count": len(items),
            "items": [_public(e) for e in items]}


@router.get("/{slug}")
def get_exercise(slug: str) -> dict:
    ex = BY_SLUG.get(slug)
    if not ex:
        raise HTTPException(404, "Exercise not found")
    return _public(ex)


@router.get("/{slug}/pose-config")
def get_pose_config(slug: str) -> dict:
    """Biomechanics rules the browser evaluates per frame for the live HUD.

    The server re-runs these same rules over the full timeline when the
    session is submitted, so the live feedback and the saved score agree.
    """
    ex = BY_SLUG.get(slug)
    if not ex:
        raise HTTPException(404, "Exercise not found")
    return {
        "slug": slug,
        "target_reps": ex["target_reps"],
        "duration_seconds": ex["duration_seconds"],
        **ex["pose"],
    }
