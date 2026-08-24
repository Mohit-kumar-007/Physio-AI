"""Stick-figure keyframes for the exercise preview animation.

Each exercise ships two poses; the browser interpolates between them to show
the movement before the patient starts. Poses are expressed as segment
DIRECTIONS rather than point coordinates, so the renderer can do forward
kinematics from the hip and a pose is only a handful of numbers.

Angle convention: degrees clockwise from straight up.
    0 = up      90 = right      180 = down      270 = left

Side-view figures face RIGHT. `*_far` fields drive the limb on the far side of
the body; when omitted the renderer mirrors the near limb, which is what you
want for a side view where the limbs overlap.
"""

from __future__ import annotations

# Base postures. Spread and override: {**STANDING, "arm": 90}
STANDING = {
    "root": [50, 50], "torso": 0, "head": 0,
    "arm": 180, "forearm": 180, "thigh": 180, "shin": 180,
}

SEATED = {
    "root": [44, 52], "torso": 0, "head": 0,
    "arm": 168, "forearm": 176, "thigh": 95, "shin": 178,
}

SUPINE = {          # on the back, head to the left
    "root": [56, 62], "torso": 272, "head": 272,
    "arm": 255, "forearm": 252, "thigh": 92, "shin": 92,
}

PRONE = {           # face down, head to the left
    "root": [56, 64], "torso": 272, "head": 268,
    "arm": 244, "forearm": 214, "thigh": 92, "shin": 92,
}

QUADRUPED = {       # hands and knees, head to the left
    "root": [60, 46], "torso": 268, "head": 262,
    "arm": 178, "forearm": 178, "thigh": 180, "shin": 92,
}


def frames(start: dict, end: dict) -> dict:
    return {"start": start, "end": end}
