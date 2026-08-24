"""Every exercise in the catalogue must actually count reps.

Builds a synthetic timeline per exercise that moves THAT exercise's own
measured joint through a realistic range, then asserts the analyser counts the
repetitions performed. This is the regression net for "it is not detecting" --
a wrong landmark triplet, an unreachable threshold, or a band nothing can
enter all show up here as a zero.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from backend.physio.exercise_data import EXERCISES
from backend.physio.pose import analyze_session, measure

FPS = 30
SETTLE_FRAMES = 15
PHASE_FRAMES = 26


def _base_skeleton(vis: float = 1.0) -> list[list[float]]:
    """A plausible upright body. Every landmark distinct so no angle degenerates."""
    pts = {
        0: (0.50, 0.10), 7: (0.47, 0.11), 8: (0.53, 0.11),          # nose, ears
        11: (0.44, 0.25), 12: (0.56, 0.25),                          # shoulders
        13: (0.42, 0.40), 14: (0.58, 0.40),                          # elbows
        15: (0.41, 0.55), 16: (0.59, 0.55),                          # wrists
        23: (0.46, 0.55), 24: (0.54, 0.55),                          # hips
        25: (0.45, 0.75), 26: (0.55, 0.75),                          # knees
        27: (0.44, 0.95), 28: (0.56, 0.95),                          # ankles
    }
    lm = [[0.5, 0.5, 0.0, vis] for _ in range(33)]
    for idx, (x, y) in pts.items():
        lm[idx] = [x, y, 0.0, vis]
    return lm


def _place_for_angle(lm, triplet, degrees, limb_len=0.22):
    """Move the third landmark so angle(a, b, c) equals `degrees` exactly."""
    a, b, c = triplet
    pa = np.array(lm[a][:2])
    pb = np.array(lm[b][:2])

    ba = pa - pb
    norm = np.linalg.norm(ba)
    if norm == 0:
        return
    ba = ba / norm

    theta = math.radians(degrees)
    rotated = np.array([
        ba[0] * math.cos(theta) - ba[1] * math.sin(theta),
        ba[0] * math.sin(theta) + ba[1] * math.cos(theta),
    ])
    pc = pb + rotated * limb_len
    lm[c] = [float(pc[0]), float(pc[1]), 0.0, lm[c][3]]


def build_timeline(triplet, high, low, reps):
    """A settle period then `reps` full down-and-up cycles of that joint."""
    frames, t = [], 0.0

    def push(deg):
        nonlocal t
        lm = _base_skeleton()
        _place_for_angle(lm, triplet, deg)
        frames.append({"t": t, "lm": lm})
        t += 1000 / FPS

    for _ in range(SETTLE_FRAMES):
        push(high)
    for _ in range(reps):
        for s in range(PHASE_FRAMES):
            push(high - (high - low) * s / (PHASE_FRAMES - 1))
        for s in range(PHASE_FRAMES):
            push(low + (high - low) * s / (PHASE_FRAMES - 1))
    return frames


# Realistic travel per exercise: (high, low) in image-plane degrees.
# Deliberately narrower than the configured clinical band for several of them,
# to prove a patient who cannot reach the textbook target is still counted.
RANGES = {
    "lumbar-extension": (168, 140), "cat-cow": (160, 120),
    "bird-dog": (165, 100), "straight-leg-raise": (170, 132),
    "terminal-knee-ext": (165, 148),        # stiff knee: 17 degrees only
    "squat": (172, 95), "heel-slides": (168, 100),
    "seated-knee-extension": (170, 92), "hamstring-curl": (170, 70),
    "glute-bridge": (160, 122), "hip-abduction": (172, 148),
    "pendulum": (100, 68), "wall-slides": (145, 88),
    "shoulder-flexion": (150, 25), "shoulder-abduction": (145, 22),
    "chin-tuck": (167, 152),                # only 15 degrees of travel
    "neck-lateral-flexion": (168, 145),
    "posture-row": (165, 78), "thoracic-ext": (118, 92),
}

RANGE_MODE = [e for e in EXERCISES if e["pose"].get("mode", "range") == "range"
              and e["pose"].get("angle_type") != "axis"]


@pytest.mark.parametrize("exercise", RANGE_MODE, ids=lambda e: e["slug"])
def test_exercise_counts_the_reps_performed(exercise):
    slug = exercise["slug"]
    pose = exercise["pose"]
    high, low = RANGES[slug]
    performed = 6

    frames = build_timeline(pose["primary_angle"], high, low, performed)
    result = analyze_session(frames, pose)

    assert result.reps == performed, (
        f'{slug}: performed {performed} reps over {high}-{low} degrees but '
        f'counted {result.reps} (rom={result.rom_degrees}, '
        f'band={pose["rep_low"]}-{pose["rep_high"]}, adaptive={result.adaptive})'
    )
    assert result.tracked_ratio > 0.9, slug


@pytest.mark.parametrize("exercise", RANGE_MODE, ids=lambda e: e["slug"])
def test_exercise_counts_the_same_on_the_right_side(exercise):
    """Mirror the movement onto the right limb; the count must not change."""
    pose = exercise["pose"]
    mirror = pose.get("primary_angle_mirror")
    if not mirror:
        pytest.skip("central measurement, no side")

    high, low = RANGES[exercise["slug"]]
    frames = build_timeline(mirror, high, low, 5)
    result = analyze_session(frames, pose)
    assert result.reps == 5, f'{exercise["slug"]} right side counted {result.reps}'


def _measure_one(lm, pose):
    coords = np.array([[p[:3] for p in lm]], dtype=float)
    vis = np.array([[p[3] for p in lm]], dtype=float)
    return measure(coords, vis, pose)[0]


@pytest.mark.parametrize("exercise", EXERCISES, ids=lambda e: e["slug"])
def test_measured_joint_responds_to_movement(exercise):
    """Moving the tracked limb must move the measured angle.

    A resting straight leg legitimately reads 180 degrees, so being collinear
    at rest proves nothing. What matters is sensitivity: if bending the joint
    barely shifts the number, the triplet is wired to the wrong landmarks and
    the exercise will never count a rep however well the patient performs it.
    """
    pose = exercise["pose"]
    if pose.get("angle_type") == "axis":
        pytest.skip("rotation is exercised by its own test")

    rest = _base_skeleton()
    assert not np.isnan(_measure_one(rest, pose)), exercise["slug"]

    moved = _base_skeleton()
    _place_for_angle(moved, pose["primary_angle"], 90)
    delta = abs(_measure_one(rest, pose) - _measure_one(moved, pose))

    assert delta > 30, (
        f'{exercise["slug"]}: bending the tracked joint moved the measured '
        f'angle by only {delta:.1f} degrees - wrong landmarks for this movement'
    )


@pytest.mark.parametrize("exercise", EXERCISES, ids=lambda e: e["slug"])
def test_configured_band_lies_inside_the_reachable_range(exercise):
    """The clinical target must be physically attainable, not just plausible.

    `terminal-knee-ext` shipped with rep_high=174 while world-landmark depth
    capped a straight knee at ~165, so the state machine could never re-enter
    the high state and every session scored zero. Measuring in the image plane
    restored the full 0-180 span; this guards the band against drifting back
    out of reach.
    """
    pose = exercise["pose"]
    assert 0 <= pose["rep_low"] < pose["rep_high"] <= 180, exercise["slug"]

    if pose.get("mode") == "hold":
        # A hold targets one position, and for a max-extension hold the upper
        # edge is legitimately 180 -- nothing exists above it. What has to be
        # attainable is the edge you enter through.
        assert pose["rep_low"] <= 175, exercise["slug"]
    else:
        # A rep must cross BOTH thresholds, so the top one needs headroom: a
        # band butting against 180 demands a perfectly straight limb held
        # perfectly side-on to the camera.
        assert pose["rep_high"] <= 178, exercise["slug"]
