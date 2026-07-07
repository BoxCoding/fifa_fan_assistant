"""Simulated live incident feed for venue staff & organizers.

In DEMO_MODE we synthesise a small, time-varying set of open incidents so the
staff response console and organizer briefing have realistic material without a
real dispatch system. Values are deterministic per-minute so the UI is stable
and repeatable. Swap for a real incident-management feed in production.
"""
from __future__ import annotations

import time

# Catalogue of incident templates we rotate through.
_TEMPLATES = [
    {"type": "medical", "severity": "high", "zone": "Section 118", "desc": "Fan reported feeling faint; first-aid dispatched."},
    {"type": "crowd_surge", "severity": "high", "zone": "Gate B / North Concourse", "desc": "Entry queue building rapidly ahead of kickoff."},
    {"type": "lost_person", "severity": "medium", "zone": "Gate C / East Concourse", "desc": "Child separated from family; description logged."},
    {"type": "spill", "severity": "low", "zone": "Section 130 concourse", "desc": "Drink spill — slip hazard; cleaning requested."},
    {"type": "security", "severity": "medium", "zone": "Gate A / West Concourse", "desc": "Unattended bag reported; staff verifying."},
    {"type": "accessibility", "severity": "medium", "zone": "Elevator D (South)", "desc": "Elevator busy; wheelchair user needs assistance to Upper level."},
    {"type": "weather", "severity": "low", "zone": "Outdoor Fan Zone", "desc": "Light rain forecast; monitor for covered-area demand."},
    {"type": "queue", "severity": "low", "zone": "Global Kitchen (Halal), Section 118", "desc": "Concession queue long; consider opening second till."},
]

_STATUSES = ["open", "in_progress"]


def live_incidents() -> dict:
    """Return the currently 'active' incidents plus severity counts.

    We surface a rotating subset (3-5 incidents) chosen by the current minute so
    the feed evolves during a demo but is stable moment-to-moment.
    """
    minute = int(time.time() // 60)
    n = 3 + (minute % 3)  # 3..5 active incidents
    active = []
    for i in range(n):
        tpl = _TEMPLATES[(minute + i) % len(_TEMPLATES)]
        age_min = ((minute * 7 + i * 13) % 25) + 1
        active.append({
            "id": f"INC-{(minute + i) % 1000:03d}",
            "type": tpl["type"],
            "severity": tpl["severity"],
            "zone": tpl["zone"],
            "description": tpl["desc"],
            "status": _STATUSES[(minute + i) % len(_STATUSES)],
            "age_min": age_min,
        })
    # Sort most severe + newest first.
    order = {"high": 0, "medium": 1, "low": 2}
    active.sort(key=lambda x: (order[x["severity"]], x["age_min"]))
    counts = {"high": 0, "medium": 0, "low": 0}
    for inc in active:
        counts[inc["severity"]] += 1
    return {
        "generated_at": int(time.time()),
        "incidents": active,
        "counts": counts,
        "total_open": len(active),
    }
