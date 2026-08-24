"""The exercise catalogue plus the biomechanics config that drives pose scoring.

This is the clinical source of truth. The browser downloads a config from here
and evaluates it frame by frame for live feedback; the server re-runs the same
rules over the full timeline for the authoritative score. Keeping the rules in
one place means the live HUD and the saved result can never disagree.

Each entry carries:
  pose      - what to measure and what counts as a rep
  preview   - two stick-figure keyframes the UI animates before the session
  steps     - how to perform it, shown in the preview
  mistakes  - what usually goes wrong

BILATERAL TRACKING: `primary_angle` is the left side and `primary_angle_mirror`
the right. The analyser measures both and follows whichever side actually
moved, so a patient working their right leg is tracked correctly.

CAMERA VIEW: `camera_view` is "side" or "front". Movements in the sagittal
plane (leg raises, chin tucks) are almost flat from the front and cannot be
measured there, so the UI tells the patient where to put the camera.

Angle thresholds are STARTING VALUES and need validation by a qualified
physiotherapist against real patients before this is used for care.
"""

from __future__ import annotations

from .landmarks import (
    L_ANKLE, L_EAR, L_ELBOW, L_HIP, L_KNEE, L_SHOULDER, L_WRIST, NOSE,
    R_ANKLE, R_EAR, R_ELBOW, R_HIP, R_KNEE, R_SHOULDER, R_WRIST,
)
from .postures import PRONE, QUADRUPED, SEATED, STANDING, SUPINE, frames

# --- reusable form rules ----------------------------------------------------
KNEE_STRAIGHT = {
    "id": "knees_straight",
    "angle": [L_HIP, L_KNEE, L_ANKLE], "mirror": [R_HIP, R_KNEE, R_ANKLE],
    "min": 158,
    "msg_en": "Keep your knee straight through the movement",
    "msg_hi": "पूरे व्यायाम में घुटना सीधा रखें",
}
ELBOW_STRAIGHT = {
    "id": "elbow_straight",
    "angle": [L_SHOULDER, L_ELBOW, L_WRIST], "mirror": [R_SHOULDER, R_ELBOW, R_WRIST],
    "min": 150,
    "msg_en": "Keep your elbow straight - do not bend the arm",
    "msg_hi": "कोहनी सीधी रखें - हाथ मोड़ें नहीं",
}
NO_SHRUG = {
    "id": "shoulders_shrugging",
    "angle": [L_EAR, L_SHOULDER, L_ELBOW], "mirror": [R_EAR, R_SHOULDER, R_ELBOW],
    "min": 72,
    "msg_en": "Relax your shoulders - do not shrug towards your ears",
    "msg_hi": "कंधों को ढीला रखें - कानों की ओर न उठाएँ",
}
BACK_NEUTRAL = {
    "id": "back_arching",
    "angle": [L_SHOULDER, L_HIP, L_KNEE], "mirror": [R_SHOULDER, R_HIP, R_KNEE],
    "min": 148,
    "msg_en": "Avoid arching your lower back",
    "msg_hi": "कमर को ज़्यादा मोड़ने से बचें",
}
CHEST_UP = {
    "id": "chest_dropping",
    "angle": [L_SHOULDER, L_HIP, L_KNEE], "mirror": [R_SHOULDER, R_HIP, R_KNEE],
    "min": 62,
    "msg_en": "Keep your chest up - do not fold forward",
    "msg_hi": "छाती ऊपर रखें - आगे की ओर न झुकें",
}


EXERCISES: list[dict] = [
    # ══════════════════════════ BACK ══════════════════════════
    {
        "slug": "lumbar-extension", "name": "Lumbar Extension",
        "name_hi": "लंबर एक्सटेंशन", "category": "back", "body_part": "Lower Back",
        "difficulty": "easy", "target_reps": 10, "duration_seconds": 30,
        "description": "Gentle back bend to relieve disc pressure and stiffness.",
        "description_hi": "डिस्क के दबाव और कमर की जकड़न से राहत के लिए हल्का पीछे झुकाव।",
        "steps": [
            "Lie face down with your palms flat under your shoulders.",
            "Press slowly through your hands to lift your chest.",
            "Keep your hips and legs relaxed on the floor.",
            "Lower back down with control and repeat.",
        ],
        "steps_hi": [
            "पेट के बल लेटें, हथेलियाँ कंधों के नीचे सपाट रखें।",
            "हाथों से धीरे दबाव देकर छाती ऊपर उठाएँ।",
            "कूल्हे और पैर ज़मीन पर ढीले रखें।",
            "नियंत्रण के साथ नीचे आएँ और दोहराएँ।",
        ],
        "mistakes": ["Lifting the hips off the floor", "Pushing into sharp pain"],
        "mistakes_hi": ["कूल्हे ज़मीन से उठाना", "तेज़ दर्द के बावजूद ज़ोर लगाना"],
        "camera_view": "side",
        "pose": {
            "primary_angle": [L_SHOULDER, L_HIP, L_KNEE],
            "primary_angle_mirror": [R_SHOULDER, R_HIP, R_KNEE],
            "primary_joint": "hip",
            "mode": "range", "rep_low": 150, "rep_high": 170,
            "cue_en": "Press your chest up, keep hips on the floor",
            "cue_hi": "छाती ऊपर उठाएँ, कूल्हे ज़मीन पर रखें",
            "form_rules": [KNEE_STRAIGHT],
        },
        "preview": frames(
            PRONE,
            {**PRONE, "torso": 300, "head": 302, "arm": 200, "forearm": 186},
        ),
    },
    {
        "slug": "cat-cow", "name": "Cat-Cow Stretch",
        "name_hi": "कैट-काउ स्ट्रैच", "category": "back", "body_part": "Spine & Core",
        "difficulty": "easy", "target_reps": 12, "duration_seconds": 45,
        "description": "Mobilizes the spine and relieves thoracic tightness.",
        "description_hi": "रीढ़ की गतिशीलता बढ़ाता है और ऊपरी पीठ की जकड़न कम करता है।",
        "steps": [
            "Start on hands and knees, wrists under shoulders.",
            "Round your back upward and tuck your chin to your chest.",
            "Reverse: drop your belly, lift your chest and look forward.",
            "Move slowly between the two positions with your breath.",
        ],
        "steps_hi": [
            "हाथों और घुटनों पर आएँ, कलाइयाँ कंधों के नीचे।",
            "पीठ ऊपर की ओर गोल करें और ठोड़ी छाती से लगाएँ।",
            "अब उल्टा करें: पेट नीचे करें, छाती उठाएँ, सामने देखें।",
            "साँस के साथ दोनों स्थितियों के बीच धीरे-धीरे चलें।",
        ],
        "mistakes": ["Moving too fast to feel the stretch",
                     "Locking the elbows straight"],
        "mistakes_hi": ["इतनी तेज़ी से करना कि खिंचाव महसूस न हो",
                        "कोहनियाँ पूरी तरह जकड़ लेना"],
        "camera_view": "side",
        "pose": {
            # MediaPipe has no spine landmarks, so the head-to-torso angle is
            # used as a proxy: the neck leads both halves of a cat-cow cycle.
            "primary_angle": [L_EAR, L_SHOULDER, L_HIP],
            "primary_angle_mirror": [R_EAR, R_SHOULDER, R_HIP],
            "primary_joint": "neck",
            "mode": "range", "rep_low": 120, "rep_high": 162,
            "cue_en": "Round up and tuck the chin, then arch down and look up",
            "cue_hi": "पीठ गोल कर ठोड़ी अंदर, फिर पीठ नीचे कर ऊपर देखें",
            "form_rules": [],
        },
        "preview": frames(
            {**QUADRUPED, "torso": 262, "head": 232},
            {**QUADRUPED, "torso": 274, "head": 298},
        ),
    },
    {
        "slug": "bird-dog", "name": "Bird Dog",
        "name_hi": "बर्ड डॉग", "category": "back", "body_part": "Core & Lower Back",
        "difficulty": "medium", "target_reps": 10, "duration_seconds": 40,
        "description": "Core stabilization exercise supporting the lumbar spine.",
        "description_hi": "रीढ़ को सहारा देने वाला कोर स्थिरीकरण व्यायाम।",
        "steps": [
            "Start on hands and knees with a flat back.",
            "Extend one arm forward and the opposite leg straight back.",
            "Hold briefly, keeping your hips level and still.",
            "Return and repeat on the other side.",
        ],
        "steps_hi": [
            "हाथों और घुटनों पर आएँ, पीठ सीधी रखें।",
            "एक हाथ आगे और विपरीत पैर सीधा पीछे फैलाएँ।",
            "कुछ पल रोकें, कूल्हे सीधे और स्थिर रखें।",
            "वापस आएँ और दूसरी ओर से दोहराएँ।",
        ],
        "mistakes": ["Letting the hips rotate or tilt",
                     "Lifting the leg higher than the back"],
        "mistakes_hi": ["कूल्हों का घूमना या झुकना",
                        "पैर को पीठ से ऊँचा उठाना"],
        "camera_view": "side",
        "pose": {
            "primary_angle": [L_SHOULDER, L_HIP, L_KNEE],
            "primary_angle_mirror": [R_SHOULDER, R_HIP, R_KNEE],
            "primary_joint": "hip",
            "mode": "range", "rep_low": 105, "rep_high": 155,
            "cue_en": "Extend opposite arm and leg, keep the hips level",
            "cue_hi": "विपरीत हाथ और पैर फैलाएँ, कूल्हे सीधे रखें",
            "form_rules": [KNEE_STRAIGHT],
        },
        "preview": frames(
            QUADRUPED,
            {**QUADRUPED, "arm": 262, "forearm": 262, "thigh": 96, "shin": 92},
        ),
    },

    # ══════════════════════════ KNEE ══════════════════════════
    {
        "slug": "quad-sets", "name": "Quadriceps Setting",
        "name_hi": "क्वाड्रिसेप्स सेटिंग", "category": "knee", "body_part": "Knee / Quad",
        "difficulty": "easy", "target_reps": 10, "duration_seconds": 40,
        "description": "Isometric quad contraction supporting patellar alignment.",
        "description_hi": "घुटने की टोपी की स्थिति सुधारने वाला स्थिर (आइसोमेट्रिक) व्यायाम।",
        "steps": [
            "Sit with your leg straight out in front of you.",
            "Roll a small towel and place it under your knee.",
            "Press the back of your knee down into the towel.",
            "Hold the squeeze, then relax fully before the next rep.",
        ],
        "steps_hi": [
            "पैर सामने सीधा फैलाकर बैठें।",
            "एक छोटा तौलिया लपेटकर घुटने के नीचे रखें।",
            "घुटने का पिछला हिस्सा तौलिये पर नीचे दबाएँ।",
            "दबाव बनाए रखें, फिर अगली बार से पहले पूरी तरह ढीला छोड़ें।",
        ],
        "mistakes": ["Holding your breath while squeezing",
                     "Never fully relaxing between repetitions"],
        "mistakes_hi": ["दबाव देते समय साँस रोकना",
                        "दो बार के बीच मांसपेशी पूरी तरह ढीली न करना"],
        "camera_view": "side",
        "pose": {
            "primary_angle": [L_HIP, L_KNEE, L_ANKLE],
            "primary_angle_mirror": [R_HIP, R_KNEE, R_ANKLE],
            "primary_joint": "knee",
            # The contraction itself barely moves the joint, so this times a
            # held straight-knee position. The patient must relax out of the
            # band between reps -- see release_margin in pose.py.
            "mode": "hold", "rep_low": 170, "rep_high": 180, "hold_seconds": 4.0,
            "cue_en": "Press the back of your knee down and hold",
            "cue_hi": "घुटने का पिछला हिस्सा नीचे दबाएँ और रोकें",
            "form_rules": [],
        },
        "preview": frames(
            {**SEATED, "thigh": 92, "shin": 102, "arm": 150, "forearm": 120},
            {**SEATED, "thigh": 92, "shin": 92, "arm": 150, "forearm": 120},
        ),
    },
    {
        "slug": "straight-leg-raise", "name": "Straight Leg Raise",
        "name_hi": "स्ट्रेट लेग रेज़", "category": "knee", "body_part": "Knee & Hip",
        "difficulty": "medium", "target_reps": 12, "duration_seconds": 40,
        "description": "Strengthens hip flexors without loading the knee joint.",
        "description_hi": "घुटने पर दबाव डाले बिना कूल्हे की मांसपेशियाँ मजबूत करता है।",
        "steps": [
            "Lie on your back, one knee bent and one leg straight.",
            "Tighten the thigh of the straight leg.",
            "Lift it about 30 cm, keeping the knee locked straight.",
            "Lower slowly - do not let it drop.",
        ],
        "steps_hi": [
            "पीठ के बल लेटें, एक घुटना मोड़ें और दूसरा पैर सीधा रखें।",
            "सीधे पैर की जांघ कसें।",
            "घुटना सीधा रखते हुए पैर लगभग 30 सेमी उठाएँ।",
            "धीरे-धीरे नीचे लाएँ - अचानक न गिराएँ।",
        ],
        "mistakes": ["Bending the knee while lifting",
                     "Arching the lower back off the floor"],
        "mistakes_hi": ["उठाते समय घुटना मोड़ना",
                        "कमर को ज़मीन से ऊपर उठाना"],
        "camera_view": "side",
        "pose": {
            "primary_angle": [L_SHOULDER, L_HIP, L_KNEE],
            "primary_angle_mirror": [R_SHOULDER, R_HIP, R_KNEE],
            "primary_joint": "hip",
            "mode": "range", "rep_low": 140, "rep_high": 168,
            "cue_en": "Lift the straight leg, lower it slowly",
            "cue_hi": "सीधा पैर उठाएँ, धीरे नीचे लाएँ",
            "form_rules": [KNEE_STRAIGHT],
        },
        "preview": frames(
            SUPINE,
            {**SUPINE, "thigh": 52, "shin": 52},
        ),
    },
    {
        "slug": "terminal-knee-ext", "name": "Terminal Knee Extension",
        "name_hi": "टर्मिनल नी एक्सटेंशन", "category": "knee", "body_part": "Knee / VMO",
        "difficulty": "medium", "target_reps": 15, "duration_seconds": 35,
        "description": "Targets the VMO to improve knee tracking and stability.",
        "description_hi": "घुटने की स्थिरता के लिए VMO मांसपेशी को लक्षित करता है।",
        "steps": [
            "Stand with a slight bend in the working knee.",
            "Straighten the knee fully, squeezing the inner thigh.",
            "Hold the straight position for one second.",
            "Return to the slight bend and repeat.",
        ],
        "steps_hi": [
            "काम करने वाले घुटने को हल्का मोड़कर खड़े हों।",
            "भीतरी जांघ कसते हुए घुटना पूरी तरह सीधा करें।",
            "सीधी स्थिति में एक सेकंड रुकें।",
            "फिर हल्के मोड़ पर लौटें और दोहराएँ।",
        ],
        "mistakes": ["Locking the knee back too hard",
                     "Shifting your weight onto the other leg"],
        "mistakes_hi": ["घुटने को ज़ोर से पीछे जकड़ना",
                        "पूरा वज़न दूसरे पैर पर डाल देना"],
        "camera_view": "side",
        "pose": {
            "primary_angle": [L_HIP, L_KNEE, L_ANKLE],
            "primary_angle_mirror": [R_HIP, R_KNEE, R_ANKLE],
            "primary_joint": "knee",
            "mode": "range", "rep_low": 155, "rep_high": 174,
            "cue_en": "Straighten the knee fully, squeeze the inner thigh",
            "cue_hi": "घुटना पूरा सीधा करें, भीतरी जांघ कसें",
            "form_rules": [],
        },
        "preview": frames(
            {**STANDING, "shin": 158},
            STANDING,
        ),
    },
    {
        "slug": "squat", "name": "Bodyweight Squat",
        "name_hi": "बॉडीवेट स्क्वाट", "category": "knee", "body_part": "Knees, Hips & Glutes",
        "difficulty": "medium", "target_reps": 12, "duration_seconds": 45,
        "description": "Builds overall leg strength and controlled knee bending.",
        "description_hi": "पैरों की समग्र ताक़त और घुटने के नियंत्रित मोड़ के लिए।",
        "steps": [
            "Stand with feet shoulder-width apart, toes slightly out.",
            "Push your hips back and bend your knees as if sitting down.",
            "Go as low as is comfortable, keeping your chest up.",
            "Drive through your heels to stand back up.",
        ],
        "steps_hi": [
            "पैर कंधों जितनी दूरी पर, पंजे हल्के बाहर की ओर रखें।",
            "कूल्हे पीछे धकेलें और घुटने मोड़ें, जैसे बैठने जा रहे हों।",
            "जितना आराम से हो सके नीचे जाएँ, छाती ऊपर रखें।",
            "एड़ियों पर ज़ोर देकर वापस खड़े हों।",
        ],
        "mistakes": ["Letting the knees collapse inward",
                     "Rounding the back at the bottom"],
        "mistakes_hi": ["घुटनों का अंदर की ओर मुड़ना",
                        "नीचे जाते समय पीठ गोल हो जाना"],
        "camera_view": "side",
        "pose": {
            "primary_angle": [L_HIP, L_KNEE, L_ANKLE],
            "primary_angle_mirror": [R_HIP, R_KNEE, R_ANKLE],
            "primary_joint": "knee",
            "mode": "range", "rep_low": 112, "rep_high": 164,
            "cue_en": "Hips back, chest up, drive through your heels",
            "cue_hi": "कूल्हे पीछे, छाती ऊपर, एड़ियों पर ज़ोर",
            "form_rules": [CHEST_UP],
        },
        "preview": frames(
            {**STANDING, "arm": 95, "forearm": 92},
            {"root": [50, 62], "torso": 20, "head": 8,
             "arm": 95, "forearm": 92, "thigh": 148, "shin": 196},
        ),
    },
    {
        "slug": "heel-slides", "name": "Heel Slides",
        "name_hi": "हील स्लाइड्स", "category": "knee", "body_part": "Knee Flexion",
        "difficulty": "easy", "target_reps": 12, "duration_seconds": 40,
        "description": "Restores knee bending range after injury or surgery.",
        "description_hi": "चोट या सर्जरी के बाद घुटने के मुड़ने की क्षमता लौटाता है।",
        "steps": [
            "Lie on your back with both legs straight.",
            "Slowly slide one heel towards your buttock.",
            "Bend only as far as is comfortable, then pause.",
            "Slide the heel back down until the leg is straight.",
        ],
        "steps_hi": [
            "पीठ के बल लेटें, दोनों पैर सीधे रखें।",
            "एक एड़ी धीरे-धीरे कूल्हे की ओर सरकाएँ।",
            "जितना आराम से हो सके उतना ही मोड़ें, फिर रुकें।",
            "एड़ी वापस सरकाकर पैर सीधा करें।",
        ],
        "mistakes": ["Forcing the bend past sharp pain",
                     "Lifting the heel off the surface"],
        "mistakes_hi": ["तेज़ दर्द के बावजूद ज़बरदस्ती मोड़ना",
                        "एड़ी को सतह से ऊपर उठाना"],
        "camera_view": "side",
        "pose": {
            "primary_angle": [L_HIP, L_KNEE, L_ANKLE],
            "primary_angle_mirror": [R_HIP, R_KNEE, R_ANKLE],
            "primary_joint": "knee",
            "mode": "range", "rep_low": 112, "rep_high": 160,
            "cue_en": "Slide the heel up slowly, then straighten fully",
            "cue_hi": "एड़ी धीरे ऊपर सरकाएँ, फिर पूरा सीधा करें",
            "form_rules": [],
        },
        "preview": frames(
            SUPINE,
            {**SUPINE, "thigh": 58, "shin": 132},
        ),
    },
    {
        "slug": "seated-knee-extension", "name": "Seated Knee Extension",
        "name_hi": "बैठकर घुटना सीधा करना", "category": "knee",
        "body_part": "Quadriceps",
        "difficulty": "easy", "target_reps": 12, "duration_seconds": 40,
        "description": "Strengthens the quadriceps through the full knee range.",
        "description_hi": "घुटने की पूरी गति सीमा में जांघ की मांसपेशी मजबूत करता है।",
        "steps": [
            "Sit tall on a chair with both feet on the floor.",
            "Straighten one knee until the leg is horizontal.",
            "Hold for two seconds at the top.",
            "Lower the foot back down slowly.",
        ],
        "steps_hi": [
            "कुर्सी पर सीधे बैठें, दोनों पैर ज़मीन पर रखें।",
            "एक घुटना सीधा करें जब तक पैर सीधा क्षैतिज न हो जाए।",
            "ऊपर दो सेकंड रुकें।",
            "पैर धीरे-धीरे नीचे लाएँ।",
        ],
        "mistakes": ["Swinging the leg up with momentum",
                     "Slouching back in the chair"],
        "mistakes_hi": ["झटके से पैर ऊपर उछालना",
                        "कुर्सी पर पीछे झुककर बैठना"],
        "camera_view": "side",
        "pose": {
            "primary_angle": [L_HIP, L_KNEE, L_ANKLE],
            "primary_angle_mirror": [R_HIP, R_KNEE, R_ANKLE],
            "primary_joint": "knee",
            "mode": "range", "rep_low": 115, "rep_high": 165,
            "cue_en": "Straighten the knee, hold, then lower with control",
            "cue_hi": "घुटना सीधा करें, रोकें, फिर नियंत्रण से नीचे लाएँ",
            "form_rules": [],
        },
        "preview": frames(
            SEATED,
            {**SEATED, "shin": 96},
        ),
    },
    {
        "slug": "wall-sit", "name": "Wall Sit",
        "name_hi": "वॉल सिट", "category": "knee", "body_part": "Quads & Glutes",
        "difficulty": "medium", "target_reps": 5, "duration_seconds": 60,
        "description": "Isometric hold that builds knee and thigh endurance.",
        "description_hi": "घुटने और जांघ की सहनशक्ति बढ़ाने वाला स्थिर होल्ड।",
        "steps": [
            "Stand with your back flat against a wall.",
            "Walk your feet forward about two steps.",
            "Slide down until your knees are bent near 90 degrees.",
            "Hold, then push back up to standing between reps.",
        ],
        "steps_hi": [
            "पीठ दीवार से सटाकर खड़े हों।",
            "पैर लगभग दो कदम आगे रखें।",
            "नीचे सरकें जब तक घुटने लगभग 90 डिग्री न मुड़ जाएँ।",
            "रुकें, फिर हर बार के बीच वापस खड़े हो जाएँ।",
        ],
        "mistakes": ["Letting the knees travel past the toes",
                     "Sliding down further than 90 degrees too early"],
        "mistakes_hi": ["घुटनों का पंजों से आगे निकल जाना",
                        "शुरुआत में ही 90 डिग्री से ज़्यादा नीचे जाना"],
        "camera_view": "side",
        "pose": {
            "primary_angle": [L_HIP, L_KNEE, L_ANKLE],
            "primary_angle_mirror": [R_HIP, R_KNEE, R_ANKLE],
            "primary_joint": "knee",
            "mode": "hold", "rep_low": 78, "rep_high": 116, "hold_seconds": 10.0,
            "cue_en": "Hold the seated position, back flat on the wall",
            "cue_hi": "बैठी हुई स्थिति में रुकें, पीठ दीवार से सटी रहे",
            "form_rules": [],
        },
        "preview": frames(
            STANDING,
            {"root": [46, 62], "torso": 0, "head": 0,
             "arm": 178, "forearm": 178, "thigh": 96, "shin": 178},
        ),
    },
    {
        "slug": "hamstring-curl", "name": "Standing Hamstring Curl",
        "name_hi": "खड़े होकर हैमस्ट्रिंग कर्ल", "category": "knee",
        "body_part": "Hamstrings",
        "difficulty": "easy", "target_reps": 12, "duration_seconds": 40,
        "description": "Strengthens the hamstrings to balance the front of the thigh.",
        "description_hi": "जांघ के आगे-पीछे संतुलन के लिए हैमस्ट्रिंग मजबूत करता है।",
        "steps": [
            "Stand tall, holding a chair for balance.",
            "Bend one knee, bringing the heel towards your buttock.",
            "Keep your thighs level with each other.",
            "Lower the foot back to the floor with control.",
        ],
        "steps_hi": [
            "सीधे खड़े हों, संतुलन के लिए कुर्सी पकड़ें।",
            "एक घुटना मोड़ें और एड़ी कूल्हे की ओर लाएँ।",
            "दोनों जांघें एक सीध में रखें।",
            "पैर नियंत्रण के साथ वापस ज़मीन पर लाएँ।",
        ],
        "mistakes": ["Swinging the hip forward to help",
                     "Leaning the upper body forward"],
        "mistakes_hi": ["मदद के लिए कूल्हा आगे झुकाना",
                        "ऊपरी शरीर आगे की ओर झुकाना"],
        "camera_view": "side",
        "pose": {
            "primary_angle": [L_HIP, L_KNEE, L_ANKLE],
            "primary_angle_mirror": [R_HIP, R_KNEE, R_ANKLE],
            "primary_joint": "knee",
            "mode": "range", "rep_low": 95, "rep_high": 162,
            "cue_en": "Heel towards your buttock, keep the thigh still",
            "cue_hi": "एड़ी कूल्हे की ओर, जांघ स्थिर रखें",
            "form_rules": [],
        },
        "preview": frames(
            STANDING,
            {**STANDING, "shin": 62},
        ),
    },

    # ══════════════════════════ HIP ══════════════════════════
    {
        "slug": "glute-bridge", "name": "Glute Bridge",
        "name_hi": "ग्लूट ब्रिज", "category": "hip", "body_part": "Glutes & Lower Back",
        "difficulty": "easy", "target_reps": 12, "duration_seconds": 45,
        "description": "Strengthens the glutes to take load off the lower back.",
        "description_hi": "कमर से भार हटाने के लिए कूल्हे की मांसपेशियाँ मजबूत करता है।",
        "steps": [
            "Lie on your back with knees bent and feet flat.",
            "Squeeze your glutes and lift your hips off the floor.",
            "Make a straight line from knees to shoulders.",
            "Lower the hips back down slowly.",
        ],
        "steps_hi": [
            "पीठ के बल लेटें, घुटने मोड़ें और तलवे ज़मीन पर रखें।",
            "कूल्हे की मांसपेशियाँ कसकर कूल्हे ऊपर उठाएँ।",
            "घुटनों से कंधों तक सीधी रेखा बनाएँ।",
            "कूल्हे धीरे-धीरे नीचे लाएँ।",
        ],
        "mistakes": ["Pushing the hips too high and arching the back",
                     "Letting the knees fall apart"],
        "mistakes_hi": ["कूल्हे बहुत ऊँचे उठाकर कमर मोड़ना",
                        "घुटनों का बाहर की ओर फैल जाना"],
        "camera_view": "side",
        "pose": {
            "primary_angle": [L_SHOULDER, L_HIP, L_KNEE],
            "primary_angle_mirror": [R_SHOULDER, R_HIP, R_KNEE],
            "primary_joint": "hip",
            "mode": "range", "rep_low": 128, "rep_high": 158,
            "cue_en": "Squeeze the glutes and lift, do not arch the back",
            "cue_hi": "कूल्हे कसकर उठाएँ, कमर को न मोड़ें",
            "form_rules": [],
        },
        "preview": frames(
            {**SUPINE, "root": [56, 62], "thigh": 66, "shin": 148},
            {**SUPINE, "root": [56, 52], "torso": 278, "thigh": 82, "shin": 152},
        ),
    },
    {
        "slug": "hip-abduction", "name": "Standing Hip Abduction",
        "name_hi": "खड़े होकर हिप अब्डक्शन", "category": "hip",
        "body_part": "Hip Abductors",
        "difficulty": "easy", "target_reps": 12, "duration_seconds": 40,
        "description": "Strengthens the side of the hip to steady your walking.",
        "description_hi": "चलने में स्थिरता के लिए कूल्हे की बगल की मांसपेशी मजबूत करता है।",
        "steps": [
            "Stand tall, holding a chair for balance.",
            "Lift one leg straight out to the side.",
            "Keep your toes pointing forward, not up.",
            "Lower the leg back down with control.",
        ],
        "steps_hi": [
            "सीधे खड़े हों, संतुलन के लिए कुर्सी पकड़ें।",
            "एक पैर सीधा बगल की ओर उठाएँ।",
            "पंजे सामने की ओर रखें, ऊपर की ओर नहीं।",
            "पैर नियंत्रण के साथ नीचे लाएँ।",
        ],
        "mistakes": ["Leaning your body to the opposite side",
                     "Rotating the leg so the toes point up"],
        "mistakes_hi": ["शरीर को विपरीत दिशा में झुकाना",
                        "पैर घुमाकर पंजे ऊपर कर देना"],
        "camera_view": "front",
        "pose": {
            "primary_angle": [L_SHOULDER, L_HIP, L_KNEE],
            "primary_angle_mirror": [R_SHOULDER, R_HIP, R_KNEE],
            "primary_joint": "hip",
            "mode": "range", "rep_low": 145, "rep_high": 170,
            "cue_en": "Lift the leg out to the side, stay upright",
            "cue_hi": "पैर बगल में उठाएँ, शरीर सीधा रखें",
            "form_rules": [KNEE_STRAIGHT],
        },
        "preview": frames(
            {**STANDING, "thigh_far": 180, "shin_far": 180},
            {**STANDING, "thigh": 218, "shin": 218, "thigh_far": 180, "shin_far": 180},
        ),
    },

    # ══════════════════════════ SHOULDER ══════════════════════════
    {
        "slug": "pendulum", "name": "Shoulder Pendulum",
        "name_hi": "शोल्डर पेंडुलम", "category": "shoulder", "body_part": "Rotator Cuff",
        "difficulty": "easy", "target_reps": 15, "duration_seconds": 35,
        "description": "Passive range-of-motion work for a stiff or painful shoulder.",
        "description_hi": "अकड़े या दर्द वाले कंधे के लिए हल्का गति-सीमा व्यायाम।",
        "steps": [
            "Lean forward and support yourself on a table with the good arm.",
            "Let the sore arm hang straight down and relax completely.",
            "Use your body, not your shoulder, to swing the arm gently.",
            "Swing forward and back in a small, easy arc.",
        ],
        "steps_hi": [
            "आगे झुकें और अच्छे हाथ से मेज़ का सहारा लें।",
            "दर्द वाला हाथ सीधा नीचे लटकने दें और पूरी तरह ढीला छोड़ें।",
            "कंधे से नहीं, शरीर की गति से हाथ को धीरे झुलाएँ।",
            "छोटे और आसान दायरे में आगे-पीछे झुलाएँ।",
        ],
        "mistakes": ["Using the shoulder muscles to move the arm",
                     "Swinging in too large an arc"],
        "mistakes_hi": ["हाथ हिलाने के लिए कंधे की मांसपेशी लगाना",
                        "बहुत बड़े दायरे में झुलाना"],
        "camera_view": "side",
        "pose": {
            # Bent at the hips, so the hanging arm sits near 90 degrees to the
            # torso -- not the ~15 degrees it would be standing upright.
            "primary_angle": [L_HIP, L_SHOULDER, L_ELBOW],
            "primary_angle_mirror": [R_HIP, R_SHOULDER, R_ELBOW],
            "primary_joint": "shoulder",
            "mode": "range", "rep_low": 72, "rep_high": 100,
            "cue_en": "Let the arm hang loose and swing it gently",
            "cue_hi": "हाथ ढीला लटकाकर धीरे झुलाएँ",
            "form_rules": [],
        },
        "preview": frames(
            {**STANDING, "root": [44, 48], "torso": 62, "head": 74,
             "arm": 178, "forearm": 178},
            {**STANDING, "root": [44, 48], "torso": 62, "head": 74,
             "arm": 138, "forearm": 138},
        ),
    },
    {
        "slug": "wall-slides", "name": "Wall Slides",
        "name_hi": "वॉल स्लाइड्स", "category": "shoulder", "body_part": "Shoulder & Traps",
        "difficulty": "medium", "target_reps": 10, "duration_seconds": 40,
        "description": "Improves shoulder blade mechanics and overhead reach.",
        "description_hi": "कंधे की हड्डी की गति और ऊपर पहुँचने की क्षमता सुधारता है।",
        "steps": [
            "Stand with your back and arms against a wall.",
            "Bend the elbows to about 90 degrees, like a goalpost.",
            "Slide your arms up the wall, keeping wrists in contact.",
            "Slide back down slowly to the start.",
        ],
        "steps_hi": [
            "पीठ और हाथ दीवार से सटाकर खड़े हों।",
            "कोहनियाँ लगभग 90 डिग्री मोड़ें, गोलपोस्ट जैसी स्थिति।",
            "कलाइयाँ दीवार से सटाए रखते हुए हाथ ऊपर सरकाएँ।",
            "धीरे-धीरे वापस नीचे लाएँ।",
        ],
        "mistakes": ["Letting the lower back arch off the wall",
                     "Shrugging the shoulders up towards the ears"],
        "mistakes_hi": ["कमर का दीवार से हटकर मुड़ जाना",
                        "कंधों को कानों की ओर उठा लेना"],
        "camera_view": "front",
        "pose": {
            "primary_angle": [L_HIP, L_SHOULDER, L_ELBOW],
            "primary_angle_mirror": [R_HIP, R_SHOULDER, R_ELBOW],
            "primary_joint": "shoulder",
            "mode": "range", "rep_low": 95, "rep_high": 140,
            "cue_en": "Slide the arms up, keep wrists on the wall",
            "cue_hi": "हाथ ऊपर सरकाएँ, कलाइयाँ दीवार पर रखें",
            "form_rules": [NO_SHRUG],
        },
        "preview": frames(
            {**STANDING, "arm": 242, "forearm": 292, "arm_far": 118, "forearm_far": 68},
            {**STANDING, "arm": 288, "forearm": 310, "arm_far": 72, "forearm_far": 50},
        ),
    },
    {
        "slug": "shoulder-flexion", "name": "Shoulder Flexion Raise",
        "name_hi": "शोल्डर फ्लेक्शन रेज़", "category": "shoulder",
        "body_part": "Front of Shoulder",
        "difficulty": "easy", "target_reps": 12, "duration_seconds": 40,
        "description": "Rebuilds the ability to reach forward and overhead.",
        "description_hi": "आगे और सिर के ऊपर हाथ उठाने की क्षमता वापस लाता है।",
        "steps": [
            "Stand tall with your arm hanging by your side.",
            "Raise the straight arm forward and up towards overhead.",
            "Go only as high as is comfortable, with no shrugging.",
            "Lower the arm back down slowly.",
        ],
        "steps_hi": [
            "सीधे खड़े हों, हाथ बगल में लटका रहे।",
            "सीधा हाथ आगे से ऊपर सिर की ओर उठाएँ।",
            "जितना आराम से हो सके उतना ही उठाएँ, कंधा न उचकाएँ।",
            "हाथ धीरे-धीरे नीचे लाएँ।",
        ],
        "mistakes": ["Bending the elbow to cheat the range",
                     "Leaning backwards as the arm rises"],
        "mistakes_hi": ["गति बढ़ाने के लिए कोहनी मोड़ लेना",
                        "हाथ उठाते समय पीछे की ओर झुकना"],
        "camera_view": "side",
        "pose": {
            "primary_angle": [L_HIP, L_SHOULDER, L_ELBOW],
            "primary_angle_mirror": [R_HIP, R_SHOULDER, R_ELBOW],
            "primary_joint": "shoulder",
            "mode": "range", "rep_low": 40, "rep_high": 145,
            "cue_en": "Raise the straight arm forward and up",
            "cue_hi": "सीधा हाथ आगे से ऊपर उठाएँ",
            "form_rules": [ELBOW_STRAIGHT, NO_SHRUG],
        },
        "preview": frames(
            STANDING,
            {**STANDING, "arm": 22, "forearm": 22},
        ),
    },
    {
        "slug": "shoulder-abduction", "name": "Shoulder Abduction Raise",
        "name_hi": "शोल्डर अब्डक्शन रेज़", "category": "shoulder",
        "body_part": "Side of Shoulder",
        "difficulty": "easy", "target_reps": 12, "duration_seconds": 40,
        "description": "Restores the sideways reach used for dressing and lifting.",
        "description_hi": "कपड़े पहनने और सामान उठाने में उपयोगी बगल की गति लौटाता है।",
        "steps": [
            "Stand tall with both arms by your sides.",
            "Raise your arms out to the sides, palms facing down.",
            "Stop at shoulder height or slightly above.",
            "Lower the arms back down under control.",
        ],
        "steps_hi": [
            "सीधे खड़े हों, दोनों हाथ बगल में रखें।",
            "हाथ बगल की ओर उठाएँ, हथेलियाँ नीचे की ओर।",
            "कंधे की ऊँचाई या थोड़ा ऊपर तक ही जाएँ।",
            "हाथ नियंत्रण के साथ नीचे लाएँ।",
        ],
        "mistakes": ["Shrugging the shoulders towards the ears",
                     "Using momentum to swing the arms up"],
        "mistakes_hi": ["कंधों को कानों की ओर उचकाना",
                        "झटके से हाथ ऊपर उछालना"],
        "camera_view": "front",
        "pose": {
            "primary_angle": [L_HIP, L_SHOULDER, L_ELBOW],
            "primary_angle_mirror": [R_HIP, R_SHOULDER, R_ELBOW],
            "primary_joint": "shoulder",
            "mode": "range", "rep_low": 40, "rep_high": 135,
            "cue_en": "Arms out to the sides, stop at shoulder height",
            "cue_hi": "हाथ बगल में उठाएँ, कंधे की ऊँचाई पर रोकें",
            "form_rules": [ELBOW_STRAIGHT, NO_SHRUG],
        },
        "preview": frames(
            {**STANDING, "arm": 190, "forearm": 190, "arm_far": 170, "forearm_far": 170},
            {**STANDING, "arm": 282, "forearm": 282, "arm_far": 78, "forearm_far": 78},
        ),
    },

    # ══════════════════════════ NECK ══════════════════════════
    {
        "slug": "chin-tuck", "name": "Cervical Chin Tuck",
        "name_hi": "सर्वाइकल चिन टक", "category": "neck", "body_part": "Cervical Spine",
        "difficulty": "easy", "target_reps": 10, "duration_seconds": 30,
        "description": "Corrects forward head posture and eases neck strain.",
        "description_hi": "सिर आगे झुकने की आदत सुधारता है और गर्दन का तनाव कम करता है।",
        "steps": [
            "Sit or stand tall, looking straight ahead.",
            "Draw your chin straight back, making a double chin.",
            "Keep your eyes level - do not nod downward.",
            "Hold for three seconds, then release.",
        ],
        "steps_hi": [
            "सीधे बैठें या खड़े हों, सामने देखें।",
            "ठोड़ी सीधे पीछे खींचें, जिससे दोहरी ठोड़ी बने।",
            "आँखें सीधी रखें - सिर नीचे न झुकाएँ।",
            "तीन सेकंड रोकें, फिर छोड़ें।",
        ],
        "mistakes": ["Tilting the head down instead of gliding it back",
                     "Tensing the jaw and shoulders"],
        "mistakes_hi": ["सिर पीछे खिसकाने के बजाय नीचे झुका लेना",
                        "जबड़े और कंधों में तनाव लाना"],
        "camera_view": "side",
        "pose": {
            "primary_angle": [L_EAR, L_SHOULDER, L_HIP],
            "primary_angle_mirror": [R_EAR, R_SHOULDER, R_HIP],
            "primary_joint": "neck",
            "mode": "range", "rep_low": 155, "rep_high": 171,
            "cue_en": "Chin straight back, eyes level",
            "cue_hi": "ठोड़ी सीधे पीछे, आँखें सीधी",
            "form_rules": [],
        },
        "preview": frames(
            {**STANDING, "head": 26},
            {**STANDING, "head": 2},
        ),
    },
    {
        "slug": "neck-rotation", "name": "Cervical Rotation",
        "name_hi": "सर्वाइकल रोटेशन", "category": "neck", "body_part": "Neck Muscles",
        "difficulty": "easy", "target_reps": 10, "duration_seconds": 30,
        "description": "Restores the range needed to check over your shoulder.",
        "description_hi": "कंधे के ऊपर से पीछे देखने की गति सीमा वापस लाता है।",
        "steps": [
            "Sit tall with your shoulders relaxed and still.",
            "Turn your head slowly to look over one shoulder.",
            "Stop where you feel a stretch, not pain.",
            "Return to centre, then turn to the other side.",
        ],
        "steps_hi": [
            "सीधे बैठें, कंधे ढीले और स्थिर रखें।",
            "सिर धीरे-धीरे घुमाकर एक कंधे के ऊपर से देखें।",
            "जहाँ खिंचाव महसूस हो वहीं रुकें, दर्द तक न जाएँ।",
            "बीच में वापस आएँ, फिर दूसरी ओर घुमाएँ।",
        ],
        "mistakes": ["Turning the shoulders along with the head",
                     "Jerking quickly to the end of the range"],
        "mistakes_hi": ["सिर के साथ कंधे भी घुमा देना",
                        "झटके से अंतिम सीमा तक जाना"],
        "camera_view": "front",
        "pose": {
            # Rotation is rigid about the neck axis, so no three-point joint
            # angle changes. Measure the ear line turning against the
            # shoulder line instead -- that IS the rotation.
            "angle_type": "axis",
            "axis_a": [L_EAR, R_EAR],
            "axis_b": [L_SHOULDER, R_SHOULDER],
            "primary_angle": [L_EAR, NOSE, R_EAR],       # fallback for old clients
            "primary_joint": "neck",
            "mode": "range", "rep_low": 12, "rep_high": 40,
            "cue_en": "Turn the head slowly, keep the shoulders still",
            "cue_hi": "सिर धीरे घुमाएँ, कंधे स्थिर रखें",
            "form_rules": [],
        },
        "preview": frames(
            {**SEATED, "head": 350},
            {**SEATED, "head": 10},
        ),
    },
    {
        "slug": "neck-lateral-flexion", "name": "Neck Side Bend",
        "name_hi": "गर्दन बगल में झुकाना", "category": "neck",
        "body_part": "Neck & Upper Traps",
        "difficulty": "easy", "target_reps": 10, "duration_seconds": 30,
        "description": "Stretches the upper trapezius and eases one-sided stiffness.",
        "description_hi": "ऊपरी ट्रैपेज़ियस खींचता है और एक तरफ़ की जकड़न कम करता है।",
        "steps": [
            "Sit tall with both shoulders relaxed and down.",
            "Tilt your head, bringing one ear towards that shoulder.",
            "Keep your nose facing forward - do not turn the head.",
            "Return to centre and repeat on the other side.",
        ],
        "steps_hi": [
            "सीधे बैठें, दोनों कंधे ढीले और नीचे रखें।",
            "सिर झुकाएँ, एक कान उसी कंधे की ओर लाएँ।",
            "नाक सामने की ओर ही रखें - सिर घुमाएँ नहीं।",
            "बीच में लौटें और दूसरी ओर दोहराएँ।",
        ],
        "mistakes": ["Lifting the shoulder up to meet the ear",
                     "Rotating the head instead of tilting it"],
        "mistakes_hi": ["कान से मिलाने के लिए कंधा ऊपर उठाना",
                        "सिर झुकाने के बजाय घुमा देना"],
        "camera_view": "front",
        "pose": {
            "primary_angle": [L_EAR, L_SHOULDER, L_HIP],
            "primary_angle_mirror": [R_EAR, R_SHOULDER, R_HIP],
            "primary_joint": "neck",
            "mode": "range", "rep_low": 148, "rep_high": 166,
            "cue_en": "Ear towards the shoulder, keep the shoulder down",
            "cue_hi": "कान कंधे की ओर, कंधा नीचे रखें",
            "form_rules": [NO_SHRUG],
        },
        "preview": frames(
            SEATED,
            {**SEATED, "head": 328},
        ),
    },

    # ══════════════════════════ POSTURE ══════════════════════════
    {
        "slug": "posture-row", "name": "Scapular Row",
        "name_hi": "स्कैपुलर रो", "category": "posture", "body_part": "Mid Back & Traps",
        "difficulty": "easy", "target_reps": 12, "duration_seconds": 40,
        "description": "Strengthens the mid-back muscles that hold you upright.",
        "description_hi": "सीधा बैठने-खड़े होने में मदद करने वाली मध्य-पीठ मांसपेशियाँ मजबूत करता है।",
        "steps": [
            "Stand tall with both arms reaching forward.",
            "Pull your elbows straight back past your ribs.",
            "Squeeze your shoulder blades together at the end.",
            "Reach forward again slowly and repeat.",
        ],
        "steps_hi": [
            "सीधे खड़े हों, दोनों हाथ आगे की ओर बढ़ाएँ।",
            "कोहनियाँ सीधे पीछे, पसलियों से पार खींचें।",
            "अंत में कंधे की हड्डियाँ आपस में दबाएँ।",
            "फिर धीरे-धीरे हाथ आगे बढ़ाएँ और दोहराएँ।",
        ],
        "mistakes": ["Shrugging the shoulders up instead of back",
                     "Leaning the torso backwards to pull harder"],
        "mistakes_hi": ["कंधों को पीछे के बजाय ऊपर उठाना",
                        "ज़्यादा खींचने के लिए शरीर पीछे झुकाना"],
        "camera_view": "front",
        "pose": {
            # The scapular squeeze itself is not visible to MediaPipe; the arm
            # pull that drives it is, so that is what gets counted.
            "primary_angle": [L_SHOULDER, L_ELBOW, L_WRIST],
            "primary_angle_mirror": [R_SHOULDER, R_ELBOW, R_WRIST],
            "primary_joint": "elbow",
            "mode": "range", "rep_low": 88, "rep_high": 150,
            "cue_en": "Elbows back, squeeze the shoulder blades",
            "cue_hi": "कोहनियाँ पीछे, कंधे की हड्डियाँ दबाएँ",
            "form_rules": [NO_SHRUG],
        },
        "preview": frames(
            {**STANDING, "arm": 108, "forearm": 96, "arm_far": 108, "forearm_far": 96},
            {**STANDING, "arm": 196, "forearm": 96, "arm_far": 196, "forearm_far": 96},
        ),
    },
    {
        "slug": "thoracic-ext", "name": "Thoracic Extension",
        "name_hi": "थोरैसिक एक्सटेंशन", "category": "posture", "body_part": "Thoracic Spine",
        "difficulty": "medium", "target_reps": 10, "duration_seconds": 35,
        "description": "Opens the upper back to reduce rounding and shoulder tension.",
        "description_hi": "ऊपरी पीठ खोलकर कूबड़ और कंधे का तनाव कम करता है।",
        "steps": [
            "Sit on a chair with the backrest at mid-back height.",
            "Support your head with your hands behind it.",
            "Lean back over the chair edge, opening your chest.",
            "Return upright slowly and repeat.",
        ],
        "steps_hi": [
            "ऐसी कुर्सी पर बैठें जिसकी पीठ मध्य-पीठ तक आती हो।",
            "हाथ सिर के पीछे रखकर सिर को सहारा दें।",
            "कुर्सी के किनारे के ऊपर पीछे झुकें, छाती खोलें।",
            "धीरे-धीरे सीधे बैठें और दोहराएँ।",
        ],
        "mistakes": ["Bending from the lower back instead of the upper back",
                     "Pulling the head forward with the hands"],
        "mistakes_hi": ["ऊपरी पीठ के बजाय कमर से झुकना",
                        "हाथों से सिर आगे खींचना"],
        "camera_view": "side",
        "pose": {
            "primary_angle": [L_SHOULDER, L_HIP, L_KNEE],
            "primary_angle_mirror": [R_SHOULDER, R_HIP, R_KNEE],
            "primary_joint": "spine",
            "mode": "range", "rep_low": 95, "rep_high": 114,
            "cue_en": "Open the chest and extend back over the support",
            "cue_hi": "छाती खोलें और सहारे के ऊपर पीछे झुकें",
            "form_rules": [],
        },
        "preview": frames(
            {**SEATED, "arm": 320, "forearm": 250},
            {**SEATED, "torso": 336, "head": 322, "arm": 296, "forearm": 226},
        ),
    },
]

BY_SLUG = {e["slug"]: e for e in EXERCISES}
POSE_CONFIGS = {e["slug"]: e["pose"] for e in EXERCISES}

CATEGORIES = ["back", "knee", "hip", "shoulder", "neck", "posture"]


def pose_config(slug: str) -> dict | None:
    return POSE_CONFIGS.get(slug)
