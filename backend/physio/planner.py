"""Builds a recovery plan from a diagnosis.

Exercise selection is driven by the diagnosed category and progresses by
difficulty across the plan's weeks, so week 2 is not a copy of week 1.
"""

from __future__ import annotations

from .exercise_data import EXERCISES

PLAN_DAYS = 14
DIFFICULTY_ORDER = {"easy": 0, "medium": 1, "hard": 2}

DIET_BY_CATEGORY = {
    "default": [
        {"meal": "Breakfast", "meal_hi": "नाश्ता",
         "items": "Oatmeal with berries & chia seeds",
         "items_hi": "ओट्स, बेरीज, अलसी के बीज",
         "note": "Omega-3 helps control inflammation",
         "note_hi": "ओमेगा-3 सूजन कम करने में मदद करता है"},
        {"meal": "Lunch", "meal_hi": "दोपहर",
         "items": "Lentil soup, brown rice & spinach",
         "items_hi": "दाल, ब्राउन राइस, पालक",
         "note": "Protein and calcium for tissue repair",
         "note_hi": "ऊतक मरम्मत के लिए प्रोटीन और कैल्शियम"},
        {"meal": "Dinner", "meal_hi": "रात",
         "items": "Grilled vegetables with tofu & turmeric milk",
         "items_hi": "हरी सब्ज़ियाँ, टोफू और हल्दी दूध",
         "note": "Curcumin supports overnight recovery",
         "note_hi": "करक्यूमिन रातभर रिकवरी में सहायक"},
    ],
    "knee": [
        {"meal": "Breakfast", "meal_hi": "नाश्ता",
         "items": "Greek yogurt with walnuts & banana",
         "items_hi": "दही, अखरोट और केला",
         "note": "Collagen and potassium for joint cartilage",
         "note_hi": "जोड़ों की उपास्थि के लिए कोलेजन और पोटैशियम"},
        {"meal": "Lunch", "meal_hi": "दोपहर",
         "items": "Rajma, millet roti & steamed broccoli",
         "items_hi": "राजमा, बाजरे की रोटी और ब्रोकली",
         "note": "Vitamin K supports bone density",
         "note_hi": "विटामिन K हड्डियों की मजबूती बढ़ाता है"},
        {"meal": "Dinner", "meal_hi": "रात",
         "items": "Fish or paneer with sweet potato",
         "items_hi": "मछली या पनीर के साथ शकरकंद",
         "note": "Lean protein preserves quadriceps mass",
         "note_hi": "दुबला प्रोटीन जांघ की मांसपेशी बनाए रखता है"},
    ],
}

ROUTINE_TEMPLATE = [
    {"time": "08:00", "act": "Morning gentle stretching & hydration",
     "act_hi": "सुबह हल्का खिंचाव और पानी पिएँ"},
    {"time": "14:00", "act": "Postural check & 5-minute walk",
     "act_hi": "मुद्रा जाँच और 5-मिनट सैर"},
    {"time": "20:30", "act": "AI guided pose session (15 minutes)",
     "act_hi": "AI निर्देशित पोज़ सत्र (15 मिनट)"},
]


def _pick_exercises(category: str, limit: int = 4) -> list[dict]:
    """Category first, easiest first; top up from general posture work."""
    matched = [e for e in EXERCISES if e["category"] == category]
    matched.sort(key=lambda e: DIFFICULTY_ORDER.get(e["difficulty"], 9))
    if len(matched) < limit:
        filler = [
            e for e in EXERCISES
            if e["category"] == "posture" and e not in matched
        ]
        matched.extend(filler)
    return matched[:limit]


def build_plan(diagnosis, lang: str = "en") -> dict:
    """Return a plan dict ready to persist as JSON."""
    exercises = _pick_exercises(diagnosis.category)

    # Week 1 eases in; week 2 adds a set and the harder movements.
    weeks = []
    for week in (1, 2):
        pool = exercises if week == 2 else [
            e for e in exercises if e["difficulty"] == "easy"
        ] or exercises[:2]
        weeks.append({
            "week": week,
            "focus": "Mobility & pain relief" if week == 1 else "Strength & control",
            "focus_hi": "गतिशीलता और दर्द राहत" if week == 1 else "ताक़त और नियंत्रण",
            "exercises": [
                {
                    "slug": e["slug"],
                    "name": e["name"],
                    "name_hi": e["name_hi"],
                    "sets": 2 if week == 1 else 3,
                    "reps": e["target_reps"],
                    "time_of_day": "Morning" if i % 2 == 0 else "Evening",
                    "time_of_day_hi": "सुबह" if i % 2 == 0 else "शाम",
                }
                for i, e in enumerate(pool)
            ],
        })

    diet = DIET_BY_CATEGORY.get(diagnosis.category, DIET_BY_CATEGORY["default"])

    return {
        "title": f"{PLAN_DAYS}-Day Targeted Recovery Plan",
        "title_hi": f"{PLAN_DAYS}-दिवसीय लक्षित रिकवरी योजना",
        "condition": diagnosis.condition,
        "condition_hi": diagnosis.condition_hi,
        "category": diagnosis.category,
        "days": PLAN_DAYS,
        "weeks": weeks,
        # Flat list the exercise tab renders directly.
        "exercises": weeks[0]["exercises"],
        "diet": diet,
        "routine": ROUTINE_TEMPLATE,
        "notes": diagnosis.advice,
        "notes_hi": diagnosis.advice_hi,
    }
