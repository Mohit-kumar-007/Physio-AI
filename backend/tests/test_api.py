"""End-to-end API tests against a throwaway database."""

from __future__ import annotations

import math

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from backend.db import get_session
from backend.main import app
from backend.physio import landmarks as L

CREDS = {"name": "Test Patient", "email": "patient@example.com",
         "password": "correct-horse-battery"}


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    """Each test starts with a clean budget; the windows are process-global."""
    from backend.ratelimit import login_window, signup_window

    login_window.reset()
    signup_window.reset()
    yield


@pytest.fixture(name="client")
def client_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    def override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(name="auth")
def auth_fixture(client):
    response = client.post("/api/auth/signup", json=CREDS)
    assert response.status_code == 201, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


# --- health & catalogue -----------------------------------------------------
def test_health(client):
    assert client.get("/api/health").json()["status"] == "ok"


def test_exercise_catalogue(client):
    from backend.physio.exercise_data import EXERCISES

    body = client.get("/api/exercises").json()
    assert body["count"] == len(EXERCISES)
    # The biomechanics config must not leak into the catalogue listing.
    assert "pose" not in body["items"][0]
    # The preview data the UI animates must be there.
    assert body["items"][0]["preview"]["start"]
    assert body["items"][0]["steps"]


def test_category_filter(client):
    from backend.physio.exercise_data import EXERCISES

    expected = sum(1 for e in EXERCISES if e["category"] == "knee")
    body = client.get("/api/exercises?category=knee").json()
    assert body["count"] == expected
    assert all(i["category"] == "knee" for i in body["items"])


def test_every_category_returns_something(client):
    from backend.physio.exercise_data import CATEGORIES

    for category in CATEGORIES:
        body = client.get(f"/api/exercises?category={category}").json()
        assert body["count"] > 0, category


def test_unknown_category_404s(client):
    assert client.get("/api/exercises?category=elbow").status_code == 404


def test_pose_config_available(client):
    body = client.get("/api/exercises/chin-tuck/pose-config").json()
    assert len(body["primary_angle"]) == 3
    assert body["rep_low"] < body["rep_high"]


# --- auth -------------------------------------------------------------------
def test_signup_then_login(client):
    assert client.post("/api/auth/signup", json=CREDS).status_code == 201
    response = client.post("/api/auth/login", json={
        "email": CREDS["email"], "password": CREDS["password"]})
    assert response.status_code == 200
    assert response.json()["user"]["email"] == CREDS["email"]


def test_duplicate_email_rejected(client):
    client.post("/api/auth/signup", json=CREDS)
    assert client.post("/api/auth/signup", json=CREDS).status_code == 409


def test_wrong_password_rejected(client):
    client.post("/api/auth/signup", json=CREDS)
    response = client.post("/api/auth/login", json={
        "email": CREDS["email"], "password": "wrong-password"})
    assert response.status_code == 401


def test_unknown_email_gives_same_error_as_wrong_password(client):
    """Must not reveal whether an account exists."""
    client.post("/api/auth/signup", json=CREDS)
    wrong_pw = client.post("/api/auth/login", json={
        "email": CREDS["email"], "password": "wrong-password"})
    no_user = client.post("/api/auth/login", json={
        "email": "nobody@example.com", "password": "wrong-password"})
    assert wrong_pw.status_code == no_user.status_code == 401
    assert wrong_pw.json()["detail"] == no_user.json()["detail"]


def test_short_password_rejected(client):
    response = client.post("/api/auth/signup", json={**CREDS, "password": "abc"})
    assert response.status_code == 422


def test_password_is_never_returned(client):
    body = client.post("/api/auth/signup", json=CREDS).text
    assert CREDS["password"] not in body
    assert "password_hash" not in body


def test_protected_route_requires_token(client):
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/sessions").status_code == 401
    assert client.get("/api/analytics").status_code == 401


def test_garbage_token_rejected(client):
    response = client.get("/api/auth/me",
                          headers={"Authorization": "Bearer not.a.jwt"})
    assert response.status_code == 401


def test_me_returns_profile(client, auth):
    assert client.get("/api/auth/me", headers=auth).json()["name"] == CREDS["name"]


# --- assessment & plan ------------------------------------------------------
def test_assess_works_logged_out(client):
    response = client.post("/api/assess", json={"text": "my knee hurts on stairs"})
    assert response.status_code == 200
    assert response.json()["category"] == "knee"
    assert response.json()["id"] is None       # not persisted for anonymous users


def test_assess_persists_when_logged_in(client, auth):
    response = client.post("/api/assess", headers=auth,
                           json={"text": "severe lower back pain with sciatica"})
    assert response.json()["id"] is not None
    assert client.get("/api/assessments", headers=auth).json()["items"]


def test_blank_assessment_rejected(client):
    assert client.post("/api/assess", json={"text": "   "}).status_code == 422


def test_plan_requires_an_assessment_first(client, auth):
    assert client.post("/api/plans", headers=auth, json={}).status_code == 404


def test_plan_generation_matches_diagnosis(client, auth):
    client.post("/api/assess", headers=auth, json={"text": "frozen shoulder pain"})
    response = client.post("/api/plans", headers=auth, json={})
    assert response.status_code == 201
    plan = response.json()
    assert plan["category"] == "shoulder"
    content = plan["content"]
    assert content["exercises"] and content["diet"] and content["routine"]
    assert len(content["weeks"]) == 2


def test_only_one_active_plan(client, auth):
    client.post("/api/assess", headers=auth, json={"text": "knee pain"})
    client.post("/api/plans", headers=auth, json={})
    client.post("/api/plans", headers=auth, json={})
    active = [p for p in client.get("/api/plans", headers=auth).json()
              if p["is_active"]]
    assert len(active) == 1


# --- sessions ---------------------------------------------------------------
def make_frames(n_reps: int = 4) -> list[dict]:
    """Synthetic knee-extension timeline the server should score."""
    frames, t = [], 0.0
    def push(angle):
        nonlocal t
        lm = [[0.0, 0.0, 0.0, 1.0] for _ in range(33)]
        rad = math.radians(angle)
        lm[L.L_KNEE] = [0.0, 0.0, 0.0, 1.0]
        lm[L.L_HIP] = [0.0, 1.0, 0.0, 1.0]
        lm[L.L_ANKLE] = [math.sin(rad), math.cos(rad), 0.0, 1.0]
        lm[L.L_SHOULDER] = [0.0, 2.0, 0.0, 1.0]
        frames.append({"t": t, "lm": lm})
        t += 33.3

    for _ in range(10):
        push(178)
    for _ in range(n_reps):
        for step in range(30):
            push(178 - (38 * step / 29))
        for step in range(30):
            push(140 + (38 * step / 29))
    return frames


def test_submit_tracked_session(client, auth):
    response = client.post("/api/sessions", headers=auth, json={
        "exercise_slug": "terminal-knee-ext",
        "frames": make_frames(4),
        "completed": True,
    })
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["reps"] == 4
    assert body["quality"] > 0
    assert body["rom_degrees"] > 10
    assert body["tracked_ratio"] > 0.9


def test_untracked_session_is_flagged(client, auth):
    response = client.post("/api/sessions", headers=auth, json={
        "exercise_slug": "chin-tuck", "frames": [], "client_reps": 10,
        "completed": True,
    })
    body = response.json()
    assert body["reps"] == 10
    assert body["quality"] == 0
    assert body["errors"][0]["id"] == "untracked"


def test_session_without_frames_or_reps_is_rejected(client, auth):
    response = client.post("/api/sessions", headers=auth, json={
        "exercise_slug": "chin-tuck", "frames": []})
    assert response.status_code == 422


def test_unknown_exercise_rejected(client, auth):
    response = client.post("/api/sessions", headers=auth, json={
        "exercise_slug": "moon-walk", "client_reps": 5})
    assert response.status_code == 404


def test_malformed_frame_rejected(client, auth):
    response = client.post("/api/sessions", headers=auth, json={
        "exercise_slug": "chin-tuck",
        "frames": [{"t": 0, "lm": [[0, 0, 0]] * 5}],      # 5 landmarks, not 33
    })
    assert response.status_code == 422


def test_users_cannot_read_each_others_sessions(client, auth):
    created = client.post("/api/sessions", headers=auth, json={
        "exercise_slug": "chin-tuck", "client_reps": 5}).json()

    other = client.post("/api/auth/signup", json={
        "name": "Other", "email": "other@example.com", "password": "another-secret"})
    other_auth = {"Authorization": f"Bearer {other.json()['access_token']}"}

    assert client.get(f"/api/sessions/{created['id']}",
                      headers=other_auth).status_code == 404
    assert client.get("/api/sessions", headers=other_auth).json() == []


# --- analytics --------------------------------------------------------------
def test_analytics_empty_state(client, auth):
    body = client.get("/api/analytics", headers=auth).json()
    assert body["total_sessions"] == 0
    assert body["quality_trend"] == []


def test_analytics_aggregates_tracked_sessions(client, auth):
    for _ in range(3):
        client.post("/api/sessions", headers=auth, json={
            "exercise_slug": "terminal-knee-ext",
            "frames": make_frames(4), "completed": True})
    body = client.get("/api/analytics", headers=auth).json()
    assert body["total_sessions"] == 3
    assert len(body["quality_trend"]) == 3
    assert body["average_quality"] > 0
    assert body["streak_days"] >= 1


def test_untracked_sessions_excluded_from_quality_trend(client, auth):
    client.post("/api/sessions", headers=auth, json={
        "exercise_slug": "chin-tuck", "client_reps": 10})
    body = client.get("/api/analytics", headers=auth).json()
    assert body["total_sessions"] == 1
    assert body["quality_trend"] == []           # no fake quality data
    assert "none had pose tracking" in body["summary"]


# --- uploads ----------------------------------------------------------------
def test_rejects_unsupported_upload_type(client, auth):
    response = client.post("/api/reports", headers=auth, files={
        "file": ("virus.exe", b"MZ\x90\x00", "application/x-msdownload")})
    assert response.status_code == 415


def test_pdf_without_text_layer_reports_honestly(client, auth):
    """A scan-only PDF must say so, not invent findings."""
    minimal_pdf = (
        b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[]/Count 0>>endobj\n"
        b"trailer<</Root 1 0 R>>\n%%EOF"
    )
    response = client.post("/api/reports", headers=auth, files={
        "file": ("scan.pdf", minimal_pdf, "application/pdf")})
    body = response.json()
    assert body["ok"] is False
    assert body["findings"] == []
    assert body["message"]


# --- static frontend --------------------------------------------------------
def test_serves_the_frontend(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "PhysioMind" in response.text


# --- schema migration -------------------------------------------------------
def test_new_columns_are_added_without_dropping_data(tmp_path):
    """Adding a model field must not cost the patient their session history."""
    from sqlalchemy import inspect as sa_inspect
    from sqlmodel import create_engine as mk_engine

    import backend.db as db

    db_path = tmp_path / "old.db"
    engine = mk_engine(f"sqlite:///{db_path}")

    # Build a table that is missing the newest columns, and put a row in it.
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE sessions (
                id INTEGER PRIMARY KEY, user_id INTEGER, exercise_slug VARCHAR,
                exercise_name VARCHAR, reps INTEGER, target_reps INTEGER,
                quality INTEGER, rom_degrees FLOAT, duration_seconds FLOAT,
                tracked_ratio FLOAT, mean_tempo_seconds FLOAT, completed BOOLEAN,
                errors JSON, angle_series JSON, created_at DATETIME
            )"""))
        conn.execute(text(
            "INSERT INTO sessions (id, user_id, exercise_name, reps) "
            "VALUES (1, 1, 'Squat', 7)"))

    original_engine = db.engine
    db.engine = engine
    try:
        db.init_db()
    finally:
        db.engine = original_engine

    columns = {c["name"] for c in sa_inspect(engine).get_columns("sessions")}
    assert {"adaptive", "target_rom", "target_met"} <= columns

    with engine.begin() as conn:
        row = conn.execute(text("SELECT reps FROM sessions WHERE id = 1")).one()
    assert row[0] == 7          # the existing session survived


def test_oversized_session_is_rejected_not_crashed(client, auth):
    """The frame cap is a memory bound; exceeding it must 413, not OOM."""
    from backend.config import MAX_SESSION_FRAMES

    frame = {"t": 0, "lm": [[0.5, 0.5, 0.0, 1.0]] * 33}
    response = client.post("/api/sessions", headers=auth, json={
        "exercise_slug": "terminal-knee-ext",
        "frames": [frame] * (MAX_SESSION_FRAMES + 1),
    })
    assert response.status_code == 413


def test_frame_cap_matches_the_client_constant():
    """pose.js stops recording at its own copy of this number. If the two
    drift apart the client keeps filming into a request the server rejects,
    and the patient loses the whole session."""
    import re
    from pathlib import Path

    from backend.config import MAX_SESSION_FRAMES

    source = Path(__file__).resolve().parents[2] / "pose.js"
    match = re.search(r"MAX_FRAMES\s*=\s*(\d+)", source.read_text(encoding="utf-8"))
    assert match, "MAX_FRAMES not found in pose.js"
    assert int(match.group(1)) == MAX_SESSION_FRAMES


# --- rate limiting ----------------------------------------------------------
def test_login_brute_force_is_blocked(client):
    """A public deployment must not allow unlimited password guesses."""
    from backend.ratelimit import LOGIN_ATTEMPTS

    client.post("/api/auth/signup", json=CREDS)

    codes = [
        client.post("/api/auth/login", json={
            "email": CREDS["email"], "password": f"guess-{i}"}).status_code
        for i in range(LOGIN_ATTEMPTS + 4)
    ]
    assert 429 in codes, "brute force was never throttled"
    assert codes.index(429) <= LOGIN_ATTEMPTS


def test_throttled_response_says_when_to_retry(client):
    from backend.ratelimit import LOGIN_ATTEMPTS

    for _ in range(LOGIN_ATTEMPTS + 2):
        response = client.post("/api/auth/login", json={
            "email": "nobody@example.com", "password": "x"})
    assert response.status_code == 429
    assert "Retry-After" in response.headers
    assert int(response.headers["Retry-After"]) > 0


def test_signup_flooding_is_blocked(client):
    from backend.ratelimit import SIGNUP_ATTEMPTS

    codes = [
        client.post("/api/auth/signup", json={
            "name": "Bot", "email": f"bot{i}@example.com",
            "password": "a-long-enough-password"}).status_code
        for i in range(SIGNUP_ATTEMPTS + 3)
    ]
    assert 429 in codes


def test_rate_limit_does_not_block_a_correct_login(client):
    """Throttling must not lock out the legitimate user it protects."""
    client.post("/api/auth/signup", json=CREDS)
    for _ in range(3):
        client.post("/api/auth/login", json={
            "email": CREDS["email"], "password": "wrong"})
    ok = client.post("/api/auth/login", json={
        "email": CREDS["email"], "password": CREDS["password"]})
    assert ok.status_code == 200


def test_window_expiry_restores_the_budget():
    """The window must slide, not latch permanently."""
    import time as _time

    from backend.ratelimit import SlidingWindow

    window = SlidingWindow(limit=2, window_seconds=1)
    assert window.check("ip") is None
    assert window.check("ip") is None
    assert window.check("ip") is not None      # third is over budget
    _time.sleep(1.05)
    assert window.check("ip") is None          # budget back after the window


def test_limits_are_tracked_per_address():
    from backend.ratelimit import SlidingWindow

    window = SlidingWindow(limit=1, window_seconds=60)
    assert window.check("1.1.1.1") is None
    assert window.check("1.1.1.1") is not None
    assert window.check("2.2.2.2") is None     # a different caller is unaffected
