"""Operational-intelligence composition.

Combines the individual live feeds (crowd, transport, incidents, sustainability)
into higher-order products that the volunteer and organizer views consume:

  * volunteer_tasks()  — a prioritised task list derived from open incidents plus
                         routine matchday duties.
  * briefing_facts()   — the grounded facts + structured data for an operational
                         briefing (synthesised into prose by the agent).

Keeping this synthesis deterministic means the AI narration layer only has to
*phrase* it — the underlying situational awareness is always correct.
"""
from __future__ import annotations

from app.data import incidents, live, sustainability

# Incident types a volunteer (vs. security/medical professional) can action.
_VOLUNTEER_ACTIONABLE = {"lost_person", "spill", "queue", "accessibility", "weather"}

# Routine, always-on volunteer duties.
_ROUTINE_TASKS = [
    {"id": "T-WAYFIND", "title": "Wayfinding support at your assigned gate", "priority": "normal", "zone": "Assigned gate"},
    {"id": "T-WATER", "title": "Check & restock the free water refill station", "priority": "normal", "zone": "Section 110 / 132"},
    {"id": "T-ACCESS", "title": "Greet and assist fans with accessibility needs", "priority": "normal", "zone": "Guest Services (120)"},
]


def volunteer_tasks() -> dict:
    """Prioritised task list = live incidents a volunteer can help with + routine."""
    feed = incidents.live_incidents()
    tasks = []
    for inc in feed["incidents"]:
        if inc["type"] in _VOLUNTEER_ACTIONABLE:
            tasks.append({
                "id": inc["id"],
                "title": f"{inc['type'].replace('_', ' ').title()} — {inc['description']}",
                "priority": "urgent" if inc["severity"] == "high" else "high" if inc["severity"] == "medium" else "normal",
                "zone": inc["zone"],
                "source": "incident",
            })
    for t in _ROUTINE_TASKS:
        tasks.append({**t, "source": "routine"})
    order = {"urgent": 0, "high": 1, "normal": 2}
    tasks.sort(key=lambda t: order[t["priority"]])
    return {"generated_at": feed["generated_at"], "tasks": tasks, "urgent_count": sum(1 for t in tasks if t["priority"] == "urgent")}


def briefing_facts() -> tuple[list[str], dict]:
    """Return (fact lines, structured data) synthesising the venue's live state."""
    crowd = live.crowd_snapshot()
    transport = live.transport_snapshot()
    inc = incidents.live_incidents()
    sus = sustainability.sustainability_snapshot()

    quietest = min(crowd["zones"], key=lambda z: z["pct"])
    busiest = max(crowd["zones"], key=lambda z: z["pct"])
    high_sev = [i for i in inc["incidents"] if i["severity"] == "high"]

    facts = [
        f"Crowd: overall {crowd['overall_level']}. Busiest {busiest['name']} ({busiest['pct']}%); "
        f"quietest {quietest['name']} ({quietest['pct']}%).",
        f"Transport: recommend {transport['recommended']} ({transport['recommended_reason']}).",
        f"Incidents: {inc['total_open']} open ({inc['counts']['high']} high, {inc['counts']['medium']} medium, {inc['counts']['low']} low).",
    ]
    if high_sev:
        facts.append("Priority incidents: " + "; ".join(f"{i['type']} at {i['zone']}" for i in high_sev) + ".")

    # Deterministic recommendations (real-time decision support).
    recs = []
    if busiest["pct"] >= 85:
        recs.append(f"Redirect arrivals away from {busiest['name']} toward {quietest['name']}; hold inflow upstream.")
    if any(i["type"] == "crowd_surge" for i in inc["incidents"]):
        recs.append("Active crowd-surge report — relieve pressure via exits, do not open new entries into the zone.")
    slowest = max(transport["modes"], key=lambda m: m["wait_min"])
    if slowest["wait_min"] >= 35:
        recs.append(f"{slowest['name']} wait ~{slowest['wait_min']} min — nudge departing fans toward {transport['recommended']}.")
    if not recs:
        recs.append("No critical actions — maintain normal operations and monitor the busiest zones.")
    facts.append("Recommended actions: " + " ".join(recs))

    data = {
        "crowd": crowd,
        "transport": transport,
        "incidents": inc,
        "sustainability": sus,
        "recommendations": recs,
    }
    return facts, data
