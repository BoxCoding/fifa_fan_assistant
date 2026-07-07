"""Simulated sustainability KPIs for the organizer dashboard.

FIFA World Cup 2026 targets a low-waste, lower-emission tournament. This module
exposes matchday sustainability metrics the organizer view surfaces and the AI
briefing references. Deterministic and slowly-varying for a stable demo.
"""
from __future__ import annotations

import math
import time


def sustainability_snapshot() -> dict:
    minute = time.time() / 60.0
    drift = 0.5 + 0.5 * math.sin(minute / 30.0)  # 0..1 slow oscillation

    waste_diverted = round(62 + 12 * drift)          # % diverted from landfill
    recycling_rate = round(48 + 10 * drift)          # %
    bottles_saved = int(8000 + 4000 * drift)         # via free refill stations
    transit_share = round(58 + 8 * drift)            # % arriving by public transit
    renewable_pct = 74                               # venue renewable energy share

    return {
        "generated_at": int(time.time()),
        "metrics": [
            {"id": "waste_diverted", "label": "Waste diverted from landfill", "value": waste_diverted, "unit": "%", "target": 80, "trend": "up"},
            {"id": "recycling_rate", "label": "Recycling + compost rate", "value": recycling_rate, "unit": "%", "target": 65, "trend": "up"},
            {"id": "bottles_saved", "label": "Single-use bottles avoided", "value": bottles_saved, "unit": "", "target": 15000, "trend": "up"},
            {"id": "transit_share", "label": "Fans arriving by public transit", "value": transit_share, "unit": "%", "target": 70, "trend": "flat"},
            {"id": "renewable_pct", "label": "Venue renewable energy", "value": renewable_pct, "unit": "%", "target": 90, "trend": "flat"},
        ],
    }
