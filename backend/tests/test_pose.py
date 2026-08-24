"""Checks for the biomechanics engine.

Synthetic keypoint timelines are generated so rep counting, ROM and form
scoring can be verified against a known answer -- something you cannot do by
waving at a webcam.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from backend.physio import landmarks as L
from backend.physio.exercise_data import BY_SLUG, EXERCISES, POSE_CONFIGS
from backend.physio.pose import analyze_session, joint_angle


# --- angle math -------------------------------------------------------------
def test_right_angle():
    assert joint_angle([0, 1, 0], [0, 0, 0], [1, 0, 0]) == pytest.approx(90.0)


def test_straight_line_is_180():
    assert joint_angle([-1, 0, 0], [0, 0, 0], [1, 0, 0]) == pytest.approx(180.0)


def test_collapsed_landmarks_give_nan_not_crash():
    assert math.isnan(joint_angle([0, 0, 0], [0, 0, 0], [1, 0, 0]))


def test_angle_is_orientation_independent():
    """Rotating the whole body must not change a joint angle."""
    a, b, c = [0, 1, 0], [0, 0, 0], [1, 0, 0]
    theta = math.radians(37)
    rot = lambda p: [                                            # noqa: E731
        p[0] * math.cos(theta) - p[1] * math.sin(theta),
        p[0] * math.sin(theta) + p[1] * math.cos(theta),
        p[2],
    ]
    assert joint_angle(rot(a), rot(b), rot(c)) == pytest.approx(
        joint_angle(a, b, c), abs=1e-6
    )


# --- synthetic frame builder ------------------------------------------------
def make_frame(knee_angle_deg: float, t: float, visibility: float = 1.0) -> dict:
    """A body where the left hip-knee-ankle angle is exactly what we ask for."""
    lm = [[0.0, 0.0, 0.0, visibility] for _ in range(33)]
    rad = math.radians(knee_angle_deg)

    lm[L.L_KNEE] = [0.0, 0.0, 0.0, visibility]
    lm[L.L_HIP] = [0.0, 1.0, 0.0, visibility]
    lm[L.L_ANKLE] = [math.sin(rad), math.cos(rad), 0.0, visibility]

    # Keep the rest of the skeleton plausible and out of the way.
    lm[L.L_SHOULDER] = [0.0, 2.0, 0.0, visibility]
    lm[L.L_EAR] = [0.0, 2.5, 0.0, visibility]
    lm[L.L_ELBOW] = [0.5, 1.5, 0.0, visibility]
    lm[L.L_WRIST] = [0.8, 1.0, 0.0, visibility]
    return {"t": t, "lm": lm}


def sweep(angles: list[float], fps: int = 30) -> list[dict]:
    step = 1000 / fps
    return [make_frame(a, i * step) for i, a in enumerate(angles)]


def rep_cycle(high: float, low: float, frames_per_phase: int = 15) -> list[float]:
    """One down-and-up movement as a smooth angle ramp."""
    down = list(np.linspace(high, low, frames_per_phase))
    up = list(np.linspace(low, high, frames_per_phase))
    return down + up


KNEE_CONFIG = {
    "primary_angle": [L.L_HIP, L.L_KNEE, L.L_ANKLE],
    "mode": "range",
    "rep_low": 150,
    "rep_high": 175,
    "form_rules": [],
}


# --- rep counting -----------------------------------------------------------
def test_counts_exact_number_of_reps():
    angles = [178.0] * 10
    for _ in range(5):
        angles += rep_cycle(178, 140)
    result = analyze_session(sweep(angles), KNEE_CONFIG)
    assert result.reps == 5


def test_partial_rep_does_not_count():
    """Coming down but never returning to the top is not a completed rep."""
    angles = [178.0] * 10 + list(np.linspace(178, 140, 15))
    assert analyze_session(sweep(angles), KNEE_CONFIG).reps == 0


def test_jitter_around_threshold_does_not_inflate_count():
    """Noise sitting on the boundary must not ratchet the counter."""
    angles = [178.0] * 5
    for _ in range(40):
        angles += [174.0, 176.0]        # oscillating across rep_high only
    assert analyze_session(sweep(angles), KNEE_CONFIG).reps == 0


def test_single_frame_glitch_does_not_create_a_rep():
    """MediaPipe occasionally throws one wild frame. It must not count as a rep."""
    angles = [178.0] * 30
    angles[10] = 100.0            # one impossible jump to the bottom and back
    assert analyze_session(sweep(angles), KNEE_CONFIG).reps == 0


def test_dropout_at_the_turning_point_does_not_split_a_rep():
    """Losing the frames at the bottom must not turn one rep into two."""
    angles = [178.0] * 5 + rep_cycle(178, 140, frames_per_phase=20)
    frames = sweep(angles)
    for i in range(23, 27):       # blank out the bottom of the movement
        frames[i] = make_frame(140, frames[i]["t"], visibility=0.1)
    assert analyze_session(frames, KNEE_CONFIG).reps <= 1


def test_hold_mode_counts_sustained_contractions():
    config = {**KNEE_CONFIG, "mode": "hold", "rep_low": 168,
              "rep_high": 180, "hold_seconds": 2.0}
    angles = []
    for _ in range(3):
        angles += [175.0] * 90       # 3s inside the band at 30fps
        angles += [120.0] * 30       # release
    assert analyze_session(sweep(angles), config).reps == 3


# --- range of motion --------------------------------------------------------
def test_rom_reflects_movement_range():
    angles = [178.0] * 5 + rep_cycle(178, 120) * 3
    result = analyze_session(sweep(angles), KNEE_CONFIG)
    # Robust percentiles trim the extremes, so expect close to but under 58.
    assert 40 < result.rom_degrees <= 58


def test_no_movement_gives_near_zero_rom():
    result = analyze_session(sweep([175.0] * 60), KNEE_CONFIG)
    assert result.rom_degrees < 1.0


# --- form scoring -----------------------------------------------------------
def test_clean_session_scores_high():
    angles = []
    for _ in range(6):
        angles += rep_cycle(178, 140, frames_per_phase=30)   # 2s per rep
    result = analyze_session(sweep(angles), KNEE_CONFIG)
    assert result.quality >= 85


def test_form_violation_lowers_quality_and_is_reported():
    config = {
        **KNEE_CONFIG,
        "form_rules": [{
            "id": "knees_straight",
            "angle": [L.L_HIP, L.L_KNEE, L.L_ANKLE],
            "min": 160,
            "msg_en": "Keep your knee straight",
            "msg_hi": "घुटना सीधा रखें",
        }],
    }
    angles = []
    for _ in range(6):
        angles += rep_cycle(178, 110, frames_per_phase=30)   # deep = breaks rule
    result = analyze_session(sweep(angles), config)
    assert any(e.rule_id == "knees_straight" for e in result.errors)
    assert result.quality < 95


def test_rushed_tempo_costs_quality():
    fast, slow = [], []
    for _ in range(6):
        fast += rep_cycle(178, 140, frames_per_phase=8)     # ~0.5s per rep
        slow += rep_cycle(178, 140, frames_per_phase=30)    # ~2s per rep
    fast_result = analyze_session(sweep(fast), KNEE_CONFIG)
    slow_result = analyze_session(sweep(slow), KNEE_CONFIG)
    assert fast_result.quality < slow_result.quality


# --- degraded input ---------------------------------------------------------
def test_untrackable_session_refuses_to_score():
    """Low visibility must produce an honest zero, not an invented number."""
    frames = [make_frame(170, i * 33, visibility=0.1) for i in range(60)]
    result = analyze_session(frames, KNEE_CONFIG)
    assert result.quality == 0
    assert result.reps == 0
    assert result.errors[0].rule_id == "poor_tracking"


def test_empty_input_does_not_crash():
    result = analyze_session([], KNEE_CONFIG)
    assert result.reps == 0 and result.quality == 0


def test_intermittent_dropout_still_scores():
    """Losing a few frames mid-session should degrade, not abort."""
    angles = []
    for _ in range(6):
        angles += rep_cycle(178, 140, frames_per_phase=30)
    frames = sweep(angles)
    for i in range(0, len(frames), 12):        # drop ~8% of frames
        frames[i] = make_frame(170, frames[i]["t"], visibility=0.1)
    result = analyze_session(frames, KNEE_CONFIG)
    assert result.reps == 6
    assert 0 < result.tracked_ratio < 1.0


# --- image-plane measurement ------------------------------------------------
def test_angle_ignores_the_depth_channel():
    """z is a monocular guess that squashes extension; it must not be used."""
    flat = joint_angle([0, 1, 0], [0, 0, 0], [1, 0, 0])
    with_depth = joint_angle([0, 1, 5], [0, 0, -3], [1, 0, 9])
    assert flat == pytest.approx(with_depth)


def test_straight_limb_reads_straight_regardless_of_depth_noise():
    """The bug that stalled every rep counter: a straight limb must read ~180.

    With z included, MediaPipe's depth estimate dragged a straight knee down
    to ~165, so a 174-degree target could never be reached.
    """
    # Collinear in x/y, wildly inconsistent in z, as real detections are.
    assert joint_angle([0, 0, 0.4], [1, 0, -0.9], [2, 0, 0.7]) == pytest.approx(180.0)


# --- adaptive thresholds ----------------------------------------------------
def test_small_range_movement_still_counts_reps():
    """A chin tuck travels ~15 degrees total; fixed clinical bands miss it."""
    config = {**KNEE_CONFIG, "rep_low": 155, "rep_high": 171}
    angles = [150.0] * 10
    for _ in range(6):
        angles += rep_cycle(150, 136, frames_per_phase=25)   # never enters band
    result = analyze_session(sweep(angles), config)
    assert result.reps == 6
    assert result.adaptive is True


def test_stiff_patient_who_cannot_reach_the_target_still_gets_counted():
    """Range 150-170 instead of the configured 155-174. Must not score zero."""
    config = {**KNEE_CONFIG, "rep_low": 155, "rep_high": 174}
    angles = [170.0] * 10
    for _ in range(5):
        angles += rep_cycle(170, 150, frames_per_phase=25)
    result = analyze_session(sweep(angles), config)
    assert result.reps == 5
    assert result.target_met is False        # honest: they missed the target


def test_full_range_patient_meets_the_target():
    config = {**KNEE_CONFIG, "rep_low": 140, "rep_high": 175}
    angles = [178.0] * 10
    for _ in range(5):
        angles += rep_cycle(178, 130, frames_per_phase=25)
    result = analyze_session(sweep(angles), config)
    assert result.reps == 5
    assert result.target_met is True


def test_no_movement_is_reported_not_silently_zero():
    """The complaint was a counter stuck on zero with no explanation."""
    result = analyze_session(sweep([172.0] * 200), KNEE_CONFIG)
    assert result.reps == 0
    assert any(e.rule_id == "no_movement" for e in result.errors)
    assert result.error_messages("hi")       # explained in both languages


def test_adaptive_does_not_invent_reps_from_noise():
    """Jitter of a few degrees must not be rescaled into a full rep."""
    angles = []
    for i in range(300):
        angles.append(172.0 + (2.0 if i % 2 else -2.0))     # 4 degree wobble
    result = analyze_session(sweep(angles), KNEE_CONFIG)
    assert result.reps == 0
    assert result.adaptive is False


def test_holds_keep_absolute_thresholds():
    """A hold targets a real clinical position, so it must not self-calibrate."""
    config = {**KNEE_CONFIG, "mode": "hold", "rep_low": 170,
              "rep_high": 180, "hold_seconds": 3.0}
    # Patient holds at 140 -- well outside the band. Adaptive scaling would
    # wrongly accept it; absolute thresholds correctly score nothing.
    angles = []
    for _ in range(3):
        angles += [140.0] * 120 + [100.0] * 30
    result = analyze_session(sweep(angles), config)
    assert result.reps == 0
    assert result.adaptive is False


# --- bilateral tracking -----------------------------------------------------
def make_right_frame(knee_angle_deg: float, t: float, visibility: float = 1.0) -> dict:
    """Mirror of make_frame: the RIGHT knee moves, the left stays straight."""
    lm = [[0.0, 0.0, 0.0, visibility] for _ in range(33)]
    rad = math.radians(knee_angle_deg)

    lm[L.R_KNEE] = [0.0, 0.0, 0.0, visibility]
    lm[L.R_HIP] = [0.0, 1.0, 0.0, visibility]
    lm[L.R_ANKLE] = [math.sin(rad), math.cos(rad), 0.0, visibility]

    # Left leg present and perfectly visible, but locked straight and still.
    lm[L.L_KNEE] = [1.0, 0.0, 0.0, visibility]
    lm[L.L_HIP] = [1.0, 1.0, 0.0, visibility]
    lm[L.L_ANKLE] = [1.0, -1.0, 0.0, visibility]

    lm[L.R_SHOULDER] = [0.0, 2.0, 0.0, visibility]
    lm[L.L_SHOULDER] = [1.0, 2.0, 0.0, visibility]
    return {"t": t, "lm": lm}


BILATERAL_CONFIG = {
    **KNEE_CONFIG,
    "primary_angle_mirror": [L.R_HIP, L.R_KNEE, L.R_ANKLE],
}


def test_right_side_reps_are_counted():
    """The bug that made most exercises look broken: right limb ignored."""
    angles = [178.0] * 10
    for _ in range(5):
        angles += rep_cycle(178, 140)
    step = 1000 / 30
    frames = [make_right_frame(a, i * step) for i, a in enumerate(angles)]
    assert analyze_session(frames, BILATERAL_CONFIG).reps == 5


def test_left_side_still_counted_with_mirror_configured():
    angles = [178.0] * 10
    for _ in range(4):
        angles += rep_cycle(178, 140)
    assert analyze_session(sweep(angles), BILATERAL_CONFIG).reps == 4


def test_still_visible_limb_does_not_win_over_the_moving_one():
    """Side choice is by movement, not visibility - both legs are visible here."""
    angles = [178.0] * 10 + rep_cycle(178, 140) * 3
    step = 1000 / 30
    frames = [make_right_frame(a, i * step) for i, a in enumerate(angles)]
    result = analyze_session(frames, BILATERAL_CONFIG)
    assert result.reps == 3
    assert result.rom_degrees > 20      # the still left leg would give ~0


# --- axis angles (rotation) -------------------------------------------------
def test_axis_angle_measures_rotation():
    from backend.physio.pose import axis_angle

    # Shoulder line along x; ear line turned 30 degrees away from it.
    rad = math.radians(30)
    assert axis_angle([0, 0, 0], [1, 0, 0],
                      [0, 0, 0], [math.cos(rad), 0, math.sin(rad)]
                      ) == pytest.approx(30.0, abs=0.5)


def test_axis_angle_is_undirected():
    """Turning left and turning right are the same magnitude of rotation."""
    from backend.physio.pose import axis_angle

    left = axis_angle([0, 0, 0], [1, 0, 0], [0, 0, 0], [0.87, 0, 0.5])
    right = axis_angle([0, 0, 0], [1, 0, 0], [0, 0, 0], [0.87, 0, -0.5])
    assert left == pytest.approx(right, abs=0.5)


def test_neck_rotation_counts_head_turns():
    """Rotation is rigid, so a joint triplet cannot see it - the axis can."""
    config = {
        "angle_type": "axis",
        "axis_a": [L.L_EAR, L.R_EAR],
        "axis_b": [L.L_SHOULDER, L.R_SHOULDER],
        "mode": "range", "rep_low": 12, "rep_high": 40,
        "form_rules": [],
    }
    frames, t = [], 0.0
    def push(turn_deg):
        nonlocal t
        lm = [[0.0, 0.0, 0.0, 1.0] for _ in range(33)]
        lm[L.L_SHOULDER] = [-1.0, 0.0, 0.0, 1.0]
        lm[L.R_SHOULDER] = [1.0, 0.0, 0.0, 1.0]
        rad = math.radians(turn_deg)
        lm[L.L_EAR] = [-0.5 * math.cos(rad), 1.5, -0.5 * math.sin(rad), 1.0]
        lm[L.R_EAR] = [0.5 * math.cos(rad), 1.5, 0.5 * math.sin(rad), 1.0]
        frames.append({"t": t, "lm": lm}); t += 33.3

    for _ in range(6):
        push(0)
    for _ in range(4):                      # four head turns and returns
        for step in range(12):
            push(55 * step / 11)
        for step in range(12):
            push(55 - 55 * step / 11)
    assert analyze_session(frames, config).reps == 4


# --- isometric holds --------------------------------------------------------
def test_resting_inside_the_band_does_not_farm_reps():
    """Sitting still with a straight knee must not score a rep every few seconds."""
    config = {**KNEE_CONFIG, "mode": "hold", "rep_low": 170,
              "rep_high": 180, "hold_seconds": 3.0}
    # 30 seconds of not moving = at most one hold, never ten.
    assert analyze_session(sweep([175.0] * 900), config).reps <= 1


def test_holds_count_when_the_patient_relaxes_between_them():
    config = {**KNEE_CONFIG, "mode": "hold", "rep_low": 170,
              "rep_high": 180, "hold_seconds": 3.0}
    angles = []
    for _ in range(3):
        angles += [175.0] * 120      # 4s contraction
        angles += [140.0] * 45       # relax out of the band
    assert analyze_session(sweep(angles), config).reps == 3


# --- catalogue integrity ----------------------------------------------------
def test_every_exercise_has_a_usable_pose_config():
    for ex in EXERCISES:
        pose = ex["pose"]
        assert len(pose["primary_angle"]) == 3, ex["slug"]
        assert all(0 <= i < 33 for i in pose["primary_angle"]), ex["slug"]
        assert pose["rep_low"] < pose["rep_high"], ex["slug"]
        for rule in pose.get("form_rules", []):
            assert len(rule["angle"]) == 3, ex["slug"]
            assert rule["msg_en"] and rule["msg_hi"], ex["slug"]


def test_bilateral_coverage():
    """Anything worked one limb at a time needs a mirror, or half the
    patients get zero reps."""
    central = {"neck-rotation"}          # measured across the body, not per side
    for ex in EXERCISES:
        if ex["slug"] in central:
            continue
        assert ex["pose"].get("primary_angle_mirror"), ex["slug"]
        left, right = ex["pose"]["primary_angle"], ex["pose"]["primary_angle_mirror"]
        assert left != right, ex["slug"]


def test_mirror_triplets_are_the_anatomical_opposites():
    """A copy-paste slip here silently measures the wrong joint."""
    opposite = {
        L.L_EAR: L.R_EAR, L.L_SHOULDER: L.R_SHOULDER, L.L_ELBOW: L.R_ELBOW,
        L.L_WRIST: L.R_WRIST, L.L_HIP: L.R_HIP, L.L_KNEE: L.R_KNEE,
        L.L_ANKLE: L.R_ANKLE,
    }
    for ex in EXERCISES:
        mirror = ex["pose"].get("primary_angle_mirror")
        if not mirror:
            continue
        expected = [opposite[i] for i in ex["pose"]["primary_angle"]]
        assert mirror == expected, ex["slug"]


def test_thresholds_sit_inside_the_measurable_range():
    """An unsigned joint angle can only be 0-180; a band outside never fires."""
    for ex in EXERCISES:
        pose = ex["pose"]
        assert 0 <= pose["rep_low"] < pose["rep_high"] <= 180, ex["slug"]
        # A band narrower than the dwell requirement can survive is unusable.
        assert pose["rep_high"] - pose["rep_low"] >= 10, ex["slug"]


def test_every_exercise_has_preview_and_teaching_content():
    required_pose_keys = {"root", "torso", "head", "arm", "forearm", "thigh", "shin"}
    for ex in EXERCISES:
        assert ex["camera_view"] in ("front", "side"), ex["slug"]
        assert len(ex["steps"]) >= 3, ex["slug"]
        assert len(ex["steps"]) == len(ex["steps_hi"]), ex["slug"]
        assert len(ex["mistakes"]) == len(ex["mistakes_hi"]), ex["slug"]
        for phase in ("start", "end"):
            frame = ex["preview"][phase]
            assert required_pose_keys <= set(frame), f'{ex["slug"]}/{phase}'
            assert len(frame["root"]) == 2, ex["slug"]


def test_preview_keyframes_actually_differ():
    """A preview whose two poses match animates nothing."""
    for ex in EXERCISES:
        start, end = ex["preview"]["start"], ex["preview"]["end"]
        assert start != end, ex["slug"]


def test_slugs_are_unique_and_original_ones_survive():
    slugs = [e["slug"] for e in EXERCISES]
    assert len(slugs) == len(set(slugs))
    # Existing plans and history reference these; renaming one breaks them.
    for slug in ["lumbar-extension", "cat-cow", "bird-dog", "quad-sets",
                 "straight-leg-raise", "terminal-knee-ext", "pendulum",
                 "wall-slides", "chin-tuck", "neck-rotation", "posture-row",
                 "thoracic-ext"]:
        assert slug in BY_SLUG
        assert slug in POSE_CONFIGS
