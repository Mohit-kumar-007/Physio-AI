"""Symptom -> likely condition scoring.

Replaces the frontend's four hardcoded if/else branches with weighted evidence
matching in English and Hindi. Confidence is computed from how much of a
condition's evidence actually appeared and how far ahead it is of the runner
up -- not a literal typed into the source.

`analyze()` is the seam: swap its body for an LLM call later and every caller
keeps working, because the return type stays the same.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

# Weight reflects how strongly a term points at the condition.
# 3 = near-pathognomonic, 2 = strong, 1 = supportive.
CONDITIONS: list[dict] = [
    {
        "key": "lumbar_disc",
        "name": "Lumbar Disc Spondylosis",
        "name_hi": "लंबर डिस्क स्पॉन्डिलोसिस",
        "category": "back",
        "terms": {
            "lower back": 3, "low back": 3, "lumbar": 3, "back pain": 2,
            "backache": 2, "disc": 3, "l4": 3, "l5": 3, "s1": 2, "sciatica": 3,
            "spine": 1, "bending": 1, "slipped disc": 3, "spondylosis": 3,
            "कमर": 3, "पीठ": 2, "कमर दर्द": 3, "रीढ़": 2, "डिस्क": 3,
            "झुकने": 1, "साइटिका": 3,
        },
        "symptoms": ["Lower Back Pain", "Stiffness on Bending", "Hip Radiation"],
        "symptoms_hi": ["कमर दर्द", "झुकने पर जकड़न", "कूल्हे में दर्द फैलना"],
        "advice": ("Lumbar extension, cat-cow stretches, core stabilization and "
                   "ice therapy for acute flare-ups."),
        "advice_hi": ("लंबर एक्सटेंशन, कैट-काउ स्ट्रैच, कोर स्टेबलाइज़ेशन और "
                      "तेज़ दर्द में बर्फ की सेंक।"),
    },
    {
        "key": "patellofemoral",
        "name": "Patellofemoral Pain Syndrome",
        "name_hi": "घुटने के जोड़ का दर्द (पेटेलोफेमोरल)",
        "category": "knee",
        "terms": {
            "knee": 3, "kneecap": 3, "patella": 3, "patellar": 3, "stairs": 2,
            "squat": 1, "clicking": 2, "swollen knee": 3, "meniscus": 2,
            "acl": 2, "grinding": 2,
            "घुटने": 3, "घुटना": 3, "घुटनों": 3, "सीढ़ी": 2, "सूजन": 1,
        },
        "symptoms": ["Knee Swelling", "Stair Difficulty", "Patellar Clicking"],
        "symptoms_hi": ["घुटनों में सूजन", "सीढ़ी चढ़ने में परेशानी", "घुटने में क्लिकिंग"],
        "advice": ("Quadriceps setting, straight leg raises and low-impact "
                   "mobility work. Avoid deep squats until pain settles."),
        "advice_hi": ("क्वाड्रिसेप्स सेटिंग, स्ट्रेट लेग रेज़ और हल्के गतिशीलता व्यायाम। "
                      "दर्द कम होने तक गहरी स्क्वाट से बचें।"),
    },
    {
        "key": "frozen_shoulder",
        "name": "Adhesive Capsulitis (Frozen Shoulder)",
        "name_hi": "अडहेसिव कैप्सुलाइटिस (कंधे की जकड़न)",
        "category": "shoulder",
        "terms": {
            "shoulder": 3, "rotator cuff": 3, "frozen": 3, "overhead": 2,
            "lifting arm": 2, "arm": 1, "night pain": 2, "reach": 1,
            "कंधे": 3, "कंधा": 3, "जकड़न": 2, "हाथ उठाने": 2, "बाजू": 1,
        },
        "symptoms": ["Restricted Overhead Reach", "Shoulder Joint Ache", "Night Pain"],
        "symptoms_hi": ["ऊपर हाथ उठाने में दिक्कत", "कंधे में दर्द", "रात का दर्द"],
        "advice": ("Pendulum swings, wall slides and gentle warmth twice daily. "
                   "Consistency matters more than intensity here."),
        "advice_hi": ("पेंडुलम स्विंग्स, वॉल स्लाइड्स और दिन में दो बार गर्म सेंक। "
                      "यहाँ तीव्रता से ज़्यादा नियमितता ज़रूरी है।"),
    },
    {
        "key": "cervical_strain",
        "name": "Cervical Muscle Strain",
        "name_hi": "सर्वाइकल मांसपेशियों में खिंचाव",
        "category": "neck",
        "terms": {
            "neck": 3, "cervical": 3, "headache": 2, "screen": 1, "laptop": 1,
            "desk": 1, "text neck": 3, "c5": 2, "c6": 2, "upper back": 1,
            "गर्दन": 3, "सिरदर्द": 2, "गरदन": 3, "सर्वाइकल": 3,
        },
        "symptoms": ["Neck Stiffness", "Postural Headache", "Upper Back Tightness"],
        "symptoms_hi": ["गर्दन की जकड़न", "मुद्रा-जनित सिरदर्द", "ऊपरी पीठ में कसाव"],
        "advice": ("Cervical chin tucks, gentle rotations and raising your screen "
                   "to eye level."),
        "advice_hi": ("सर्वाइकल चिन टक्स, हल्की घुमावट और स्क्रीन को आँखों की "
                      "ऊँचाई तक उठाना।"),
    },
    {
        "key": "postural_kyphosis",
        "name": "Postural Kyphosis",
        "name_hi": "मुद्रा-जनित कूबड़ (काइफ़ोसिस)",
        "category": "posture",
        "terms": {
            "posture": 3, "slouch": 3, "hunch": 3, "rounded shoulders": 3,
            "sitting": 1, "kyphosis": 3, "stooped": 2, "bent forward": 2,
            "मुद्रा": 3, "झुकी": 2, "कूबड़": 3, "बैठने": 1,
        },
        "symptoms": ["Rounded Shoulders", "Mid-Back Fatigue", "Forward Head Posture"],
        "symptoms_hi": ["गोल कंधे", "मध्य-पीठ थकान", "सिर आगे की ओर झुका"],
        "advice": ("Scapular retraction, thoracic extension and hourly posture "
                   "breaks during desk work."),
        "advice_hi": ("स्कैपुलर रिट्रैक्शन, थोरैसिक एक्सटेंशन और डेस्क कार्य के दौरान "
                      "हर घंटे मुद्रा ब्रेक।"),
    },
]

# Phrases that mean this needs a clinician now, not an exercise plan.
RED_FLAGS = {
    "numbness": "Numbness or tingling can indicate nerve involvement.",
    "tingling": "Numbness or tingling can indicate nerve involvement.",
    "cannot walk": "Loss of walking ability needs urgent assessment.",
    "can not walk": "Loss of walking ability needs urgent assessment.",
    "unable to walk": "Loss of walking ability needs urgent assessment.",
    "loss of bladder": "Bladder or bowel changes are a medical emergency.",
    "bowel": "Bladder or bowel changes are a medical emergency.",
    "fever": "Fever with joint or spinal pain may indicate infection.",
    "unexplained weight loss": "Unexplained weight loss requires medical review.",
    "chest pain": "Chest pain requires immediate medical attention.",
    "fracture": "A suspected fracture must be imaged before any exercise.",
    "सुन्न": "सुन्नपन नस से जुड़ी समस्या का संकेत हो सकता है।",
    "झुनझुनी": "झुनझुनी नस से जुड़ी समस्या का संकेत हो सकती है।",
    "बुखार": "जोड़ या रीढ़ के दर्द के साथ बुखार संक्रमण का संकेत हो सकता है।",
    "चल नहीं": "चलने में असमर्थता की तुरंत जाँच ज़रूरी है।",
}

MIN_CONFIDENCE = 0.35
MAX_CONFIDENCE = 0.95
DEFAULT_CONDITION = "lumbar_disc"   # most common presentation, used on no match


@dataclass
class Diagnosis:
    condition_key: str
    condition: str
    condition_hi: str
    category: str
    confidence: float
    matched_terms: list[str]
    symptoms: list[str]
    symptoms_hi: list[str]
    advice: str
    advice_hi: str
    red_flags: list[str] = field(default_factory=list)
    alternatives: list[dict] = field(default_factory=list)
    is_confident: bool = True

    def reply(self, lang: str = "en") -> str:
        name = self.condition_hi if lang == "hi" else self.condition
        pct = round(self.confidence * 100)
        if self.red_flags:
            return (
                f"मैंने आपके विवरण में कुछ चेतावनी संकेत देखे हैं। कृपया व्यायाम शुरू करने से "
                f"पहले डॉक्टर से मिलें। संभावित स्थिति: {name} ({pct}%)।"
                if lang == "hi" else
                f"I noticed some warning signs in your description. Please see a "
                f"doctor before starting any exercises. Possible condition: "
                f"{name} ({pct}% confidence)."
            )
        if not self.is_confident:
            return (
                f"आपके लक्षण स्पष्ट नहीं हैं। सबसे संभावित स्थिति {name} ({pct}%) लगती है, "
                f"लेकिन कृपया और विवरण दें — दर्द कहाँ है और कब बढ़ता है?"
                if lang == "hi" else
                f"Your symptoms are not clear enough yet. The closest match is "
                f"{name} ({pct}% confidence) - could you tell me where exactly it "
                f"hurts and what makes it worse?"
            )
        return (
            f"आपके लक्षणों के आधार पर संभावित स्थिति {name} है ({pct}% विश्वास)। "
            f"मैं आपके लिए व्यक्तिगत रिकवरी योजना तैयार कर सकता हूँ!"
            if lang == "hi" else
            f"Based on your symptoms, the most likely condition is {name} "
            f"({pct}% confidence). I can generate a tailored recovery plan for you!"
        )


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def _score(text: str, condition: dict) -> tuple[float, list[str]]:
    """Sum the weights of every term present. Returns (score, matched terms)."""
    score, matched = 0.0, []
    for term, weight in condition["terms"].items():
        if term in text:
            score += weight
            matched.append(term)
    return score, matched


def find_red_flags(text: str) -> list[str]:
    seen, flags = set(), []
    for phrase, warning in RED_FLAGS.items():
        if phrase in text and warning not in seen:
            seen.add(warning)
            flags.append(warning)
    return flags


def analyze(text: str, lang: str = "en") -> Diagnosis:
    """Score every condition against the text and return the best match.

    Confidence blends two signals: how much evidence this condition collected
    relative to its own maximum, and how clearly it beat the runner up. A
    single vague word therefore cannot produce a 93% result.
    """
    norm = _normalize(text)
    red_flags = find_red_flags(norm)

    scored = []
    for cond in CONDITIONS:
        score, matched = _score(norm, cond)
        if score > 0:
            scored.append((score, cond, matched))
    scored.sort(key=lambda item: item[0], reverse=True)

    if not scored:
        cond = next(c for c in CONDITIONS if c["key"] == DEFAULT_CONDITION)
        return _build(cond, MIN_CONFIDENCE, [], red_flags, [], is_confident=False)

    top_score, top_cond, matched = scored[0]
    runner_up = scored[1][0] if len(scored) > 1 else 0.0

    # Evidence ratio: how much of this condition's vocabulary actually showed up.
    max_possible = sum(sorted(top_cond["terms"].values(), reverse=True)[:3])
    evidence = min(top_score / max_possible, 1.0)

    # Separation: how decisively it beat the next best explanation.
    separation = (top_score - runner_up) / top_score if top_score else 0.0

    confidence = MIN_CONFIDENCE + (0.6 * evidence + 0.4 * separation) * (
        MAX_CONFIDENCE - MIN_CONFIDENCE
    )
    confidence = round(min(max(confidence, MIN_CONFIDENCE), MAX_CONFIDENCE), 2)

    alternatives = [
        {"condition": c["name"], "condition_hi": c["name_hi"],
         "score": round(s / top_score, 2)}
        for s, c, _ in scored[1:3]
    ]
    return _build(top_cond, confidence, matched, red_flags, alternatives,
                  is_confident=confidence >= 0.5)


def from_condition_key(key: str, confidence: float = MIN_CONFIDENCE,
                       red_flags: list[str] | None = None) -> Diagnosis:
    """Rebuild a Diagnosis from a stored assessment row.

    Lets the planner work from history without re-running the text analysis.
    """
    cond = next(
        (c for c in CONDITIONS if c["key"] == key),
        next(c for c in CONDITIONS if c["key"] == DEFAULT_CONDITION),
    )
    return _build(cond, confidence, [], red_flags or [], [], is_confident=True)


def _build(cond, confidence, matched, red_flags, alternatives, is_confident):
    return Diagnosis(
        condition_key=cond["key"],
        condition=cond["name"],
        condition_hi=cond["name_hi"],
        category=cond["category"],
        confidence=confidence,
        matched_terms=matched,
        symptoms=cond["symptoms"],
        symptoms_hi=cond["symptoms_hi"],
        advice=cond["advice"],
        advice_hi=cond["advice_hi"],
        red_flags=red_flags,
        alternatives=alternatives,
        is_confident=is_confident,
    )
