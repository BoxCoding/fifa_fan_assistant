"""Integration tests: auth gating, login, cache behaviour over the HTTP API."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core import cache, ratelimit
from app.main import app

client = TestClient(app)

DEMO_PW = "kickoff2026"


@pytest.fixture(autouse=True)
def _reset_state():
    cache.clear()
    ratelimit.reset()
    yield


def _token(username: str = "fan") -> str:
    r = client.post("/api/auth/login", json={"username": username, "password": DEMO_PW})
    assert r.status_code == 200, r.text
    return r.json()["token"]


# --- Auth -------------------------------------------------------------------
def test_login_success_returns_token_and_user():
    r = client.post("/api/auth/login", json={"username": "organizer", "password": DEMO_PW})
    assert r.status_code == 200
    body = r.json()
    assert body["user"]["role"] == "organizer"
    assert body["token"]


def test_login_bad_password_rejected():
    r = client.post("/api/auth/login", json={"username": "fan", "password": "nope"})
    assert r.status_code == 401


def test_login_unknown_user_rejected():
    r = client.post("/api/auth/login", json={"username": "ghost", "password": DEMO_PW})
    assert r.status_code == 401


def test_protected_endpoint_requires_token():
    r = client.post("/api/chat", json={"message": "Where is the nearest restroom?", "role": "fan"})
    assert r.status_code == 401


def test_protected_endpoint_rejects_bad_token():
    r = client.post(
        "/api/chat",
        json={"message": "hi", "role": "fan"},
        headers={"Authorization": "Bearer not.a.token"},
    )
    assert r.status_code == 401


def test_me_returns_current_user():
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {_token('staff')}"})
    assert r.status_code == 200
    assert r.json()["username"] == "staff"


def test_health_is_public():
    assert client.get("/health").status_code == 200


# --- Chat + cache -----------------------------------------------------------
def test_chat_authenticated_ok():
    h = {"Authorization": f"Bearer {_token()}"}
    r = client.post("/api/chat", json={"message": "Where is the nearest restroom?", "role": "fan"}, headers=h)
    assert r.status_code == 200
    assert r.json()["intent"] == "navigation"


def test_repeated_question_served_from_cache():
    h = {"Authorization": f"Bearer {_token()}"}
    q = "Where can I find halal food?"
    first = client.post("/api/chat", json={"message": q, "role": "fan"}, headers=h).json()
    # Repeat with conversation history present (as the real UI sends it) — must
    # still hit the cache, keyed only on role + message.
    second = client.post(
        "/api/chat",
        json={"message": q, "role": "fan", "history": [
            {"role": "user", "content": q},
            {"role": "assistant", "content": first["reply"]},
        ]},
        headers=h,
    ).json()
    assert first["cached"] is False
    assert second["cached"] is True
    assert second["reply"] == first["reply"]


def test_live_intent_not_cached():
    h = {"Authorization": f"Bearer {_token('organizer')}"}
    payload = {"message": "How busy is the venue right now?", "role": "organizer"}
    first = client.post("/api/chat", json=payload, headers=h).json()
    second = client.post("/api/chat", json=payload, headers=h).json()
    assert first["intent"] == "crowd"
    assert second["cached"] is False  # live data must never be cached


# --- Authorization (role-based) --------------------------------------------
def test_fan_cannot_use_organizer_persona():
    h = {"Authorization": f"Bearer {_token('fan')}"}
    r = client.post("/api/chat", json={"message": "brief me", "role": "organizer"}, headers=h)
    assert r.status_code == 403


def test_organizer_can_use_any_persona():
    h = {"Authorization": f"Bearer {_token('organizer')}"}
    r = client.post("/api/chat", json={"message": "Where is the restroom?", "role": "fan"}, headers=h)
    assert r.status_code == 200


def test_fan_cannot_read_incidents():
    h = {"Authorization": f"Bearer {_token('fan')}"}
    assert client.get("/api/incidents/metlife", headers=h).status_code == 403


def test_staff_can_read_incidents():
    h = {"Authorization": f"Bearer {_token('staff')}"}
    assert client.get("/api/incidents/metlife", headers=h).status_code == 200


def test_fan_cannot_read_volunteer_tasks():
    h = {"Authorization": f"Bearer {_token('fan')}"}
    assert client.get("/api/volunteer/tasks", headers=h).status_code == 403


def test_organizer_can_read_sustainability():
    h = {"Authorization": f"Bearer {_token('organizer')}"}
    assert client.get("/api/sustainability/metlife", headers=h).status_code == 200


# --- Rate limiting ----------------------------------------------------------
def test_login_rate_limited_after_burst(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "LOGIN_RATE_LIMIT", 3)
    ratelimit.reset()
    # 3 allowed (even if wrong password), then throttled with 429.
    for _ in range(3):
        assert client.post("/api/auth/login", json={"username": "fan", "password": "x"}).status_code == 401
    assert client.post("/api/auth/login", json={"username": "fan", "password": "x"}).status_code == 429
