"""Unit tests for the data layer and agent grounding across every intent."""
from __future__ import annotations

import asyncio

from app.core import cache
from app.core.agent import handle_chat
from app.data import incidents, live, ops, sustainability
from app.data.procedures import find_procedure


def setup_function():
    cache.clear()


# --- Live simulators -------------------------------------------------------
def test_crowd_snapshot_shape():
    snap = live.crowd_snapshot()
    assert len(snap["zones"]) == 6
    assert snap["busiest_zone"]
    assert all(0 <= z["pct"] <= 100 for z in snap["zones"])


def test_transport_recommends_shortest_wait():
    snap = live.transport_snapshot()
    best = min(snap["modes"], key=lambda m: m["wait_min"])
    assert snap["recommended"] == best["name"]


def test_amenity_queue_is_bounded():
    assert 0 <= live.amenity_queue("food_halal") <= 40


def test_incidents_sorted_by_severity():
    feed = incidents.live_incidents()
    order = {"high": 0, "medium": 1, "low": 2}
    sevs = [order[i["severity"]] for i in feed["incidents"]]
    assert sevs == sorted(sevs)


def test_sustainability_has_targets():
    snap = sustainability.sustainability_snapshot()
    assert all(m["target"] > 0 for m in snap["metrics"])


# --- Ops synthesis ---------------------------------------------------------
def test_volunteer_tasks_urgent_first():
    t = ops.volunteer_tasks()
    order = {"urgent": 0, "high": 1, "normal": 2}
    prios = [order[x["priority"]] for x in t["tasks"]]
    assert prios == sorted(prios)


def test_briefing_facts_include_recommendations():
    facts, data = ops.briefing_facts()
    assert any("Recommended actions" in f for f in facts)
    assert data["recommendations"]


# --- Procedures ------------------------------------------------------------
def test_find_procedure_scoped_by_role():
    # A medical SOP is available to volunteer and staff.
    assert find_procedure("medical emergency", "volunteer")
    # An intoxicated-fan SOP is staff-only.
    assert find_procedure("intoxicated aggressive fan", "volunteer") == []
    assert find_procedure("intoxicated aggressive fan", "staff")


# --- Agent grounding across intents ----------------------------------------
def _reply(role, message):
    return asyncio.run(handle_chat(message, role, "metlife", []))


def test_agent_navigation_lists_gates():
    r = _reply("fan", "How do I get to my seat?")
    assert r.intent == "navigation"
    assert r.data and "gates" in r.data


def test_agent_accessibility_services():
    r = _reply("fan", "I use a wheelchair, how do I get to my seat?")
    assert r.intent == "accessibility"
    assert "accessible_services" in r.data


def test_agent_incident_intent_for_staff():
    r = _reply("staff", "What incidents are open right now?")
    assert r.intent == "incident"
    assert "incidents" in r.data


def test_agent_task_intent_for_volunteer():
    r = _reply("volunteer", "What are my current tasks?")
    assert r.intent == "task"
    assert "tasks" in r.data


def test_agent_briefing_intent_for_organizer():
    r = _reply("organizer", "Give me the operational briefing")
    assert r.intent == "briefing"
    assert "recommendations" in r.data


def test_agent_sustainability_for_organizer():
    r = _reply("organizer", "How are our sustainability metrics?")
    assert r.intent == "sustainability"
    assert "sustainability" in r.data


def test_agent_procedure_for_volunteer():
    r = _reply("volunteer", "How do I handle a lost child?")
    assert r.intent == "procedure"
    assert "procedure" in r.data


def test_agent_unknown_role_defaults_to_fan():
    r = _reply("intruder", "Where is the nearest restroom?")
    assert r.role == "fan"
