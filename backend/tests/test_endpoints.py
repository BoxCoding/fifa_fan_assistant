"""Integration tests for the stadium, transport and operations endpoints."""
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


def _token(username: str) -> str:
    r = client.post("/api/auth/login", json={"username": username, "password": DEMO_PW})
    assert r.status_code == 200, r.text
    return r.json()["token"]


def _auth(username: str) -> dict:
    return {"Authorization": f"Bearer {_token(username)}"}


# --- Stadium ---------------------------------------------------------------
def test_venues_lists_all_host_cities():
    r = client.get("/api/venues", headers=_auth("fan"))
    assert r.status_code == 200
    assert len(r.json()["venues"]) == 16


def test_stadium_detail_ok():
    r = client.get("/api/stadium/metlife", headers=_auth("fan"))
    assert r.status_code == 200
    body = r.json()
    assert body["venue"]["name"] == "MetLife Stadium"
    assert body["detail"]["gates"]


def test_stadium_unknown_404():
    assert client.get("/api/stadium/nope", headers=_auth("fan")).status_code == 404


def test_amenities_filter_by_type():
    r = client.get("/api/amenities/metlife?type=food", headers=_auth("fan"))
    assert r.status_code == 200
    items = r.json()["amenities"]
    assert items and all(a["type"] == "food" for a in items)
    assert all("queue" in a for a in items)


def test_amenities_unknown_stadium_404():
    assert client.get("/api/amenities/nope", headers=_auth("fan")).status_code == 404


def test_navigate_step_free_route():
    r = client.post(
        "/api/navigate",
        headers=_auth("fan"),
        json={"from_point": "Gate A", "to_point": "Section 232", "accessible": True},
    )
    assert r.status_code == 200
    steps = r.json()["steps"]
    assert any("step-free" in s.lower() or "elevator" in s.lower() for s in steps)


def test_navigate_standard_route():
    r = client.post(
        "/api/navigate",
        headers=_auth("fan"),
        json={"from_point": "Gate B", "to_point": "Section 112", "accessible": False},
    )
    assert r.status_code == 200
    assert r.json()["steps"][-1].startswith("You've arrived")


# --- Transport -------------------------------------------------------------
def test_transport_snapshot():
    r = client.get("/api/transport/metlife", headers=_auth("fan"))
    assert r.status_code == 200
    body = r.json()
    assert body["modes"] and body["recommended"]


def test_transport_unknown_404():
    assert client.get("/api/transport/nope", headers=_auth("fan")).status_code == 404


# --- Operations ------------------------------------------------------------
def test_procedures_by_role():
    r = client.get("/api/procedures?role=staff", headers=_auth("staff"))
    assert r.status_code == 200
    assert all("staff" in p["roles"] for p in r.json()["procedures"])


def test_procedures_search_query():
    r = client.get("/api/procedures?q=lost%20child", headers=_auth("volunteer"))
    assert r.status_code == 200
    assert r.json()["procedures"][0]["id"] == "lost_child"


def test_briefing_synthesises_recommendations():
    r = client.get("/api/ops/briefing/metlife", headers=_auth("organizer"))
    assert r.status_code == 200
    assert r.json()["data"]["recommendations"]


def test_briefing_unknown_stadium_404():
    assert client.get("/api/ops/briefing/nope", headers=_auth("organizer")).status_code == 404


def test_sustainability_metrics():
    r = client.get("/api/sustainability/metlife", headers=_auth("organizer"))
    assert r.status_code == 200
    assert len(r.json()["metrics"]) == 5
