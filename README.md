# PhysioMind AI

Digital physiotherapy app: describe your symptoms, get a likely condition and a
recovery plan, then practise each exercise in front of your camera while pose
tracking counts reps and corrects your form.

- **Frontend** — vanilla JS SPA (`index.html`, `app.js`, `api.js`, `pose.js`, `preview.js`, `styles.css`)
- **Backend** — Python / FastAPI + SQLite (`backend/`)
- **Pose tracking** — MediaPipe Pose, running **in the browser**

## Run it

```bash
python -m venv .venv && .venv/Scripts/python.exe -m pip install -r requirements.txt
```

```bash
.venv/Scripts/python.exe -m uvicorn backend.main:app --reload --port 8000
```

Open <http://127.0.0.1:8000>. FastAPI serves the frontend and the API from the
same port, so there is nothing else to start.

Interactive API docs: <http://127.0.0.1:8000/docs>

```bash
.venv/Scripts/python.exe -m pytest
```

## How the pose tracking is split

Video **never leaves the device**. The browser runs MediaPipe, extracts 33 body
keypoints per frame, and evaluates the rules for the live on-screen feedback.
When the session ends it uploads only the coordinate timeline — numbers, no
images — and the server recomputes the authoritative score.

```
browser                                    server
-------                                    ------
webcam -> MediaPipe -> 33 keypoints        GET /api/exercises/{slug}/pose-config
             |                                  |  joint triplets, rep thresholds,
             |  <-------------------------------+  form rules  (clinical truth)
             |
        live HUD (reps, cues)
             |
        POST /api/sessions  { frames: [...] } --> joint angles (numpy)
                                                  rep counting
                                                  range of motion
                                                  form-rule violations
                                                  quality score
```

Both sides run the *same* rules from the *same* source, so the live HUD and the
saved result cannot disagree. The server's number is the one that is stored.

## API

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/api/auth/signup` | – | Create account (bcrypt + JWT) |
| POST | `/api/auth/login` | – | Log in |
| GET | `/api/auth/me` | ✓ | Current user |
| GET | `/api/exercises` | – | Catalogue (22 exercises), `?category=` filter |
| GET | `/api/exercises/{slug}/pose-config` | – | Biomechanics rules for the browser |
| POST | `/api/assess` | optional | Symptoms → condition + confidence |
| GET | `/api/assessments` | ✓ | Assessment history |
| POST | `/api/plans` | ✓ | Generate plan from latest assessment |
| GET | `/api/plans/active` | ✓ | Current plan |
| POST | `/api/sessions` | ✓ | Submit keypoint timeline, get scored (returns `adaptive`, `target_met`) |
| GET | `/api/sessions` | ✓ | Session history |
| GET | `/api/analytics` | ✓ | Trends, streak, common form errors |
| POST | `/api/reports` | optional | Upload MRI/X-ray, extract findings |

## Configuration

All optional in development; `PHYSIO_SECRET_KEY` is **required** in production.

| Variable | Default | Notes |
|---|---|---|
| `PHYSIO_SECRET_KEY` | random per restart | JWT signing key. Set it in production or the app refuses to start. |
| `PHYSIO_ENV` | `dev` | Set to `production` to enforce the above and hide error details. |
| `PHYSIO_DATABASE_URL` | `sqlite:///backend/physio.db` | Any SQLAlchemy URL. |
| `PHYSIO_UPLOAD_DIR` | `./uploads` | Where medical reports are stored. |
| `PHYSIO_CORS_ORIGINS` | *(none)* | Comma-separated. Only needed if you serve the frontend elsewhere. |

Generate a production key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Exercise catalogue

22 exercises across six categories: back, knee, hip, shoulder, neck, posture.
Each one carries its own biomechanics config, step-by-step instructions in both
languages, common mistakes, and an animated stick-figure preview.

Open `exercise-previews.html` to see every preview keyframe on one page.

### How detection works per exercise

Three things decide whether an exercise is detected reliably:

**1. Bilateral tracking.** `primary_angle` is the left side and
`primary_angle_mirror` the right. The analyser measures both and follows the
side that actually *moved* — not the side that is most visible, because a
resting limb is perfectly visible and perfectly useless. Without this, a
patient working their right leg scores zero.

**2. Camera view.** `camera_view` is `side` or `front`. A sagittal movement
(leg raise, chin tuck) is almost flat when viewed head-on and cannot be
measured from there. The preview tells the patient where to stand; getting
this wrong is the most common reason a real session records nothing.

**3. Measured in the image plane, not 3D.** MediaPipe returns both image and
"world" landmarks. World looks better on paper — metric, view-independent —
but its depth is a monocular guess, and measured against real detections it
compresses every extension angle by 10-15 degrees. A fully straight knee reads
**165 degrees in 3D but 180 in 2D**, and two equally straight legs disagree by
6 degrees in 3D versus 3 in 2D. Since each exercise already tells the patient
which way to face, the movement is in the image plane anyway. Rotation is the
one thing 2D cannot see, so `axis_angle` still uses the depth channel.

**4. Thresholds calibrate to the patient.** Fixed anatomical cutoffs assume a
textbook body. A stiff knee that only travels 17 degrees, or a chin tuck that
travels 15 in total, never reaches them — and the patient just sees a counter
stuck on zero. So for range-mode exercises the rep thresholds are placed at
30% and 70% of the range the patient actually demonstrated. The configured
clinical band is still reported against as `target_met`, so a small range is
visible rather than quietly rescaled away. Holds keep absolute thresholds,
because a hold is about reaching a specific clinical position.

If the joint barely moves at all, the session says so explicitly instead of
returning an unexplained zero.

**5. What is actually measurable.** MediaPipe gives 33 landmarks and no spine,
so some movements need a proxy or a different metric entirely:

| Exercise | Measured as | Why |
|---|---|---|
| `neck-rotation` | angle between the ear line and the shoulder line | Head rotation bends no joint — no three-point angle can see it |
| `cat-cow` | head-to-torso angle | There are no spine landmarks; the neck leads both halves of the cycle |
| `posture-row` | elbow angle | The scapular squeeze is invisible; the arm pull that drives it is not |
| `quad-sets`, `wall-sit` | timed hold inside an angle band | Isometric — the joint barely moves, so effort is timed, not measured |

Holds re-arm only after the patient leaves the band, so resting inside it does
not score a rep every few seconds.

## Notes and limitations

- **Angle thresholds in `backend/physio/exercise_data.py` are starting values.**
  They are structured and commented for tuning but have not been validated by a
  physiotherapist against real patients. Do this before any clinical use. The
  four exercises in the proxy table above are the ones most worth reviewing:
  each measures something adjacent to the movement rather than the movement
  itself.
- **Image OCR needs Tesseract** installed separately
  ([Windows build](https://github.com/UB-Mannheim/tesseract/wiki)). PDFs with a
  text layer work with no extra install. When OCR is unavailable the app says so
  rather than inventing findings.
- **The pose model loads from a CDN** (~3 MB, cached after first load), so the
  first session needs an internet connection.
- **Camera requires a secure context.** `localhost` counts; if you serve this on
  a LAN IP you need HTTPS or the browser will block `getUserMedia`.
- Sessions recorded without pose tracking are stored but excluded from quality
  and range-of-motion trends, so simulated data can never inflate the analytics.
- Adding a field to a model auto-adds the SQLite column on startup, so an
  update does not wipe recorded sessions. Renames, type changes and drops
  still need a real migration.

This app provides informational guidance and does not replace assessment by a
licensed physiotherapist.
