"""Standard Operating Procedures (SOPs) for volunteers and venue staff.

The GenAI assistant retrieves the relevant SOP and narrates the steps in clear,
calm language for whoever is asking — a volunteer handling their first lost-child
report, or a steward managing a crowd surge. Grounding on these fixed procedures
keeps safety-critical guidance accurate and on-policy.
"""
from __future__ import annotations

PROCEDURES: list[dict] = [
    {
        "id": "lost_child",
        "title": "Lost or separated child",
        "roles": ["volunteer", "staff"],
        "keywords": ["lost child", "lost kid", "separated", "missing child", "child alone", "lost person"],
        "steps": [
            "Stay calm and keep the child with you — do not walk them around looking for the parent.",
            "Radio the Command Centre immediately with the child's description and your location.",
            "Escort the child to the nearest Guest Services (Section 120) or a designated safe point.",
            "Log the report; Command broadcasts the description to all gates.",
            "Only release the child to a verified guardian who can confirm identifying details.",
        ],
    },
    {
        "id": "medical",
        "title": "Medical emergency",
        "roles": ["volunteer", "staff"],
        "keywords": ["medical", "injured", "collapsed", "faint", "chest pain", "unconscious", "first aid", "hurt", "sick"],
        "steps": [
            "Do not move the person unless they are in immediate danger.",
            "Radio for First Aid with the exact section/zone and nature of the emergency.",
            "Clear space around the person and reassure them; keep bystanders back.",
            "If trained and safe, provide basic first aid until responders arrive.",
            "Hand over to medical staff and log the incident time and outcome.",
        ],
    },
    {
        "id": "crowd_surge",
        "title": "Crowd surge / dangerous density",
        "roles": ["staff", "organizer"],
        "keywords": ["crowd surge", "surge", "crush", "too crowded", "density", "packed", "overcrowd", "bottleneck"],
        "steps": [
            "Radio Command with the zone and direction of flow immediately.",
            "Do NOT open more entries into the affected area — relieve pressure by opening exits/alternate routes.",
            "Use calm, clear directions to redirect arriving fans to the nearest quieter gate/concourse.",
            "Hold and stagger inflow at the upstream gate until density eases.",
            "Escalate to a Yellow/Red status per the venue crowd-management plan if it does not ease.",
        ],
    },
    {
        "id": "evacuation",
        "title": "Partial or full evacuation",
        "roles": ["staff", "organizer"],
        "keywords": ["evacuate", "evacuation", "emergency exit", "clear the stand", "fire", "threat"],
        "steps": [
            "Await and confirm the evacuation instruction and zone from Command — do not self-initiate.",
            "Direct fans to the nearest SAFE exit, not necessarily the one they entered.",
            "Prioritise accessible egress: elevators at Gates A/D and step-free routes for wheelchair users.",
            "Keep moving, keep calm, keep talking — steady stream, no stopping in stairwells.",
            "Report your zone 'clear' to Command once evacuated.",
        ],
    },
    {
        "id": "accessibility_assist",
        "title": "Assisting a fan with accessibility needs",
        "roles": ["volunteer", "staff"],
        "keywords": ["wheelchair", "accessible", "disability", "assist", "blind", "deaf", "sensory", "step free", "help disabled"],
        "steps": [
            "Ask the fan how they would like to be assisted before acting — respect their independence.",
            "For step-free routing use the elevators at Gates A and D.",
            "The Sensory Room is near Section 142 for neurodivergent fans needing a quiet space.",
            "Assistive Listening Devices are available at Guest Services (Section 120).",
            "If unsure, radio the Accessibility Coordinator rather than guessing.",
        ],
    },
    {
        "id": "intoxicated",
        "title": "Intoxicated or aggressive fan",
        "roles": ["staff"],
        "keywords": ["drunk", "intoxicated", "aggressive", "fight", "abusive", "disorderly"],
        "steps": [
            "Do not confront alone — call for a second steward and, if needed, security.",
            "Keep a safe distance and a calm tone; avoid escalating language.",
            "Radio Command with the location and a description.",
            "Follow the venue's ejection procedure only with security present.",
            "Document the incident, including witnesses, for the duty manager.",
        ],
    },
    {
        "id": "lost_property",
        "title": "Lost property",
        "roles": ["volunteer", "staff"],
        "keywords": ["lost property", "lost bag", "lost phone", "lost item", "found item", "left behind"],
        "steps": [
            "Take the item to Guest Services (Section 120) — do not keep it on your person.",
            "Log a description, the location found, and the time.",
            "Direct the fan who lost an item to Guest Services to file a claim.",
            "Handle any suspicious/unattended item as a SECURITY report, not lost property.",
        ],
    },
    {
        "id": "ticket_issue",
        "title": "Ticket / entry dispute",
        "roles": ["volunteer", "staff"],
        "keywords": ["ticket", "entry", "scan", "invalid ticket", "duplicate", "gate dispute", "cant get in"],
        "steps": [
            "Stay polite; do not block the flow — step the fan aside to a resolution point.",
            "Verify the mobile ticket in the FIFA wallet (screenshots are not valid).",
            "For duplicate/invalid scans, escalate to the Ticketing Supervisor at the gate.",
            "Never accept cash or resolve payment yourself — the venue is cashless.",
        ],
    },
]


def find_procedure(text: str, role: str | None = None) -> list[dict]:
    low = text.lower()
    scored = []
    for p in PROCEDURES:
        if role and role not in p["roles"]:
            continue
        score = sum(1 for kw in p["keywords"] if kw in low)
        if score:
            scored.append((score, p))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in scored]
