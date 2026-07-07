"""Static domain data for FIFA World Cup 2026 venues.

The tournament is co-hosted by Canada, Mexico and the USA across 16 host cities.
We model the full venue list for context, plus a richly detailed layout for the
demo stadium (MetLife, host of the final) that powers navigation, amenities and
accessibility features.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# All 16 host venues (name, city, country, capacity, notable role)
# ---------------------------------------------------------------------------
HOST_VENUES: list[dict] = [
    {"id": "metlife", "name": "MetLife Stadium", "city": "New York / New Jersey", "country": "USA", "capacity": 82500, "role": "Final"},
    {"id": "sofi", "name": "SoFi Stadium", "city": "Los Angeles", "country": "USA", "capacity": 70000, "role": "Group + knockout"},
    {"id": "att", "name": "AT&T Stadium", "city": "Dallas", "country": "USA", "capacity": 80000, "role": "Semi-final"},
    {"id": "mercedes", "name": "Mercedes-Benz Stadium", "city": "Atlanta", "country": "USA", "capacity": 71000, "role": "Semi-final"},
    {"id": "arrowhead", "name": "Arrowhead Stadium", "city": "Kansas City", "country": "USA", "capacity": 76000, "role": "Quarter-final"},
    {"id": "gillette", "name": "Gillette Stadium", "city": "Boston", "country": "USA", "capacity": 65000, "role": "Quarter-final"},
    {"id": "lincoln", "name": "Lincoln Financial Field", "city": "Philadelphia", "country": "USA", "capacity": 69000, "role": "Round of 16"},
    {"id": "levis", "name": "Levi's Stadium", "city": "San Francisco Bay Area", "country": "USA", "capacity": 70000, "role": "Group + knockout"},
    {"id": "hardrock", "name": "Hard Rock Stadium", "city": "Miami", "country": "USA", "capacity": 65000, "role": "Third place"},
    {"id": "nrg", "name": "NRG Stadium", "city": "Houston", "country": "USA", "capacity": 72000, "role": "Round of 16"},
    {"id": "lumen", "name": "Lumen Field", "city": "Seattle", "country": "USA", "capacity": 69000, "role": "Group + knockout"},
    {"id": "azteca", "name": "Estadio Azteca", "city": "Mexico City", "country": "Mexico", "capacity": 87000, "role": "Opening match"},
    {"id": "akron", "name": "Estadio Akron", "city": "Guadalajara", "country": "Mexico", "capacity": 48000, "role": "Group stage"},
    {"id": "monterrey", "name": "Estadio BBVA", "city": "Monterrey", "country": "Mexico", "capacity": 53500, "role": "Group + knockout"},
    {"id": "bmo", "name": "BMO Field", "city": "Toronto", "country": "Canada", "capacity": 45000, "role": "Group + knockout"},
    {"id": "bcplace", "name": "BC Place", "city": "Vancouver", "country": "Canada", "capacity": 54000, "role": "Group + knockout"},
]

VENUE_BY_ID = {v["id"]: v for v in HOST_VENUES}


# ---------------------------------------------------------------------------
# Detailed demo layout: MetLife Stadium
# ---------------------------------------------------------------------------
# Amenities keyed by concourse level. Each has a friendly name, the nearest
# section range, and metadata used for filtering (halal, kosher, vegan, etc.).
METLIFE = {
    "id": "metlife",
    "name": "MetLife Stadium",
    "levels": ["Lower (100s)", "Club (200s)", "Upper (300s)"],
    "gates": [
        {"id": "A", "name": "Gate A", "side": "West", "serves": "100 & 300 level, sections 101-115", "transit": "NJ Transit rail platform"},
        {"id": "B", "name": "Gate B", "side": "North", "serves": "100 & 300 level, sections 116-125", "transit": "Coach USA bus lot"},
        {"id": "C", "name": "Gate C", "side": "East", "serves": "100 & 300 level, sections 126-140", "transit": "Lot G rideshare drop-off"},
        {"id": "D", "name": "Gate D", "side": "South", "serves": "100 & 300 level, sections 141-152", "transit": "Accessible parking Lot K"},
    ],
    "amenities": [
        {"id": "restroom_a", "type": "restroom", "name": "Restrooms — West Concourse", "near_section": "112", "level": "Lower (100s)", "accessible": True},
        {"id": "restroom_c", "type": "restroom", "name": "Restrooms — East Concourse", "near_section": "130", "level": "Lower (100s)", "accessible": True},
        {"id": "restroom_upper", "type": "restroom", "name": "Restrooms — Upper North", "near_section": "320", "level": "Upper (300s)", "accessible": True},
        {"id": "firstaid_main", "type": "first_aid", "name": "First Aid Station — Main", "near_section": "116", "level": "Lower (100s)", "accessible": True},
        {"id": "firstaid_upper", "type": "first_aid", "name": "First Aid Station — Upper", "near_section": "328", "level": "Upper (300s)", "accessible": True},
        {"id": "food_halal", "type": "food", "name": "Global Kitchen (Halal)", "near_section": "118", "level": "Lower (100s)", "tags": ["halal", "vegetarian"]},
        {"id": "food_vegan", "type": "food", "name": "Green Pitch (Vegan / Plant-based)", "near_section": "124", "level": "Club (200s)", "tags": ["vegan", "vegetarian", "gluten_free"]},
        {"id": "food_kosher", "type": "food", "name": "Kosher Corner", "near_section": "225", "level": "Club (200s)", "tags": ["kosher"]},
        {"id": "food_classic", "type": "food", "name": "Stadium Classics (burgers, dogs)", "near_section": "134", "level": "Lower (100s)", "tags": ["halal_option"]},
        {"id": "water_a", "type": "water", "name": "Free Water Refill Station — West", "near_section": "110", "level": "Lower (100s)", "tags": ["sustainability"]},
        {"id": "water_c", "type": "water", "name": "Free Water Refill Station — East", "near_section": "132", "level": "Lower (100s)", "tags": ["sustainability"]},
        {"id": "merch_main", "type": "merch", "name": "FIFA Official Store", "near_section": "120", "level": "Lower (100s)"},
        {"id": "charging", "type": "charging", "name": "Phone Charging Lockers", "near_section": "128", "level": "Club (200s)"},
        {"id": "prayer", "type": "prayer", "name": "Multi-Faith Quiet Room", "near_section": "140", "level": "Lower (100s)", "accessible": True},
        {"id": "sensory", "type": "sensory", "name": "Sensory Room (accessibility)", "near_section": "142", "level": "Lower (100s)", "accessible": True},
        {"id": "recycling", "type": "recycling", "name": "Zero-Waste Sorting Point", "near_section": "115", "level": "Lower (100s)", "tags": ["sustainability"]},
    ],
    "accessible_services": [
        "Step-free routing via elevators at Gates A and D",
        "Wheelchair-accessible seating in every section tier",
        "Sensory Room near section 142 for neurodivergent fans",
        "Assistive Listening Devices at Guest Services (section 120)",
        "Companion restrooms on every concourse",
    ],
    "elevators": [
        {"id": "elev_a", "name": "Elevator A (West)", "serves": ["Lower (100s)", "Club (200s)", "Upper (300s)"], "near_gate": "A"},
        {"id": "elev_d", "name": "Elevator D (South)", "serves": ["Lower (100s)", "Club (200s)", "Upper (300s)"], "near_gate": "D"},
    ],
}

STADIUM_DETAIL = {"metlife": METLIFE}


def get_venue(stadium_id: str) -> dict | None:
    return VENUE_BY_ID.get(stadium_id)


def get_detail(stadium_id: str) -> dict | None:
    return STADIUM_DETAIL.get(stadium_id)
