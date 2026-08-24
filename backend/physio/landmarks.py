"""MediaPipe Pose landmark indices (33-point BlazePose topology).

Named constants so exercise configs read as anatomy, not magic numbers.
"""

NOSE = 0
L_EAR, R_EAR = 7, 8
L_SHOULDER, R_SHOULDER = 11, 12
L_ELBOW, R_ELBOW = 13, 14
L_WRIST, R_WRIST = 15, 16
L_HIP, R_HIP = 23, 24
L_KNEE, R_KNEE = 25, 26
L_ANKLE, R_ANKLE = 27, 28

LANDMARK_COUNT = 33

NAMES = {
    NOSE: "nose",
    L_EAR: "left_ear", R_EAR: "right_ear",
    L_SHOULDER: "left_shoulder", R_SHOULDER: "right_shoulder",
    L_ELBOW: "left_elbow", R_ELBOW: "right_elbow",
    L_WRIST: "left_wrist", R_WRIST: "right_wrist",
    L_HIP: "left_hip", R_HIP: "right_hip",
    L_KNEE: "left_knee", R_KNEE: "right_knee",
    L_ANKLE: "left_ankle", R_ANKLE: "right_ankle",
}
