/* =====================================================
   PhysioMind AI - exercise preview

   Draws an animated stick figure showing how to perform an exercise, built
   by forward kinematics from the keyframes the API serves. Because the
   keyframes live beside the detection thresholds in the backend catalogue,
   the demonstration and the thing the tracker is looking for cannot drift
   apart.

   Angle convention (matches backend/physio/postures.py):
     0 = up    90 = right    180 = down    270 = left
   ===================================================== */

'use strict';

const Preview = (() => {
  // Segment lengths in the 100x100 viewBox.
  const LEN = { torso: 26, head: 11, upperArm: 15, foreArm: 14, thigh: 19, shin: 18 };
  const CYCLE_MS = 2600;          // one out-and-back movement
  const HEAD_RADIUS = 7;

  const rad = deg => ((deg - 90) * Math.PI) / 180;   // 0 deg = up

  /** Walk `len` from `point` in direction `deg`. */
  function step(point, deg, len) {
    return [point[0] + Math.cos(rad(deg)) * len, point[1] + Math.sin(rad(deg)) * len];
  }

  /** Build every joint coordinate for one pose. */
  function skeleton(p) {
    const hip = p.root;
    const shoulder = step(hip, p.torso, LEN.torso);
    const head = step(shoulder, p.head, LEN.head);

    const build = (armDeg, foreDeg, thighDeg, shinDeg) => {
      const elbow = step(shoulder, armDeg, LEN.upperArm);
      const knee = step(hip, thighDeg, LEN.thigh);
      return {
        elbow,
        wrist: step(elbow, foreDeg, LEN.foreArm),
        knee,
        ankle: step(knee, shinDeg, LEN.shin),
      };
    };

    // The far limbs default to the near ones, which is what you want for a
    // side view where they overlap.
    const near = build(p.arm, p.forearm, p.thigh, p.shin);
    const far = build(
      p.arm_far ?? p.arm,
      p.forearm_far ?? p.forearm,
      p.thigh_far ?? p.thigh,
      p.shin_far ?? p.shin,
    );
    return { hip, shoulder, head, near, far };
  }

  const lerp = (a, b, k) => a + (b - a) * k;

  /** Interpolate two poses. Angles take the shortest way round the circle. */
  function blend(start, end, k) {
    const out = {};
    for (const key of Object.keys(start)) {
      const from = start[key];
      const to = end[key] ?? from;
      if (key === 'root') {
        out[key] = [lerp(from[0], to[0], k), lerp(from[1], to[1], k)];
      } else {
        let delta = ((to - from + 540) % 360) - 180;
        out[key] = from + delta * k;
      }
    }
    // Keyframes may introduce a far limb the start pose did not name.
    for (const key of Object.keys(end)) {
      if (!(key in out)) out[key] = end[key];
    }
    return out;
  }

  const line = (a, b, cls) =>
    `<line x1="${a[0].toFixed(2)}" y1="${a[1].toFixed(2)}" ` +
    `x2="${b[0].toFixed(2)}" y2="${b[1].toFixed(2)}" class="${cls}"/>`;

  function draw(svg, pose) {
    const s = skeleton(pose);
    svg.innerHTML = `
      <line x1="4" y1="88" x2="96" y2="88" class="pv-ground"/>
      <g class="pv-far">
        ${line(s.shoulder, s.far.elbow, 'pv-limb')}
        ${line(s.far.elbow, s.far.wrist, 'pv-limb')}
        ${line(s.hip, s.far.knee, 'pv-limb')}
        ${line(s.far.knee, s.far.ankle, 'pv-limb')}
      </g>
      ${line(s.hip, s.shoulder, 'pv-torso')}
      <g class="pv-near">
        ${line(s.shoulder, s.near.elbow, 'pv-limb')}
        ${line(s.near.elbow, s.near.wrist, 'pv-limb')}
        ${line(s.hip, s.near.knee, 'pv-limb')}
        ${line(s.near.knee, s.near.ankle, 'pv-limb')}
      </g>
      <circle cx="${s.head[0].toFixed(2)}" cy="${s.head[1].toFixed(2)}"
              r="${HEAD_RADIUS}" class="pv-head"/>
      <circle cx="${s.shoulder[0].toFixed(2)}" cy="${s.shoulder[1].toFixed(2)}"
              r="2.4" class="pv-joint"/>
      <circle cx="${s.hip[0].toFixed(2)}" cy="${s.hip[1].toFixed(2)}"
              r="2.4" class="pv-joint"/>
      <circle cx="${s.near.elbow[0].toFixed(2)}" cy="${s.near.elbow[1].toFixed(2)}"
              r="2" class="pv-joint"/>
      <circle cx="${s.near.knee[0].toFixed(2)}" cy="${s.near.knee[1].toFixed(2)}"
              r="2" class="pv-joint"/>
    `;
  }

  /**
   * Animate an exercise into an <svg>. Returns a stop function.
   * Respects prefers-reduced-motion by holding the end pose instead.
   */
  function animate(svg, exercise) {
    const { start, end } = exercise.preview;

    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      draw(svg, end);
      return () => {};
    }

    // Paint one frame up front. requestAnimationFrame does not run in a
    // hidden tab or a throttled window, and without this the preview would
    // sit empty until the browser decides to grant a frame.
    draw(svg, start);

    let raf = null;
    let t0 = null;
    const tick = now => {
      if (t0 === null) t0 = now;
      const phase = ((now - t0) % CYCLE_MS) / CYCLE_MS;
      // Ease in and out so the movement looks controlled, not mechanical.
      const k = (1 - Math.cos(phase * 2 * Math.PI)) / 2;
      draw(svg, blend(start, end, k));
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => { if (raf) cancelAnimationFrame(raf); };
  }

  /** A single static pose, for the small thumbnail on each exercise card. */
  function still(svg, exercise, phase = 'end') {
    draw(svg, exercise.preview[phase]);
  }

  return { animate, still, draw, skeleton, blend };
})();
