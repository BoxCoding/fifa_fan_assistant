"""Simulated real-time operational data.

In DEMO_MODE we synthesise plausible, time-varying crowd, transport and queue
data so organisers/staff features (crowd management, real-time decisions) are
demoable without live sensor feeds. Values are deterministic per-minute so the
UI updates smoothly and repeatably. Swap these functions for real feeds
(turnstile counts, transit APIs, CV people-counting) in production.
"""
from __future__ import annotations

import math
import time

# Zones we report density for — roughly one per gate/concourse cluster.
ZONES = [
    {"id": "gate_a", "name": "Gate A / West Concourse", "capacity": 8000},
    {"id": "gate_b", "name": "Gate B / North Concourse", "capacity": 7000},
    {"id": "gate_c", "name": "Gate C / East Concourse", "capacity": 8000},
    {"id": "gate_d", "name": "Gate D / South Concourse", "capacity": 6000},
    {"id": "concourse_food", "name": "Main Food Court (100s)", "capacity": 4000},
    {"id": "fan_zone", "name": "Outdoor Fan Zone", "capacity": 12000},
]

TRANSPORT_MODES = [
    {"id": "rail", "name": "NJ Transit Rail", "gate": "A"},
    {"id": "bus", "name": "Coach USA Bus", "gate": "B"},
    {"id": "rideshare", "name": "Rideshare (Lot G)", "gate": "C"},
    {"id": "parking", "name": "Parking Lots", "gate": "D"},
]


def _wave(zone_id: str, period_min: float, phase: float) -> float:
    """Return a 0..1 occupancy factor that drifts over time, unique per zone."""
    minute = time.time() / 60.0
    seed = sum(ord(c) for c in zone_id)
    base = 0.55 + 0.35 * math.sin((minute / period_min) * 2 * math.pi + phase + seed)
    return max(0.05, min(0.99, base))


def _level(pct: float) -> str:
    if pct >= 0.85:
        return "critical"
    if pct >= 0.65:
        return "busy"
    if pct >= 0.35:
        return "moderate"
    return "low"


def crowd_snapshot() -> dict:
    zones = []
    for i, z in enumerate(ZONES):
        pct = _wave(z["id"], period_min=18, phase=i * 0.8)
        occupancy = int(z["capacity"] * pct)
        zones.append({
            "id": z["id"],
            "name": z["name"],
            "capacity": z["capacity"],
            "occupancy": occupancy,
            "pct": round(pct * 100),
            "level": _level(pct),
        })
    hottest = max(zones, key=lambda z: z["pct"])
    return {
        "generated_at": int(time.time()),
        "zones": zones,
        "busiest_zone": hottest["name"],
        "overall_level": _level(sum(z["pct"] for z in zones) / len(zones) / 100),
    }


def transport_snapshot() -> dict:
    modes = []
    for i, m in enumerate(TRANSPORT_MODES):
        pct = _wave("t_" + m["id"], period_min=25, phase=i * 1.3)
        wait_min = int(5 + pct * 40)
        modes.append({
            "id": m["id"],
            "name": m["name"],
            "gate": m["gate"],
            "load_pct": round(pct * 100),
            "wait_min": wait_min,
            "status": _level(pct),
        })
    best = min(modes, key=lambda m: m["wait_min"])
    return {
        "generated_at": int(time.time()),
        "modes": modes,
        "recommended": best["name"],
        "recommended_reason": f"Shortest wait right now (~{best['wait_min']} min).",
    }


def amenity_queue(amenity_id: str) -> int:
    """Approximate current queue length (people) for a given amenity."""
    pct = _wave("q_" + amenity_id, period_min=12, phase=1.1)
    return int(pct * 40)
