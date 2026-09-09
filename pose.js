/* =====================================================
   PhysioMind AI - live pose tracking

   Runs MediaPipe Pose in the browser. Video frames NEVER leave this device;
   only the 33 keypoint coordinates are collected, and only those get sent to
   the server when the session ends.

   The rep thresholds and form rules come from the server
   (/api/exercises/{slug}/pose-config) so the clinical knowledge lives in one
   place. This file only executes them for the live HUD -- the server re-runs
   the same rules over the full timeline and its score is the one that is
   saved.
   ===================================================== */

import {
  FilesetResolver,
  PoseLandmarker,
  DrawingUtils,
} from 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.18';

const WASM_PATH =
  'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.18/wasm';
const MODEL_PATH =
  'https://storage.googleapis.com/mediapipe-models/pose_landmarker/' +
  'pose_landmarker_lite/float16/1/pose_landmarker_lite.task';

// Must match backend/physio/pose.py or the HUD and the saved score disagree.
const MIN_DWELL_FRAMES = 2;
const MIN_VISIBILITY = 0.5;
const FORM_RULE_GRACE_FRAMES = 8;   // ignore a brief breach before nagging

// Must match MAX_SESSION_FRAMES in backend/config.py. Recording past it would
// earn a 413 on submit and throw away the patient's entire session, so stop
// and bank what we have instead. 3 minutes at 30fps.
const MAX_FRAMES = 5400;

let landmarker = null;
let loadingPromise = null;

/** Load the model once and reuse it across sessions. */
function ensureLandmarker() {
  if (landmarker) return Promise.resolve(landmarker);
  if (loadingPromise) return loadingPromise;

  loadingPromise = (async () => {
    const vision = await FilesetResolver.forVisionTasks(WASM_PATH);
    landmarker = await PoseLandmarker.createFromOptions(vision, {
      baseOptions: { modelAssetPath: MODEL_PATH, delegate: 'GPU' },
      runningMode: 'VIDEO',
      numPoses: 1,
      minPoseDetectionConfidence: 0.5,
      minPosePresenceConfidence: 0.5,
      minTrackingConfidence: 0.5,
    });
    return landmarker;
  })();

  // A failed load must not poison every later attempt.
  loadingPromise.catch(() => { loadingPromise = null; });
  return loadingPromise;
}

/**
 * Joint angle IN THE IMAGE PLANE. z is dropped on purpose — MediaPipe's depth
 * is a monocular guess that compresses extension by 10-15 degrees (a straight
 * knee measures 165 in 3D, 180 in 2D) and is noticeably noisier. Each exercise
 * already tells the patient which way to face, so the movement is in this
 * plane. Must stay identical to joint_angle() in backend/physio/pose.py.
 */
function angle(a, b, c) {
  const bax = a.x - b.x, bay = a.y - b.y;
  const bcx = c.x - b.x, bcy = c.y - b.y;
  const dot = bax * bcx + bay * bcy;
  const magA = Math.hypot(bax, bay);
  const magC = Math.hypot(bcx, bcy);
  if (magA === 0 || magC === 0) return NaN;
  const cos = Math.min(1, Math.max(-1, dot / (magA * magC)));
  return (Math.acos(cos) * 180) / Math.PI;
}

function angleFrom(landmarks, [i, j, k], visSource) {
  const a = landmarks[i], b = landmarks[j], c = landmarks[k];
  if (!a || !b || !c) return NaN;
  const v = visSource || landmarks;
  const vis = Math.min(v[i]?.visibility ?? 1, v[j]?.visibility ?? 1, v[k]?.visibility ?? 1);
  if (vis < MIN_VISIBILITY) return NaN;
  return angle(a, b, c);
}

/** Angle between two lines. Needed for rotation, which bends no joint. */
function axisAngleFrom(landmarks, [p1, p2], [q1, q2], visSource) {
  const a = landmarks[p1], b = landmarks[p2], c = landmarks[q1], d = landmarks[q2];
  if (!a || !b || !c || !d) return NaN;
  const v = visSource || landmarks;
  const vis = Math.min(v[p1]?.visibility ?? 1, v[p2]?.visibility ?? 1,
                       v[q1]?.visibility ?? 1, v[q2]?.visibility ?? 1);
  if (vis < MIN_VISIBILITY) return NaN;

  const u = [b.x - a.x, b.y - a.y, (b.z ?? 0) - (a.z ?? 0)];
  const w = [d.x - c.x, d.y - c.y, (d.z ?? 0) - (c.z ?? 0)];
  const dot = u[0] * w[0] + u[1] * w[1] + u[2] * w[2];
  const mag = Math.hypot(...u) * Math.hypot(...w);
  if (mag === 0) return NaN;
  const deg = (Math.acos(Math.min(1, Math.max(-1, dot / mag))) * 180) / Math.PI;
  return Math.min(deg, 180 - deg);       // undirected: left turn == right turn
}

/**
 * Drives one exercise session.
 *
 * @param {object} opts
 *   video      - <video> element to attach the webcam to
 *   canvas     - <canvas> overlay for the skeleton
 *   config     - pose config from the API
 *   lang       - 'en' | 'hi'
 *   onUpdate   - ({reps, quality, seconds, feedback, tone}) each frame
 *   onComplete - (frames) when the target rep count is reached
 */
export function createSession({ video, canvas, config, lang, onUpdate, onComplete }) {
  const ctx = canvas.getContext('2d');
  const drawer = new DrawingUtils(ctx);
  const frames = [];

  let stream = null;
  let rafId = null;
  let running = false;
  let lastVideoTime = -1;
  let startedAt = 0;
  let finished = false;

  // rep state
  let reps = 0;
  let state = 'high';
  let lowRun = 0;
  let highRun = 0;
  let holdStart = null;
  let holdArmed = true;

  // Live calibration. Fixed anatomical cutoffs are unreachable for a stiff
  // joint, and a chin tuck only travels ~15 degrees in total, so the
  // thresholds move inside the range this patient actually demonstrates.
  // Mirrors _adaptive_thresholds() in backend/physio/pose.py.
  const MIN_MOVEMENT_RANGE = 10;
  const REP_LOW_FRACTION = 0.30;
  const REP_HIGH_FRACTION = 0.70;
  let seenMin = Infinity;
  let seenMax = -Infinity;
  let calibrated = false;

  // form state
  const breachRuns = new Map();
  let liveFeedback = null;
  let trackedFrames = 0;
  let totalFrames = 0;

  // Which side the patient is actually working. Chosen once from the first
  // few seconds of movement, then held: flipping sides mid-set would reset
  // the rep state machine and lose the count.
  const SIDE_LOCK_FRAMES = 45;
  let side = null;
  const sideRange = {
    left:  { min: Infinity, max: -Infinity, seen: 0 },
    right: { min: Infinity, max: -Infinity, seen: 0 },
  };

  const t = (en, hi) => (lang === 'hi' ? hi : en);

  /** Track both limbs until it is clear which one is moving, then commit. */
  function primaryAngle(source, visSource) {
    if (config.angle_type === 'axis') {
      return axisAngleFrom(source, config.axis_a, config.axis_b, visSource);
    }
    if (!config.primary_angle_mirror) {
      return angleFrom(source, config.primary_angle, visSource);
    }

    const left = angleFrom(source, config.primary_angle, visSource);
    const right = angleFrom(source, config.primary_angle_mirror, visSource);

    if (side) return side === 'right' ? right : left;

    for (const [key, value] of [['left', left], ['right', right]]) {
      if (Number.isNaN(value)) continue;
      const r = sideRange[key];
      r.min = Math.min(r.min, value);
      r.max = Math.max(r.max, value);
      r.seen++;
    }

    if (totalFrames >= SIDE_LOCK_FRAMES) {
      const spread = k => (sideRange[k].seen ? sideRange[k].max - sideRange[k].min : -1);
      side = spread('right') > spread('left') ? 'right' : 'left';
    }
    // Before the lock, follow whichever side has moved more so far.
    const leftSpread = sideRange.left.seen ? sideRange.left.max - sideRange.left.min : -1;
    const rightSpread = sideRange.right.seen ? sideRange.right.max - sideRange.right.min : -1;
    return rightSpread > leftSpread ? right : left;
  }

  function ruleAngle(source, rule, visSource) {
    const near = angleFrom(source, rule.angle, visSource);
    if (!rule.mirror) return near;
    const far = angleFrom(source, rule.mirror, visSource);
    if (Number.isNaN(near)) return far;
    if (Number.isNaN(far)) return near;
    // Judge the limb being exercised, matching the server.
    return side === 'right' ? far : near;
  }

  async function start() {
    await ensureLandmarker();

    stream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' },
      audio: false,
    });
    video.srcObject = stream;
    await video.play();

    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;

    running = true;
    startedAt = performance.now();
    rafId = requestAnimationFrame(loop);
  }

  function loop() {
    if (!running) return;

    if (video.currentTime !== lastVideoTime && video.readyState >= 2) {
      lastVideoTime = video.currentTime;
      const now = performance.now();
      let result = null;
      try {
        result = landmarker.detectForVideo(video, now);
      } catch {
        // A dropped frame is not fatal; keep the loop alive.
      }
      if (result) handleResult(result, now - startedAt);
    }
    rafId = requestAnimationFrame(loop);
  }

  function handleResult(result, elapsedMs) {
    const pose = result.landmarks && result.landmarks[0];
    const world = result.worldLandmarks && result.worldLandmarks[0];
    totalFrames++;

    ctx.save();
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (!pose) {
      ctx.restore();
      emit(elapsedMs, t('Step back so your whole body is visible',
                        'पीछे हटें ताकि पूरा शरीर दिखे'), 'warn');
      return;
    }

    drawer.drawConnectors(pose, PoseLandmarker.POSE_CONNECTIONS,
                          { color: '#0ea5a4', lineWidth: 3 });
    drawer.drawLandmarks(pose, { color: '#6366f1', radius: 3 });
    ctx.restore();

    // Image-space landmarks, NOT world. Their x/y are what the joint-angle
    // maths wants, and their z (same normalised scale) still serves the
    // rotation metric. World landmarks were tried first and measured worse:
    // their depth estimate squashes every extension angle by 10-15 degrees,
    // which put targets like a 174-degree straight knee permanently out of
    // reach and left the rep counter stuck on zero.
    const source = pose;

    frames.push({
      t: Math.round(elapsedMs),
      lm: source.map(p => [
        +p.x.toFixed(4), +p.y.toFixed(4), +(p.z ?? 0).toFixed(4),
        +(p.visibility ?? 1).toFixed(3),
      ]),
    });

    const primary = primaryAngle(source, pose);
    if (!Number.isNaN(primary)) trackedFrames++;

    updateReps(primary, elapsedMs);
    const formIssue = checkForm(source, pose);

    let message, tone;
    if (Number.isNaN(primary)) {
      message = t('Adjust position - key joints are hidden',
                  'स्थिति ठीक करें - मुख्य जोड़ दिखाई नहीं दे रहे');
      tone = 'warn';
    } else if (formIssue) {
      message = formIssue;
      tone = 'warn';
    } else if (config.mode !== 'hold' && !calibrated) {
      // Say what is happening rather than showing a counter stuck on zero.
      message = t('Calibrating - do one slow, full repetition',
                  'कैलिब्रेट हो रहा है - एक धीमा, पूरा दोहराव करें');
      tone = 'good';
    } else {
      message = liveFeedback || (lang === 'hi' ? config.cue_hi : config.cue_en);
      tone = 'good';
    }
    emit(elapsedMs, message, tone);

    // Target reached, or the recording buffer is full. Either way, bank the
    // session rather than let it grow into a request the server will reject.
    if (!finished && (reps >= config.target_reps || frames.length >= MAX_FRAMES)) {
      finished = true;
      if (reps < config.target_reps) {
        emit(elapsedMs, t('Time limit reached - saving your session',
                          'समय सीमा पूरी - आपका सत्र सहेजा जा रहा है'), 'warn');
      }
      stop();
      onComplete(frames);
    }
  }

  function updateReps(primary, elapsedMs) {
    if (Number.isNaN(primary)) { lowRun = 0; highRun = 0; return; }

    if (config.mode === 'hold') {
      // A hold targets an absolute clinical position, so it keeps the
      // configured band. Re-arming only after release stops a patient who is
      // simply resting inside the band from scoring a rep every few seconds.
      const inside = primary >= config.rep_low && primary <= config.rep_high;
      if (!inside) { holdStart = null; holdArmed = true; return; }
      if (!holdArmed) return;
      if (holdStart === null) holdStart = elapsedMs;
      if (elapsedMs - holdStart >= (config.hold_seconds ?? 3) * 1000) {
        reps++;
        holdStart = null;
        holdArmed = false;
        liveFeedback = t('Hold complete - relax', 'होल्ड पूरा - आराम करें');
      }
      return;
    }

    seenMin = Math.min(seenMin, primary);
    seenMax = Math.max(seenMax, primary);
    const span = seenMax - seenMin;

    // Use the configured band until the patient has shown enough travel to
    // calibrate against, then switch to their own range.
    let low = config.rep_low, high = config.rep_high;
    if (span >= MIN_MOVEMENT_RANGE) {
      calibrated = true;
      low = seenMin + REP_LOW_FRACTION * span;
      high = seenMin + REP_HIGH_FRACTION * span;
    }

    if (primary <= low) { lowRun++; highRun = 0; }
    else if (primary >= high) { highRun++; lowRun = 0; }
    else { lowRun = 0; highRun = 0; }

    if (state === 'high' && lowRun >= MIN_DWELL_FRAMES) {
      state = 'low';
      liveFeedback = t('Good depth - now return slowly',
                       'अच्छी गहराई - अब धीरे वापस आएँ');
    } else if (state === 'low' && highRun >= MIN_DWELL_FRAMES) {
      state = 'high';
      reps++;
      liveFeedback = t('Rep complete - well done', 'दोहराव पूरा - बहुत अच्छे');
    }
  }

  /** Returns a message for the first rule breached long enough to matter. */
  function checkForm(landmarks, visSource) {
    for (const rule of config.form_rules || []) {
      const value = ruleAngle(landmarks, rule, visSource);
      if (Number.isNaN(value)) continue;
      const breached =
        (rule.min !== undefined && value < rule.min) ||
        (rule.max !== undefined && value > rule.max);

      const run = (breachRuns.get(rule.id) || 0);
      breachRuns.set(rule.id, breached ? run + 1 : 0);

      if (breached && run + 1 >= FORM_RULE_GRACE_FRAMES) {
        return lang === 'hi' ? rule.msg_hi : rule.msg_en;
      }
    }
    return null;
  }

  function emit(elapsedMs, feedback, tone) {
    onUpdate({
      reps,
      target: config.target_reps,
      seconds: Math.floor(elapsedMs / 1000),
      quality: totalFrames ? Math.round((trackedFrames / totalFrames) * 100) : 0,
      feedback,
      tone,
    });
  }

  function stop() {
    running = false;
    if (rafId) cancelAnimationFrame(rafId);
    if (stream) {
      // Releasing every track is what actually turns the camera light off.
      stream.getTracks().forEach(track => track.stop());
      stream = null;
    }
    video.srcObject = null;
  }

  return {
    start,
    stop,
    getFrames: () => frames,
    getReps: () => reps,
  };
}

// app.js is a classic script, so hand it the entry points on window.
window.PhysioPose = { createSession, ensureLandmarker };
window.dispatchEvent(new Event('physio-pose-ready'));
