"""Checks for the symptom scoring engine."""

from __future__ import annotations

from backend.physio import diagnosis
from backend.physio.ocr import extract_findings


def test_routes_knee_complaints_to_knee_condition():
    result = diagnosis.analyze("my knee is swollen and hurts on stairs")
    assert result.category == "knee"
    assert result.confidence >= 0.5


def test_routes_hindi_complaints():
    result = diagnosis.analyze("मेरे घुटने में सूजन है")
    assert result.category == "knee"


def test_routes_shoulder_and_neck_separately():
    assert diagnosis.analyze("frozen shoulder, cannot reach overhead").category == "shoulder"
    assert diagnosis.analyze("neck stiffness and headache from my laptop").category == "neck"


def test_strong_evidence_beats_weak_evidence():
    vague = diagnosis.analyze("my back feels off")
    specific = diagnosis.analyze(
        "severe lower back pain, lumbar disc bulge at L4-L5 with sciatica"
    )
    assert specific.confidence > vague.confidence


def test_gibberish_is_not_confident():
    """The old code returned a hardcoded 93% for anything. It must not."""
    result = diagnosis.analyze("asdfgh qwerty zxcvb")
    assert result.is_confident is False
    assert result.confidence <= 0.5
    assert "not clear enough" in result.reply("en")


def test_confidence_never_exceeds_ceiling():
    result = diagnosis.analyze(
        "lower back lumbar disc L4 L5 S1 sciatica spondylosis slipped disc bending spine"
    )
    assert result.confidence <= diagnosis.MAX_CONFIDENCE


def test_red_flags_are_detected_and_change_the_reply():
    result = diagnosis.analyze("back pain with numbness and fever")
    assert result.red_flags
    assert "doctor" in result.reply("en").lower()


def test_red_flags_in_hindi():
    assert diagnosis.analyze("कमर दर्द के साथ सुन्न").red_flags


def test_alternatives_are_listed_when_symptoms_overlap():
    result = diagnosis.analyze("pain in my neck and also my lower back")
    assert result.alternatives


def test_reply_switches_language():
    result = diagnosis.analyze("knee pain")
    assert result.reply("en") != result.reply("hi")


def test_rebuild_from_stored_key():
    original = diagnosis.analyze("frozen shoulder")
    restored = diagnosis.from_condition_key(original.condition_key)
    assert restored.condition == original.condition
    assert restored.category == original.category


# --- report findings --------------------------------------------------------
def test_extracts_spinal_level_and_disc_finding():
    findings = extract_findings("MRI LUMBAR SPINE: Mild disc bulge noted at L4-L5.")
    kinds = {f["type"] for f in findings}
    assert "spinal_level" in kinds
    assert "disc" in kinds


def test_extracts_knee_ligament_tear():
    findings = extract_findings("Partial ACL tear with joint effusion.")
    assert any(f["type"] == "knee_ligament" for f in findings)


def test_clean_report_yields_no_false_findings():
    assert extract_findings("No abnormality detected. Study within normal limits.") == []
