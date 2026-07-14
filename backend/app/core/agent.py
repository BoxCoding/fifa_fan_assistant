"""The Kickoff assistant agent — multi-persona, English-only.

One assistant serves four personas, adapting its knowledge and tone to each:

  * fan       — navigation, amenities, crowd, transport, accessibility, sustainability
  * volunteer — SOPs / procedures, task assignments (and can answer fan questions)
  * staff     — live incidents, response procedures, crowd & transport decisions
  * organizer — synthesised operational briefings and real-time decision support

Pipeline per turn: classify intent (within the persona's scope) → retrieve
grounding (knowledge base + live tools + SOPs + ops synthesis) → generate a reply
via the LLM when available, else a deterministic grounded fallback.

Design goal: the GenAI layer makes answers fluent and role-aware, but every
answer is grounded in structured data so it stays accurate and safe.
"""
from __future__ import annotations

from app.core import cache
from app.core.llm import LLMUnavailable, generate
from app.core.matching import kw_hit  # word-boundary keyword matcher
from app.data import live, ops
from app.data.incidents import live_incidents
from app.data.knowledge import KNOWLEDGE_BASE
from app.data.procedures import find_procedure
from app.data.stadiums import get_detail, get_venue
from app.models import Action, ChatMessage, ChatResponse

# ---------------------------------------------------------------------------
# Intent definitions
# ---------------------------------------------------------------------------
INTENTS = {
    # Fan-facing
    "navigation": ["get to", "how do i get", "where is", "find my seat", "section", "gate", "directions", "route", "way to", "nearest", "toilet", "restroom", "bathroom"],
    "crowd": ["crowd", "busy", "how full", "queue", "line", "packed", "wait", "density", "least busy", "quiet", "quietest"],
    "transport": ["train", "rail", "bus", "parking", "uber", "rideshare", "leave", "get home", "way home", "fastest way", "head home", "transport", "metro", "subway"],
    "accessibility": ["wheelchair", "accessible", "accessibility", "disability", "disabled", "step free", "step-free", "elevator", "lift", "sensory", "companion", "blind", "deaf"],
    "food": ["food", "eat", "halal", "kosher", "vegan", "vegetarian", "gluten", "drink", "water", "hungry"],
    "sustainability": ["recycle", "recycling", "waste", "compost", "sustainab*", "green", "environment", "carbon", "emission"],
    # Volunteer / staff
    "procedure": ["how do i handle", "procedure", "protocol", "what do i do", "sop", "steps", "how to deal", "how to handle", "someone is", "report a", "lost child", "lost person", "medical", "collapsed", "evacuat*", "crowd surge", "intoxicated", "aggressive", "lost property", "ticket dispute"],
    "incident": ["incident", "incidents", "what's happening", "whats happening", "current situation", "open incidents", "any issues", "situation", "alerts"],
    "task": ["my task", "my tasks", "tasks", "assignment", "assigned", "where am i needed", "shift", "what should i do next"],
    "briefing": ["briefing", "brief me", "overview", "summary", "how are things", "operational", "situation report", "sitrep", "status report", "how is the venue"],
}

# Which intents each persona can trigger, in priority-ish order.
ROLE_INTENTS = {
    "fan": ["navigation", "food", "crowd", "transport", "accessibility", "sustainability"],
    "volunteer": ["procedure", "task", "navigation", "food", "accessibility", "crowd", "transport"],
    "staff": ["incident", "procedure", "crowd", "transport", "accessibility", "briefing"],
    "organizer": ["briefing", "incident", "crowd", "transport", "sustainability"],
}

# Default intent when nothing matches, per persona.
ROLE_DEFAULT = {"fan": "general", "volunteer": "general", "staff": "incident", "organizer": "briefing"}

# Intents whose answers embed live, time-varying data — never cache these.
NON_CACHEABLE_INTENTS = {"crowd", "transport", "incident", "task", "briefing", "sustainability"}

# Strong accessibility cues win over navigation phrasing for fans/volunteers/staff.
ACCESSIBILITY_OVERRIDE = ["wheelchair", "step free", "step-free", "sensory", "disability", "disabled", "blind", "deaf"]


def classify_intent(text: str, role: str) -> str:
    low = text.lower()
    allowed = ROLE_INTENTS.get(role, ROLE_INTENTS["fan"])
    if "accessibility" in allowed and any(kw_hit(kw, low) for kw in ACCESSIBILITY_OVERRIDE):
        return "accessibility"
    best, best_hits = None, 0
    for intent in allowed:
        hits = sum(1 for kw in INTENTS[intent] if kw_hit(kw, low))
        if hits > best_hits:
            best, best_hits = intent, hits
    return best or ROLE_DEFAULT.get(role, "general")


# ---------------------------------------------------------------------------
# Retrieval helpers
# ---------------------------------------------------------------------------
def retrieve_knowledge(text: str, k: int = 2) -> list[dict]:
    low = text.lower()
    scored = []
    for entry in KNOWLEDGE_BASE:
        score = sum(1 for kw in entry["keywords"] if kw_hit(kw, low))
        if score:
            scored.append((score, entry))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [e for _, e in scored[:k]]


def _find_amenity(detail: dict, text: str) -> list[dict]:
    low = text.lower()
    type_map = {
        "restroom": ["restroom", "toilet", "bathroom"],
        "first_aid": ["first aid", "medic*", "hurt", "injured", "sick"],
        "food": ["food", "eat", "halal", "kosher", "vegan", "vegetarian", "hungry"],
        "water": ["water", "refill", "thirsty", "hydrate", "drink"],
        "prayer": ["pray", "prayer", "faith", "quiet room"],
        "sensory": ["sensory", "autism", "overwhelm"],
        "charging": ["charge", "charging", "battery", "phone"],
        "merch": ["merch", "shop", "store", "jersey", "shirt"],
        "recycling": ["recycl*", "waste", "compost", "bin"],
    }
    wanted = {t for t, kws in type_map.items() if any(kw_hit(kw, low) for kw in kws)}
    if not wanted:
        return []
    return [a for a in detail["amenities"] if a["type"] in wanted]


# ---------------------------------------------------------------------------
# Role-specific system prompts
# ---------------------------------------------------------------------------
_BASE = (
    "You are Kickoff, the official assistant for the FIFA World Cup 2026. Answer "
    "ONLY using the CONTEXT provided — never invent gate numbers, section numbers, "
    "times, procedures or policies. Be concise and practical. Reply in English."
)
ROLE_PROMPT = {
    "fan": _BASE + " You are helping a FAN enjoy their matchday: be warm and reassuring (2-4 sentences).",
    "volunteer": _BASE + " You are helping a VOLUNTEER. Give clear, calm, step-by-step guidance they can act on immediately.",
    "staff": _BASE + " You are helping VENUE STAFF manage operations. Be direct and action-oriented; lead with the priority.",
    "organizer": _BASE + " You are briefing an ORGANIZER. Summarise the operational picture and lead with recommended decisions.",
}


# ---------------------------------------------------------------------------
# Context building
# ---------------------------------------------------------------------------
def _build_context(intent: str, text: str, role: str, detail: dict | None, venue: dict | None) -> tuple[str, dict]:
    """Assemble grounding text (most-relevant first) + structured data payload."""
    primary: list[str] = []
    data: dict = {}

    # --- Fan-style grounding -------------------------------------------------
    if detail and intent in {"navigation", "food", "accessibility", "sustainability", "general"}:
        matches = _find_amenity(detail, text)
        if matches:
            data["amenities"] = matches
            for a in matches[:4]:
                q = live.amenity_queue(a["id"])
                primary.append(f"Amenity: {a['name']} — near section {a['near_section']}, {a['level']} level (current queue ~{q} people).")
        if intent == "accessibility":
            data["accessible_services"] = detail["accessible_services"]
            primary.append("Accessible services: " + " | ".join(detail["accessible_services"]))
        if intent == "navigation":
            data["gates"] = detail["gates"]
            primary.append("Gates: " + "; ".join(f"{g['name']} ({g['side']}, serves {g['serves']})" for g in detail["gates"]))

    if intent == "crowd":
        snap = live.crowd_snapshot()
        data["crowd"] = snap
        quietest = min(snap["zones"], key=lambda z: z["pct"])
        primary.append(f"Live crowd: overall {snap['overall_level']}. Busiest: {snap['busiest_zone']}. Quietest right now: {quietest['name']} ({quietest['pct']}% full).")

    if intent == "transport":
        snap = live.transport_snapshot()
        data["transport"] = snap
        primary.append("Live transport: " + "; ".join(f"{m['name']} ~{m['wait_min']} min ({m['status']})" for m in snap["modes"]) + f". Recommended: {snap['recommended']} — {snap['recommended_reason']}")

    # --- Volunteer / staff: procedures --------------------------------------
    if intent == "procedure":
        procs = find_procedure(text, role if role in {"volunteer", "staff", "organizer"} else None)
        if procs:
            p = procs[0]
            data["procedure"] = p
            steps = " ".join(f"{i+1}) {s}" for i, s in enumerate(p["steps"]))
            primary.append(f"SOP — {p['title']}: {steps}")
        else:
            primary.append("No specific SOP matched. Advise the user to radio the Command Centre for guidance.")

    # --- Staff / organizer: incidents ---------------------------------------
    if intent == "incident":
        feed = live_incidents()
        data["incidents"] = feed
        primary.append(
            f"Open incidents: {feed['total_open']} ({feed['counts']['high']} high, {feed['counts']['medium']} medium, {feed['counts']['low']} low). "
            + " | ".join(f"[{i['severity']}] {i['type']} at {i['zone']} — {i['status']} ({i['age_min']}m)" for i in feed["incidents"][:5])
        )

    # --- Volunteer: tasks ----------------------------------------------------
    if intent == "task":
        t = ops.volunteer_tasks()
        data["tasks"] = t
        primary.append(
            f"Your task list ({t['urgent_count']} urgent): "
            + " | ".join(f"[{x['priority']}] {x['title']} @ {x['zone']}" for x in t["tasks"][:5])
        )

    # --- Organizer / staff: operational briefing ----------------------------
    if intent == "briefing":
        facts, bdata = ops.briefing_facts()
        data.update(bdata)
        primary.extend(facts)

    # --- Sustainability KPIs -------------------------------------------------
    if intent == "sustainability" and role == "organizer":
        from app.data.sustainability import sustainability_snapshot
        sus = sustainability_snapshot()
        data["sustainability"] = sus
        primary.append("Sustainability KPIs: " + "; ".join(f"{m['label']} {m['value']}{m['unit']} (target {m['target']}{m['unit']})" for m in sus["metrics"]))

    # --- Supporting knowledge base ------------------------------------------
    knowledge = [f"[{e['topic']}] {e['answer']}" for e in retrieve_knowledge(text)] if intent not in {"incident", "task", "briefing"} else []

    header = []
    if venue:
        header.append(f"Venue: {venue['name']} — {venue['city']}, {venue['country']} (capacity {venue['capacity']:,}; role: {venue['role']}).")

    return "\n".join(header + primary + knowledge), data


def _fallback_reply(context: str) -> str:
    """Deterministic grounded reply when the LLM is unavailable (English)."""
    lines = [ln for ln in context.split("\n") if ln.strip()]
    body = [ln for ln in lines if not ln.startswith("Venue:")] or lines
    bullet = "\n".join(f"• {ln}" for ln in body[:5])
    return f"Here's what I found:\n{bullet}\n\nAnything else I can help with?"


# ---------------------------------------------------------------------------
# Suggested follow-up actions (per role)
# ---------------------------------------------------------------------------
_ACTIONS = {
    "fan": {
        "navigation": [("Nearest restroom", "Where is the nearest restroom?"), ("Find food", "Where can I find halal food?")],
        "crowd": [("Quietest exit", "Which gate is least busy to leave?"), ("Transport wait times", "What's the fastest way home right now?")],
        "transport": [("Accessible parking", "Where is accessible parking?"), ("Crowd levels", "How busy is the stadium right now?")],
        "accessibility": [("Sensory room", "Where is the sensory room?"), ("Step-free route", "I use a wheelchair, how do I get to my seat?")],
        "food": [("Free water", "Where can I refill water for free?"), ("Vegan options", "Where can I find vegan food?")],
        "sustainability": [("Recycling points", "Where do I recycle?"), ("Free water", "Where can I refill water for free?")],
        "general": [("Bag policy", "What can I bring into the stadium?"), ("When to arrive", "What time do gates open?")],
    },
    "volunteer": {
        "procedure": [("Medical steps", "How do I handle a medical emergency?"), ("Lost child", "What do I do for a lost child?")],
        "task": [("My tasks", "What are my current tasks?"), ("Accessibility help", "How do I assist a wheelchair user?")],
        "general": [("My tasks", "What are my current tasks?"), ("Lost child SOP", "What do I do for a lost child?")],
    },
    "staff": {
        "incident": [("Priority incident", "What is the highest priority incident?"), ("Crowd surge SOP", "How do I handle a crowd surge?")],
        "procedure": [("Evacuation steps", "What is the evacuation procedure?"), ("Crowd surge SOP", "How do I handle a crowd surge?")],
        "general": [("Current incidents", "What incidents are open right now?"), ("Crowd status", "How busy is the venue?")],
    },
    "organizer": {
        "briefing": [("Full briefing", "Give me the operational briefing"), ("Sustainability", "How are our sustainability metrics?")],
        "incident": [("Open incidents", "What incidents are open right now?"), ("Crowd status", "How busy is the venue?")],
        "general": [("Full briefing", "Give me the operational briefing"), ("Transport", "What's the transport situation?")],
    },
}


def _suggest_actions(role: str, intent: str) -> list[Action]:
    role_map = _ACTIONS.get(role, _ACTIONS["fan"])
    pairs = role_map.get(intent) or role_map.get("general") or _ACTIONS["fan"]["general"]
    return [Action(label=label, query=query) for label, query in pairs]


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------
async def handle_chat(message: str, role: str, stadium_id: str, history: list[ChatMessage]) -> ChatResponse:
    role = role if role in ROLE_INTENTS else "fan"
    intent = classify_intent(message, role)
    venue = get_venue(stadium_id)
    detail = get_detail(stadium_id)

    # --- Local cache: repeatable questions skip the LLM ---------------------
    # Keyed on (role, stadium, normalised message) so the same question returns
    # instantly regardless of conversation position. Live-data intents excluded.
    cacheable = intent not in NON_CACHEABLE_INTENTS
    cache_key = cache.make_key(f"{role}:{stadium_id}", message) if cacheable else None
    if cache_key:
        hit = await cache.get(cache_key)
        if hit is not None:
            return ChatResponse.model_validate_json(hit).model_copy(update={"cached": True})

    context, data = _build_context(intent, message, role, detail, venue)
    if not context.strip():
        context = "No specific data matched; answer generally and offer relevant help for this persona."

    convo = "\n".join(f"{m.role}: {m.content}" for m in history[-4:])
    prompt = (
        f"CONTEXT:\n{context}\n\n"
        f"CONVERSATION SO FAR:\n{convo or '(none)'}\n\n"
        f"QUESTION: {message}"
    )

    try:
        reply = await generate(ROLE_PROMPT.get(role, ROLE_PROMPT["fan"]), prompt)
        source = "llm"
    except LLMUnavailable:
        reply = _fallback_reply(context)
        source = "fallback"

    response = ChatResponse(
        reply=reply,
        role=role,
        intent=intent,
        source=source,
        cached=False,
        actions=_suggest_actions(role, intent),
        data=data or None,
    )
    if cache_key:
        await cache.set(cache_key, response.model_dump_json())
    return response


async def operational_briefing(stadium_id: str) -> dict:
    """Generate a synthesised operational briefing (used by /api/ops/briefing)."""
    facts, data = ops.briefing_facts()
    venue = get_venue(stadium_id)
    header = f"Venue: {venue['name']}." if venue else ""
    context = header + "\n" + "\n".join(facts)
    prompt = f"CONTEXT:\n{context}\n\nWrite a concise operational briefing for the duty organizer, leading with recommended actions."
    try:
        narrative = await generate(ROLE_PROMPT["organizer"], prompt)
        source = "llm"
    except LLMUnavailable:
        narrative = _fallback_reply(context)
        source = "fallback"
    return {"narrative": narrative, "source": source, "data": data}
