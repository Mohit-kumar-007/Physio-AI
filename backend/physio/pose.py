"""Biomechanical analysis of a pose-keypoint timeline.

The browser runs MediaPipe and streams us landmarks (numbers, never video).
Everything clinical -- joint angles, rep counting, range of motion, form
scoring -- is computed here so it is testable and swappable without touching
the client.

Frame format (what the client POSTs):
    {"t": <ms since session start>, "lm": [[x, y, z, visibility], ...33]}
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

# --- tuning knobs -----------------------------------------------------------
# Starting values. A physiotherapist should validate these against real
# patients; every one of them is meant to be adjusted, not treated as truth.
SMOOTHING_WINDOW = 5          # frames of moving average on each angle series
MIN_VISIBILITY = 0.5          # landmark below this is treated as unreliable
VIOLATION_TOLERANCE = 0.15    # flag a form rule only if >15% of frames breach it
# Consecutive frames the angle must stay past a threshold before the rep state
# flips. 2 kills the single-frame spikes MediaPipe produces while still
# catching a fast rep, which only spends ~2 frames at the top at 30fps.
# ponytail: a sustained 2-frame glitch would still slip through; raise this if
# you move to a higher frame rate, where real reps have more frames to spare.
MIN_DWELL_FRAMES = 2
MIN_TRACKED_RATIO = 0.6       # below this we refuse to score the session
ROM_LOW_PCT, ROM_HIGH_PCT = 5, 95   # robust percentiles instead of min/max

# --- adaptive rep thresholds ------------------------------------------------
# Fixed anatomical cutoffs assume a textbook body. A stiff shoulder, an
# arthritic knee, or a chin tuck (which only travels ~15 degrees in total)
# never reaches them, and the patient sees a rep counter stuck on zero with no
# explanation. So the thresholds are placed inside the range the patient
# actually demonstrated. The clinical band from the config is still reported
# against, as the target they are working towards.
MIN_MOVEMENT_RANGE = 10.0     # degrees of travel before a movement is real
REP_LOW_FRACTION = 0.30       # bottom of the rep, as a fraction of the range
REP_HIGH_FRACTION = 0.70      # top of the rep -- 40% dead band between them

# quality penalty weights
PENALTY_PER_FORM_ERROR = 12
PENALTY_MAX_FORM = 45
PENALTY_MAX_TRACKING = 25
PENALTY_MAX_TEMPO = 15
IDEAL_REP_SECONDS = (1.5, 6.0)   # outside this band the tempo costs points


@dataclass
class FormError:
    rule_id: str
    message_en: str
    message_hi: str
    frames: int
    rate: float          # fraction of tracked frames in violation


@dataclass
class SessionAnalysis:
    reps: int
    rom_degrees: float
    quality: int                       # 0-100
    duration_seconds: float
    tracked_ratio: float
    peak_angle: float
    min_angle: float
    mean_tempo_seconds: float
    errors: list[FormError] = field(default_factory=list)
    angle_series: list[float] = field(default_factory=list)
    # How the reps were counted, and how the patient did against the clinical
    # target. Reported so a small range is visible rather than silently
    # rescaled away.
    adaptive: bool = False
    target_rom: float = 0.0
    target_met: bool = False

    def error_messages(self, lang: str = "en") -> list[str]:
        key = "message_hi" if lang == "hi" else "message_en"
        return [getattr(e, key) for e in self.errors]


def joint_angle(a, b, c) -> float:
    """Angle ABC in degrees, with B as the vertex, measured IN THE IMAGE PLANE.

    The z component is deliberately dropped. MediaPipe's depth is a monocular
    guess, and measured against real detections it compresses extension by
    10-15 degrees: a fully straight knee reads 165 in 3D but 180 in 2D, and
    two equally straight legs disagree by 6 degrees in 3D versus 3 in 2D.
    Since each exercise already tells the patient which way to face, the
    movement happens in the image plane anyway, where 2D is both accurate and
    far less noisy.

    Use axis_angle() for rotation, which is the one thing 2D genuinely cannot
    see and which does need the depth channel.

    Returns NaN when a segment has zero length (landmarks collapsed onto each
    other), which the caller filters out rather than propagating.
    """
    a = np.asarray(a, float)[:2]
    b = np.asarray(b, float)[:2]
    c = np.asarray(c, float)[:2]
    ba, bc = a - b, c - b
    denom = np.linalg.norm(ba) * np.linalg.norm(bc)
    if denom == 0:
        return float("nan")
    cosine = float(np.dot(ba, bc) / denom)
    return float(np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0))))


def _to_array(frames: list[dict]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (coords[F,33,3], visibility[F,33], times[F] in seconds)."""
    if not frames:
        return np.zeros((0, 33, 3)), np.zeros((0, 33)), np.zeros(0)
    coords = np.array([[p[:3] for p in f["lm"]] for f in frames], dtype=float)
    vis = np.array(
        [[p[3] if len(p) > 3 else 1.0 for p in f["lm"]] for f in frames], dtype=float
    )
    times = np.array([f.get("t", i * 33) for i, f in enumerate(frames)], float) / 1000.0
    return coords, vis, times


def axis_angle(p1, p2, q1, q2) -> float:
    """Angle in degrees between the line p1->p2 and the line q1->q2.

    Needed for rotation, which no three-point joint angle can express: turning
    your head is rigid about the neck axis, so nothing bends. What changes is
    the ear line swinging away from the shoulder line, and that is this.
    """
    u = np.asarray(p2, float) - np.asarray(p1, float)
    v = np.asarray(q2, float) - np.asarray(q1, float)
    denom = np.linalg.norm(u) * np.linalg.norm(v)
    if denom == 0:
        return float("nan")
    cosine = float(np.dot(u, v) / denom)
    # Undirected: a 170 degree separation is a 10 degree turn the other way.
    return float(min(np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0))),
                     180 - np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0)))))


def _angle_series(coords: np.ndarray, vis: np.ndarray, triplet: list[int]) -> np.ndarray:
    """Per-frame joint angle; NaN wherever a required landmark is unreliable."""
    a, b, c = triplet
    out = np.full(len(coords), np.nan)
    for i in range(len(coords)):
        if min(vis[i, a], vis[i, b], vis[i, c]) < MIN_VISIBILITY:
            continue
        out[i] = joint_angle(coords[i, a], coords[i, b], coords[i, c])
    return out


def _axis_series(coords: np.ndarray, vis: np.ndarray,
                 axis_a: list[int], axis_b: list[int]) -> np.ndarray:
    p1, p2 = axis_a
    q1, q2 = axis_b
    out = np.full(len(coords), np.nan)
    for i in range(len(coords)):
        if min(vis[i, p1], vis[i, p2], vis[i, q1], vis[i, q2]) < MIN_VISIBILITY:
            continue
        out[i] = axis_angle(coords[i, p1], coords[i, p2],
                            coords[i, q1], coords[i, q2])
    return out


def _excursion(series: np.ndarray) -> float:
    """How much this angle actually moved, ignoring outliers. NaN-safe."""
    valid = series[~np.isnan(series)]
    if len(valid) < 2:
        return 0.0
    return float(np.percentile(valid, ROM_HIGH_PCT) -
                 np.percentile(valid, ROM_LOW_PCT))


def measure(coords: np.ndarray, vis: np.ndarray, spec: dict) -> np.ndarray:
    """Resolve a config's angle spec into one per-frame series.

    For a bilateral exercise both sides are measured and the one the patient
    actually used is returned. Picking by movement rather than by visibility
    is what fixes right-limb reps going uncounted: a still left leg is
    perfectly visible, it just is not the leg being exercised.
    """
    if spec.get("angle_type") == "axis":
        return _axis_series(coords, vis, spec["axis_a"], spec["axis_b"])

    left = _angle_series(coords, vis, spec["primary_angle"])
    mirror = spec.get("primary_angle_mirror")
    if not mirror:
        return left

    right = _angle_series(coords, vis, mirror)

    left_seen = float((~np.isnan(left)).mean())
    right_seen = float((~np.isnan(right)).mean())

    # If one side is barely visible at all, the choice is already made.
    if left_seen < MIN_TRACKED_RATIO <= right_seen:
        return right
    if right_seen < MIN_TRACKED_RATIO <= left_seen:
        return left

    # Both visible: follow whichever one moved.
    return right if _excursion(right) > _excursion(left) else left


def _rule_series(coords: np.ndarray, vis: np.ndarray, rule: dict) -> np.ndarray:
    """A form rule measured on whichever side has more usable frames."""
    left = _angle_series(coords, vis, rule["angle"])
    mirror = rule.get("mirror")
    if not mirror:
        return left
    right = _angle_series(coords, vis, mirror)
    # For form rules, coverage is the right tiebreak: we want to judge the
    # limb we can actually see, not the one that moved most.
    return right if (~np.isnan(right)).sum() > (~np.isnan(left)).sum() else left


def _smooth(series: np.ndarray, window: int = SMOOTHING_WINDOW) -> np.ndarray:
    """Moving average that ignores NaN gaps instead of spreading them."""
    if len(series) < window or window < 2:
        return series
    out = series.copy()
    half = window // 2
    for i in range(len(series)):
        chunk = series[max(0, i - half): i + half + 1]
        valid = chunk[~np.isnan(chunk)]
        if len(valid):
            out[i] = valid.mean()
    return out


def _count_reps(series: np.ndarray, low: float, high: float) -> tuple[int, list[int]]:
    """Hysteresis state machine: a rep completes on high -> low -> high.

    Runs on the UNSMOOTHED angle series on purpose. A moving average shaves
    turning points, and turning points are exactly where the thresholds get
    crossed -- smoothing first makes fast reps vanish. Noise is rejected by
    two mechanisms that do not distort the peaks: the wide dead band between
    `low` and `high`, and a dwell requirement so the signal must stay past a
    threshold for MIN_DWELL_FRAMES in a row before the state flips.
    """
    reps, boundaries = 0, []
    state = "high"          # assume the patient starts at rest
    low_run = high_run = 0
    for i, v in enumerate(series):
        if np.isnan(v):
            low_run = high_run = 0      # a gap proves nothing either way
            continue
        if v <= low:
            low_run, high_run = low_run + 1, 0
        elif v >= high:
            high_run, low_run = high_run + 1, 0
        else:
            low_run = high_run = 0      # in the dead band

        if state == "high" and low_run >= MIN_DWELL_FRAMES:
            state = "low"
        elif state == "low" and high_run >= MIN_DWELL_FRAMES:
            state = "high"
            reps += 1
            boundaries.append(i)
    return reps, boundaries


def _count_holds(series: np.ndarray, times: np.ndarray, low: float, high: float,
                 hold_seconds: float) -> tuple[int, list[int]]:
    """Isometric exercises: one rep per sustained period inside the target band.

    After a hold completes the counter is LOCKED until the patient leaves the
    band. Without that, someone simply resting inside the band -- sitting with
    a straight knee, say -- scores a rep every `hold_seconds` forever, which
    is the difference between counting effort and counting the clock.
    """
    reps, boundaries = 0, []
    start = None
    armed = True
    for i, v in enumerate(series):
        inside = (not np.isnan(v)) and low <= v <= high

        if not inside:
            start = None
            armed = True            # released: the next hold may count
            continue
        if not armed:
            continue
        if start is None:
            start = i
        if times[i] - times[start] >= hold_seconds:
            reps += 1
            boundaries.append(i)
            start = None
            armed = False           # must relax out of the band first
    return reps, boundaries


def analyze_session(frames: list[dict], config: dict) -> SessionAnalysis:
    """Turn a raw keypoint timeline into clinical numbers.

    `config` is one entry from exercise_data.POSE_CONFIGS.
    """
    coords, vis, times = _to_array(frames)
    if len(coords) == 0:
        return SessionAnalysis(0, 0.0, 0, 0.0, 0.0, 0.0, 0.0, 0.0)

    duration = float(times[-1] - times[0]) if len(times) > 1 else 0.0
    raw = measure(coords, vis, config)
    series = _smooth(raw)

    # Measured on the RAW series. _smooth() interpolates across gaps, so asking
    # the smoothed signal how many frames were tracked always answers "all of
    # them" -- which would let a session the camera barely saw score as clean.
    tracked = ~np.isnan(raw)
    tracked_ratio = float(tracked.sum() / len(raw))

    # Not enough of the body was visible to say anything honest about form.
    if tracked_ratio < MIN_TRACKED_RATIO:
        return SessionAnalysis(
            reps=0, rom_degrees=0.0, quality=0, duration_seconds=duration,
            tracked_ratio=round(tracked_ratio, 3), peak_angle=0.0, min_angle=0.0,
            mean_tempo_seconds=0.0,
            errors=[FormError(
                "poor_tracking",
                "Camera could not see you clearly - step back and improve lighting",
                "कैमरा आपको ठीक से नहीं देख पाया - थोड़ा पीछे हटें और रोशनी बढ़ाएँ",
                int((~tracked).sum()), round(1.0 - tracked_ratio, 3),
            )],
            angle_series=[],
        )

    valid = series[~np.isnan(series)]
    rom = float(np.percentile(valid, ROM_HIGH_PCT) - np.percentile(valid, ROM_LOW_PCT))
    target_rom = float(config["rep_high"] - config["rep_low"])

    adaptive = False
    if config.get("mode") == "hold":
        # A hold is about reaching an absolute clinical position, so the
        # configured band is the right yardstick. Smoothing costs nothing over
        # a multi-second hold and stops a wobble breaking a good contraction.
        reps, _ = _count_holds(series, times, config["rep_low"], config["rep_high"],
                               config.get("hold_seconds", 3.0))
    else:
        window = _adaptive_thresholds(valid)
        adaptive = window is not None
        low, high = window if adaptive else (config["rep_low"], config["rep_high"])
        reps, _ = _count_reps(raw, low, high)

    tempo = (duration / reps) if reps else 0.0

    errors = _evaluate_form_rules(coords, vis, config.get("form_rules", []), tracked)

    # A zero should never be unexplained. If the joint barely moved, say that
    # outright instead of returning a silent 0 reps.
    if reps == 0 and rom < MIN_MOVEMENT_RANGE:
        errors.insert(0, FormError(
            "no_movement",
            "Almost no movement was detected at the tracked joint. Check you "
            "are facing the way the exercise asks and that the limb is in frame.",
            "ट्रैक किए गए जोड़ में लगभग कोई गति नहीं मिली। जाँचें कि आप सही दिशा में "
            "हैं और वह अंग कैमरे में दिख रहा है।",
            len(valid), 1.0,
        ))

    quality = _score_quality(errors, tracked_ratio, tempo, reps)

    return SessionAnalysis(
        reps=reps,
        rom_degrees=round(rom, 1),
        quality=quality,
        duration_seconds=round(duration, 1),
        tracked_ratio=round(tracked_ratio, 3),
        peak_angle=round(float(valid.max()), 1),
        min_angle=round(float(valid.min()), 1),
        mean_tempo_seconds=round(tempo, 2),
        errors=errors,
        angle_series=[round(float(v), 1) for v in valid][:600],
        adaptive=adaptive,
        target_rom=round(target_rom, 1),
        target_met=rom >= target_rom,
    )


def _adaptive_thresholds(valid: np.ndarray) -> tuple[float, float] | None:
    """Place the rep thresholds inside the range the patient actually moved.

    Returns None when there was not enough travel to call it a movement, in
    which case the caller falls back to the configured clinical band.
    """
    if len(valid) < 2:
        return None
    low_obs = float(np.percentile(valid, ROM_LOW_PCT))
    high_obs = float(np.percentile(valid, ROM_HIGH_PCT))
    span = high_obs - low_obs
    if span < MIN_MOVEMENT_RANGE:
        return None
    return low_obs + REP_LOW_FRACTION * span, low_obs + REP_HIGH_FRACTION * span


def _evaluate_form_rules(coords, vis, rules, tracked) -> list[FormError]:
    errors = []
    total = max(int(tracked.sum()), 1)
    for rule in rules:
        angles = _smooth(_rule_series(coords, vis, rule))
        checkable = ~np.isnan(angles)
        if not checkable.any():
            continue
        lo = rule.get("min", -np.inf)
        hi = rule.get("max", np.inf)
        breached = checkable & ((angles < lo) | (angles > hi))
        count = int(breached.sum())
        rate = count / total
        if rate > VIOLATION_TOLERANCE:
            errors.append(FormError(
                rule_id=rule["id"],
                message_en=rule["msg_en"],
                message_hi=rule["msg_hi"],
                frames=count,
                rate=round(rate, 3),
            ))
    return errors


def _score_quality(errors, tracked_ratio, tempo, reps) -> int:
    """100 minus penalties for bad form, lost tracking, and rushed tempo."""
    form_penalty = min(len(errors) * PENALTY_PER_FORM_ERROR, PENALTY_MAX_FORM)
    tracking_penalty = min((1.0 - tracked_ratio) * 100, PENALTY_MAX_TRACKING)

    tempo_penalty = 0.0
    if reps and tempo:
        fast, slow = IDEAL_REP_SECONDS
        if tempo < fast:
            tempo_penalty = min((fast - tempo) / fast * PENALTY_MAX_TEMPO,
                                PENALTY_MAX_TEMPO)
        elif tempo > slow:
            tempo_penalty = min((tempo - slow) / slow * PENALTY_MAX_TEMPO,
                                PENALTY_MAX_TEMPO)

    return int(max(0, round(100 - form_penalty - tracking_penalty - tempo_penalty)))
