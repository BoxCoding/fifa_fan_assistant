"""Curated fan-facing knowledge base used for retrieval-augmented answers.

Each entry has keywords (for lightweight retrieval), a topic, and a canonical
answer. The agent retrieves the most relevant entries and grounds the LLM (or
the fallback templater) on them so answers stay accurate and on-policy.
"""
from __future__ import annotations

KNOWLEDGE_BASE: list[dict] = [
    {
        "id": "bag_policy",
        "topic": "Bag policy",
        "keywords": ["bag", "backpack", "purse", "clear bag", "what can i bring", "prohibited"],
        "answer": (
            "MetLife Stadium enforces a clear-bag policy. Bags must be clear plastic/vinyl "
            "and no larger than 12\" x 6\" x 12\", or a small clutch (4.5\" x 6.5\"). "
            "Prohibited items include outside food/drink (empty reusable bottles are OK), "
            "umbrellas, professional cameras, and noisemakers."
        ),
    },
    {
        "id": "gates_open",
        "topic": "Gate times",
        "keywords": ["what time", "gates open", "arrive", "entry", "when should i"],
        "answer": (
            "Stadium gates open 2 hours before kickoff. For a high-demand World Cup match, "
            "arrive 90+ minutes early to clear security and enjoy the fan zone. Mobile tickets "
            "in your FIFA wallet are required — screenshots are not accepted."
        ),
    },
    {
        "id": "water",
        "topic": "Water & hydration",
        "keywords": ["water", "thirsty", "hydrate", "refill", "free water", "bottle"],
        "answer": (
            "Free water refill stations are available on every concourse (nearest to sections "
            "110 and 132 on the lower level). Bring an empty reusable bottle — it helps the "
            "tournament's zero-waste goal and keeps you hydrated."
        ),
    },
    {
        "id": "halal_food",
        "topic": "Dietary food options",
        "keywords": ["halal", "kosher", "vegan", "vegetarian", "gluten", "dietary", "food", "eat"],
        "answer": (
            "Dietary options are clearly labelled: Global Kitchen (Halal) near section 118, "
            "Kosher Corner near section 225, and Green Pitch (Vegan/plant-based, gluten-free) "
            "near section 124. Most classic stands also offer a halal-certified option."
        ),
    },
    {
        "id": "accessibility",
        "topic": "Accessibility",
        "keywords": ["wheelchair", "accessible", "disability", "step free", "elevator", "sensory", "assistance"],
        "answer": (
            "Accessible services include step-free routing via elevators at Gates A and D, "
            "wheelchair-accessible seating in every tier, companion restrooms on every "
            "concourse, a Sensory Room near section 142 for neurodivergent fans, and Assistive "
            "Listening Devices at Guest Services (section 120)."
        ),
    },
    {
        "id": "transport",
        "topic": "Getting there",
        "keywords": ["transport", "train", "rail", "bus", "parking", "uber", "rideshare", "get to", "how do i get", "leave"],
        "answer": (
            "Public transit is strongly recommended. NJ Transit rail runs directly to the "
            "stadium platform (arrive at Gate A). Coach USA buses serve Gate B. Rideshare "
            "drop-off/pick-up is at Lot G near Gate C. Accessible parking is in Lot K near "
            "Gate D. Expect heavy demand — pre-book return transit before the match."
        ),
    },
    {
        "id": "lost",
        "topic": "Lost & found / lost person",
        "keywords": ["lost", "found", "missing", "child", "meeting point", "help", "guest services"],
        "answer": (
            "Guest Services is near section 120 (lower level). For a lost child or companion, "
            "notify the nearest staff member or steward immediately — every gate has a radio to "
            "the command centre. Agree a family meeting point at Guest Services before the match."
        ),
    },
    {
        "id": "cashless",
        "topic": "Payments",
        "keywords": ["cash", "card", "pay", "payment", "cashless", "money", "atm"],
        "answer": (
            "MetLife Stadium is 100% cashless. Bring a contactless card or mobile wallet. "
            "Reverse-ATMs (cash-to-card kiosks) are available at Guest Services if you only "
            "have cash."
        ),
    },
    {
        "id": "sustainability",
        "topic": "Sustainability",
        "keywords": ["recycle", "recycling", "sustainability", "waste", "green", "environment", "compost"],
        "answer": (
            "FIFA World Cup 2026 targets a low-waste tournament. Use the Zero-Waste Sorting "
            "Points (nearest section 115) to separate recycling and compost, refill at free "
            "water stations instead of buying bottles, and take public transit to cut emissions."
        ),
    },
    {
        "id": "match_info",
        "topic": "Match & schedule",
        "keywords": ["match", "kickoff", "schedule", "who is playing", "score", "lineup", "fixture"],
        "answer": (
            "Check the official FIFA app for live fixtures, kickoff times and scores. MetLife "
            "hosts group-stage matches through the Final on 19 July 2026. This assistant can "
            "help you navigate once you know your match and section."
        ),
    },
]
