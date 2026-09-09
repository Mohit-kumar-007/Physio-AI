"""Everyday strength training - push-ups, pull-ups, curls and the rest.

Same shape as the rehab catalogue in exercise_data, same pose engine, same
scoring. These are fitness movements rather than clinical rehab, so they live
in their own "strength" category and the planner never prescribes them: a
recovery plan is built from the diagnosed body part, and strength is not one.

Rep bands are image-plane degrees at the tracked joint. They are the target a
trained adult should reach; _adaptive_thresholds in pose.py still counts reps
for someone with a shorter range, so a beginner's half push-up is not a zero.
"""

from __future__ import annotations

from .landmarks import (
    L_ANKLE, L_ELBOW, L_HIP, L_KNEE, L_SHOULDER, L_WRIST,
    R_ANKLE, R_ELBOW, R_HIP, R_KNEE, R_SHOULDER, R_WRIST,
)
from .postures import STANDING, frames

# --- form rules -------------------------------------------------------------
# Same landmarks as the rehab rules but different thresholds and cues: a lifter
# is told to stop swinging, a patient is told not to arch.
BODY_STRAIGHT = {
    "id": "body_not_straight",
    "angle": [L_SHOULDER, L_HIP, L_KNEE], "mirror": [R_SHOULDER, R_HIP, R_KNEE],
    "min": 155,
    "msg_en": "Keep a straight line from head to heels - no sagging or piking",
    "msg_hi": "सिर से एड़ी तक शरीर सीधा रखें - कमर न झुकाएँ, न कूल्हे ऊपर उठाएँ",
}
NO_SWING = {
    "id": "swinging_body",
    "angle": [L_SHOULDER, L_HIP, L_KNEE], "mirror": [R_SHOULDER, R_HIP, R_KNEE],
    "min": 150,
    "msg_en": "Stop swinging your torso - move the weight with the muscle",
    "msg_hi": "शरीर को झटका न दें - वज़न मांसपेशी से उठाएँ",
}


STRENGTH_EXERCISES: list[dict] = [
    {
        "slug": "push-up", "name": "Push-Up",
        "name_hi": "पुश-अप", "category": "strength",
        "body_part": "Chest, Shoulders & Triceps",
        "difficulty": "medium", "target_reps": 12, "duration_seconds": 45,
        "description": "The core upper-body pushing movement - no equipment needed.",
        "description_hi": "बिना उपकरण के ऊपरी शरीर का बुनियादी पुशिंग व्यायाम।",
        "steps": [
            "Hands under your shoulders, body in one straight line.",
            "Lower your chest towards the floor, elbows about 45 degrees out.",
            "Stop when your elbows reach roughly a right angle.",
            "Press back up without letting your hips drop.",
        ],
        "steps_hi": [
            "हथेलियाँ कंधों के नीचे, शरीर एक सीधी रेखा में रखें।",
            "छाती ज़मीन की ओर नीचे लाएँ, कोहनियाँ लगभग 45 डिग्री बाहर।",
            "जब कोहनियाँ लगभग समकोण पर आ जाएँ तब रुकें।",
            "कूल्हे गिराए बिना वापस ऊपर धकेलें।",
        ],
        "mistakes": ["Letting the hips sag towards the floor",
                     "Only going halfway down"],
        "mistakes_hi": ["कूल्हों का ज़मीन की ओर झुक जाना",
                        "आधा ही नीचे जाना"],
        "camera_view": "side",
        "pose": {
            "primary_angle": [L_SHOULDER, L_ELBOW, L_WRIST],
            "primary_angle_mirror": [R_SHOULDER, R_ELBOW, R_WRIST],
            "primary_joint": "elbow",
            "mode": "range", "rep_low": 100, "rep_high": 158,
            "cue_en": "Chest to the floor, then press away - body stays rigid",
            "cue_hi": "छाती नीचे लाएँ, फिर धकेलें - शरीर कड़ा रखें",
            "form_rules": [BODY_STRAIGHT],
        },
        "preview": frames(
            {"root": [53, 71], "torso": 297, "head": 300,
             "arm": 178, "forearm": 178, "thigh": 117, "shin": 117},
            {"root": [53, 79], "torso": 297, "head": 300,
             "arm": 140, "forearm": 246, "thigh": 117, "shin": 117},
        ),
    },
    {
        "slug": "pull-up", "name": "Pull-Up",
        "name_hi": "पुल-अप", "category": "strength",
        "body_part": "Back, Lats & Biceps",
        "difficulty": "hard", "target_reps": 8, "duration_seconds": 45,
        "description": "The strongest pulling movement for back and arm strength.",
        "description_hi": "पीठ और बाँहों की ताक़त के लिए सबसे असरदार खींचने वाला व्यायाम।",
        "steps": [
            "Hang from the bar, hands a little wider than your shoulders.",
            "Start from a full hang with the arms straight.",
            "Pull your chest towards the bar, driving the elbows down.",
            "Lower under control until the arms are straight again.",
        ],
        "steps_hi": [
            "बार से लटकें, हाथ कंधों से थोड़े चौड़े रखें।",
            "पूरी तरह लटकी हुई स्थिति से शुरू करें, बाँहें सीधी।",
            "छाती बार की ओर खींचें, कोहनियाँ नीचे की ओर दबाएँ।",
            "नियंत्रण के साथ नीचे आएँ जब तक बाँहें फिर सीधी न हो जाएँ।",
        ],
        "mistakes": ["Kicking the legs to swing yourself up",
                     "Stopping short of a full hang at the bottom"],
        "mistakes_hi": ["ऊपर जाने के लिए पैर मारकर झूलना",
                        "नीचे पूरी तरह लटके बिना रुक जाना"],
        # Front-on: from the side the far arm hides the near one on the bar.
        "camera_view": "front",
        "pose": {
            "primary_angle": [L_SHOULDER, L_ELBOW, L_WRIST],
            "primary_angle_mirror": [R_SHOULDER, R_ELBOW, R_WRIST],
            "primary_joint": "elbow",
            "mode": "range", "rep_low": 80, "rep_high": 155,
            "cue_en": "Chest to the bar, then lower to a full straight hang",
            "cue_hi": "छाती बार तक लाएँ, फिर पूरी सीधी लटकन तक नीचे आएँ",
            # No torso rule: hanging with the knees bent is normal form and
            # would trip a straight-body check on every honest rep.
            "form_rules": [],
        },
        "preview": frames(
            {"root": [50, 66], "torso": 0, "head": 0,
             "arm": 18, "forearm": 18, "arm_far": 342, "forearm_far": 342,
             "thigh": 160, "shin": 60},
            {"root": [50, 50], "torso": 0, "head": 0,
             "arm": 100, "forearm": 337, "arm_far": 260, "forearm_far": 23,
             "thigh": 160, "shin": 60},
        ),
    },
    {
        "slug": "dumbbell-curl", "name": "Dumbbell Bicep Curl",
        "name_hi": "डम्बल बाइसेप कर्ल", "category": "strength",
        "body_part": "Biceps",
        "difficulty": "easy", "target_reps": 12, "duration_seconds": 40,
        "description": "Isolates the biceps with a controlled bend of the elbow.",
        "description_hi": "कोहनी के नियंत्रित मोड़ से बाइसेप्स पर सीधा असर डालता है।",
        "steps": [
            "Stand tall with a dumbbell in each hand, palms facing forward.",
            "Keep your elbows pinned at your sides.",
            "Curl the weights up towards your shoulders.",
            "Lower slowly until the arms are fully straight again.",
        ],
        "steps_hi": [
            "सीधे खड़े हों, दोनों हाथों में डम्बल, हथेलियाँ सामने की ओर।",
            "कोहनियाँ शरीर से सटी रखें।",
            "वज़न कंधों की ओर ऊपर मोड़ें।",
            "धीरे-धीरे नीचे लाएँ जब तक बाँहें पूरी सीधी न हो जाएँ।",
        ],
        "mistakes": ["Swinging the body to throw the weight up",
                     "Not straightening the arm at the bottom"],
        "mistakes_hi": ["वज़न ऊपर फेंकने के लिए शरीर झुलाना",
                        "नीचे आकर बाँह पूरी सीधी न करना"],
        "camera_view": "front",
        "pose": {
            "primary_angle": [L_SHOULDER, L_ELBOW, L_WRIST],
            "primary_angle_mirror": [R_SHOULDER, R_ELBOW, R_WRIST],
            "primary_joint": "elbow",
            "mode": "range", "rep_low": 65, "rep_high": 150,
            "cue_en": "Elbows still at your sides, curl up and lower slowly",
            "cue_hi": "कोहनियाँ शरीर से सटी रहें, ऊपर मोड़ें और धीरे नीचे लाएँ",
            "form_rules": [NO_SWING],
        },
        "preview": frames(
            {**STANDING, "arm": 184, "forearm": 184,
             "arm_far": 176, "forearm_far": 176},
            {**STANDING, "arm": 186, "forearm": 20,
             "arm_far": 174, "forearm_far": 340},
        ),
    },
    {
        "slug": "shoulder-press", "name": "Dumbbell Shoulder Press",
        "name_hi": "डम्बल शोल्डर प्रेस", "category": "strength",
        "body_part": "Shoulders & Triceps",
        "difficulty": "medium", "target_reps": 10, "duration_seconds": 40,
        "description": "Overhead pressing strength for the shoulders and triceps.",
        "description_hi": "कंधों और ट्राइसेप्स के लिए सिर के ऊपर दबाने वाली ताक़त।",
        "steps": [
            "Sit or stand tall with a dumbbell at each shoulder.",
            "Elbows point out and down, wrists stacked over the elbows.",
            "Press both weights straight overhead until the arms lock out.",
            "Lower back to shoulder height with control.",
        ],
        "steps_hi": [
            "सीधे बैठें या खड़े हों, हर कंधे के पास एक डम्बल।",
            "कोहनियाँ बाहर-नीचे की ओर, कलाइयाँ कोहनियों के ऊपर।",
            "दोनों वज़न सीधे सिर के ऊपर तब तक दबाएँ जब तक बाँहें सीधी न हों।",
            "नियंत्रण के साथ कंधों की ऊँचाई तक वापस लाएँ।",
        ],
        "mistakes": ["Leaning back and turning it into a chest press",
                     "Pressing the weights forward instead of straight up"],
        "mistakes_hi": ["पीछे झुककर इसे चेस्ट प्रेस बना देना",
                        "वज़न सीधे ऊपर के बजाय आगे की ओर दबाना"],
        "camera_view": "front",
        "pose": {
            "primary_angle": [L_SHOULDER, L_ELBOW, L_WRIST],
            "primary_angle_mirror": [R_SHOULDER, R_ELBOW, R_WRIST],
            "primary_joint": "elbow",
            "mode": "range", "rep_low": 100, "rep_high": 160,
            "cue_en": "Press straight overhead, then lower to your shoulders",
            "cue_hi": "सीधे सिर के ऊपर दबाएँ, फिर कंधों तक नीचे लाएँ",
            "form_rules": [NO_SWING],
        },
        "preview": frames(
            {"root": [44, 62], "torso": 0, "head": 0,
             "arm": 120, "forearm": 20, "arm_far": 240, "forearm_far": 340,
             "thigh": 95, "shin": 178},
            {"root": [44, 62], "torso": 0, "head": 0,
             "arm": 10, "forearm": 2, "arm_far": 350, "forearm_far": 358,
             "thigh": 95, "shin": 178},
        ),
    },
    {
        "slug": "forward-lunge", "name": "Forward Lunge",
        "name_hi": "फॉरवर्ड लंज", "category": "strength",
        "body_part": "Quads, Glutes & Balance",
        "difficulty": "medium", "target_reps": 10, "duration_seconds": 45,
        "description": "Single-leg strength and balance for the thighs and glutes.",
        "description_hi": "जांघों और कूल्हों के लिए एक-पैर की ताक़त और संतुलन।",
        "steps": [
            "Stand tall with your feet hip-width apart.",
            "Step one foot forward and bend both knees.",
            "Lower until the front thigh is close to parallel with the floor.",
            "Push through the front heel to return to standing.",
        ],
        "steps_hi": [
            "सीधे खड़े हों, पैर कूल्हों जितनी दूरी पर।",
            "एक पैर आगे रखें और दोनों घुटने मोड़ें।",
            "तब तक नीचे जाएँ जब तक आगे की जांघ ज़मीन के लगभग समानांतर न हो।",
            "आगे की एड़ी पर ज़ोर देकर वापस खड़े हों।",
        ],
        "mistakes": ["Letting the front knee travel far past the toes",
                     "Leaning the chest forward over the front leg"],
        "mistakes_hi": ["आगे का घुटना पंजों से काफ़ी आगे निकल जाना",
                        "छाती का आगे वाले पैर के ऊपर झुक जाना"],
        "camera_view": "side",
        "pose": {
            "primary_angle": [L_HIP, L_KNEE, L_ANKLE],
            "primary_angle_mirror": [R_HIP, R_KNEE, R_ANKLE],
            "primary_joint": "knee",
            "mode": "range", "rep_low": 105, "rep_high": 165,
            "cue_en": "Step forward, drop straight down, drive back up",
            "cue_hi": "आगे कदम रखें, सीधा नीचे जाएँ, वापस ऊपर आएँ",
            "form_rules": [],
        },
        "preview": frames(
            STANDING,
            {"root": [50, 58], "torso": 0, "head": 0,
             "arm": 180, "forearm": 180, "thigh": 130, "shin": 190,
             "thigh_far": 200, "shin_far": 235},
        ),
    },
    {
        "slug": "sit-up", "name": "Sit-Up",
        "name_hi": "सिट-अप", "category": "strength",
        "body_part": "Abs & Core",
        "difficulty": "easy", "target_reps": 15, "duration_seconds": 45,
        "description": "Classic abdominal exercise using the full range of the trunk.",
        "description_hi": "धड़ की पूरी गति का उपयोग करने वाला पेट का क्लासिक व्यायाम।",
        "steps": [
            "Lie on your back with knees bent and feet flat on the floor.",
            "Reach your hands towards your knees.",
            "Curl your upper body up until your torso is off the floor.",
            "Lower back down with control - do not drop.",
        ],
        "steps_hi": [
            "पीठ के बल लेटें, घुटने मुड़े और पैर ज़मीन पर सपाट।",
            "हाथ घुटनों की ओर बढ़ाएँ।",
            "ऊपरी शरीर मोड़कर तब तक उठाएँ जब तक धड़ ज़मीन से न उठ जाए।",
            "नियंत्रण से नीचे आएँ - धड़ाम से न गिरें।",
        ],
        "mistakes": ["Pulling on the neck with the hands",
                     "Using a jerk instead of curling up slowly"],
        "mistakes_hi": ["हाथों से गर्दन खींचना",
                        "धीरे मोड़ने के बजाय झटका देना"],
        "camera_view": "side",
        "pose": {
            "primary_angle": [L_SHOULDER, L_HIP, L_KNEE],
            "primary_angle_mirror": [R_SHOULDER, R_HIP, R_KNEE],
            "primary_joint": "hip",
            "mode": "range", "rep_low": 85, "rep_high": 140,
            "cue_en": "Curl the chest up towards your knees, then lower slowly",
            "cue_hi": "छाती घुटनों की ओर मोड़ें, फिर धीरे नीचे लाएँ",
            "form_rules": [],
        },
        "preview": frames(
            {"root": [56, 80], "torso": 272, "head": 272,
             "arm": 72, "forearm": 72, "thigh": 45, "shin": 155},
            {"root": [56, 80], "torso": 320, "head": 325,
             "arm": 102, "forearm": 102, "thigh": 45, "shin": 155},
        ),
    },
    {
        "slug": "plank", "name": "Plank Hold",
        "name_hi": "प्लैंक होल्ड", "category": "strength",
        "body_part": "Core & Shoulders",
        "difficulty": "medium", "target_reps": 3, "duration_seconds": 60,
        "description": "Isometric hold that trains the whole core to stay rigid.",
        "description_hi": "पूरे कोर को कड़ा रखना सिखाने वाला स्थिर होल्ड।",
        "steps": [
            "Rest on your forearms with the elbows under your shoulders.",
            "Extend your legs back and come up onto your toes.",
            "Squeeze the glutes so hips, shoulders and heels form one line.",
            "Hold, breathing steadily, then rest between holds.",
        ],
        "steps_hi": [
            "कोहनियों के बल आएँ, कोहनियाँ कंधों के ठीक नीचे।",
            "पैर पीछे फैलाएँ और पंजों पर आ जाएँ।",
            "कूल्हे कसें ताकि कूल्हे, कंधे और एड़ियाँ एक रेखा में रहें।",
            "साँस लेते हुए रुकें, फिर हर होल्ड के बीच आराम करें।",
        ],
        "mistakes": ["Letting the hips sag towards the floor",
                     "Lifting the hips up into an upside-down V"],
        "mistakes_hi": ["कूल्हों का ज़मीन की ओर झुक जाना",
                        "कूल्हे ऊपर उठाकर उल्टा V बना लेना"],
        "camera_view": "side",
        "pose": {
            "primary_angle": [L_SHOULDER, L_HIP, L_KNEE],
            "primary_angle_mirror": [R_SHOULDER, R_HIP, R_KNEE],
            "primary_joint": "hip",
            # The straight line IS the exercise, so the hip angle is scored
            # directly rather than duplicated as a form rule.
            "mode": "hold", "rep_low": 155, "rep_high": 180, "hold_seconds": 10.0,
            "cue_en": "Hold the line - hips level with shoulders and heels",
            "cue_hi": "रेखा बनाए रखें - कूल्हे कंधों और एड़ियों के बराबर",
            "form_rules": [],
        },
        "preview": frames(
            {"root": [60, 80], "torso": 292, "head": 296,
             "arm": 180, "forearm": 270, "thigh": 96, "shin": 100},
            {"root": [60, 74], "torso": 284, "head": 287,
             "arm": 180, "forearm": 270, "thigh": 104, "shin": 104},
        ),
    },
]
