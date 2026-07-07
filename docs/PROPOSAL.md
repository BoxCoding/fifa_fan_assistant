# Kickoff — GenAI Stadium Operations & Fan Experience Platform
### Technical Proposal & Pitch · FIFA World Cup 2026

---

## 1. The Problem

The FIFA World Cup 2026 is the largest edition ever: **48 teams, 104 matches, 16
host cities across 3 countries** (USA, Canada, Mexico), and an expected **6+
million in-stadium fans**. Each venue is a small city for a day — 45,000 to 87,000
people — and matchday success depends on **four groups working in sync**:

- **Fans** need to find their seat, a restroom, food, an accessible route, or the
  fastest way home — fast, often under pressure.
- **Volunteers** — many first-timers — need to know the correct procedure the
  moment something happens, and where they're needed next.
- **Venue staff** need real-time awareness of incidents and the exact response
  steps to keep people safe.
- **Organizers** need a synthesised operational picture to make fast decisions on
  crowd flow, transport and incident response.

Today this is fragmented across static signage, printed SOP binders, radios, and
single-purpose dashboards. The result: congestion at the wrong gates, slow or
inconsistent incident response, accessibility gaps, transport bottlenecks at the
final whistle, and a coordination burden that doesn't scale.

## 2. The Solution

**Kickoff** is a GenAI platform that serves **all four personas from one
assistant**, each with a tailored knowledge base, tone, tools, and live panel —
selectable from a single role switcher.

| Persona | The assistant does… | Live panel |
|---|---|---|
| **🎟️ Fan** | Navigation, food, crowds, transport, accessibility, sustainability | Live crowd + transport |
| **🦺 Volunteer** | Step-by-step SOPs + fan support | Prioritised task list |
| **🎧 Venue Staff** | Live incidents + response procedures + crowd/transport | Incident console |
| **📋 Organizer** | Synthesised operational briefings + real-time decisions | Incidents + crowd + transport + sustainability |

### Coverage of the challenge themes

| Theme | How Kickoff delivers it |
|---|---|
| **Navigation** | Section/gate/amenity lookup + deterministic step-by-step routing, narrated by the LLM. |
| **Crowd management** | Live per-zone density; "quietest zone now" guidance for fans; redirect recommendations for staff/organizers. |
| **Accessibility** | Step-free routing, sensory room, companion facilities, ALDs; wheelchair intent is prioritized; accessibility-assist SOP for staff. |
| **Transportation** | Live wait times per mode + a recommended option; egress nudges in the organizer briefing. |
| **Sustainability** | Fan nudges (refills, zero-waste, transit) + organizer KPI dashboard vs. targets. |
| **Operational intelligence** | Live incident feed + an AI briefing synthesising crowd, transport & incidents. |
| **Real-time decision support** | Deterministic recommendations ("redirect arrivals from Gate B to Gate A; relieve surge via exits"). |

*(This build's interface is English. Multilingual output — auto-detect + reply in
the fan's language — is a designed-in extension: the agent already separates
grounding from phrasing, so adding languages is a prompt-level change, not a
re-architecture.)*

## 3. Why Generative AI (and where)

GenAI is the layer that lets **one** assistant serve **four very different users**
over messy natural-language questions — from "where's the nearest halal place that
isn't packed?" to "brief me on the venue."

We use a **grounded / retrieval-augmented** design:

```
User question + persona
   │
   ▼
[Intent classification within persona scope] ──► [Retrieve grounding]
                                                    │  knowledge base
                                                    │  live crowd / transport / incidents
                                                    │  SOP library
                                                    │  ops synthesis (tasks, briefing)
                                                    ▼
                                     [LLM generation, role-aware tone]
                                                    │
                                                    ▼
                              Grounded, actionable, persona-appropriate answer
```

The LLM **never invents** gate numbers, times, procedures or policies — it only
phrases facts pulled from structured data. For wayfinding, safety SOPs and
accessibility, that accuracy is non-negotiable.

### Graceful degradation (demo-safe by design)
If the LLM backend is unavailable, the agent **automatically falls back** to a
deterministic grounded templater that surfaces the same facts. The product
**always responds** — GenAI enhances but is never a single point of failure. The
header shows a live `LLM ●` / `Fallback ●` indicator.

## 4. Architecture

```
┌────────────────────────────┐        ┌──────────────────────────────────────────┐
│  React + Vite frontend      │        │              FastAPI backend               │
│  • role switcher (4 personas)│  HTTP │  /api/chat          → per-persona agent     │
│  • persona-specific panels   │ ─────►│  /api/crowd|transport → live simulators     │
│  • dynamic action chips      │        │  /api/incidents     → live incident feed    │
│                              │        │  /api/ops/briefing  → AI ops briefing       │
│  Fan: crowd+transport         │       │  /api/volunteer/tasks → task synthesis      │
│  Volunteer: tasks             │       │  /api/procedures    → SOP library           │
│  Staff: incidents             │       │  /api/sustainability → KPIs                 │
│  Organizer: full dashboard    │       │                                            │
└────────────────────────────┘        │  Agent = classify(persona) → retrieve →     │
                                       │          ground → generate                  │
                                       │  LLM: Ollama (Gemma) ── fallback ──┐        │
                                       │  Data: venues, amenities, KB, SOPs,│        │
                                       │        live crowd/transport/incidents       │
                                       └────────────────────────────────────┘        │
                                        (swap simulators for real sensor / transit /
                                         CV / incident-management feeds in production)
```

### Tech stack
- **Backend:** FastAPI (async), Pydantic v2, httpx
- **LLM:** Ollama running **Gemma** locally (privacy-friendly, no per-query cost),
  behind a pluggable provider interface
- **Agent:** lightweight in-house pipeline — persona-scoped intent routing → RAG
  over knowledge base + SOPs + live tools → grounded generation (LangGraph-ready)
- **Frontend:** React 18 + Vite, dev proxy to the API
- **Data:** all 16 host venues modeled; MetLife (host of the Final) fully detailed

## 5. Live Demo Script (~2 minutes)

1. **Fan** — *"Where can I find halal food?"* → names Global Kitchen near Section
   118 with the current queue length; live crowd + transport stream in the sidebar.
2. **Fan** — *"I use a wheelchair, how do I get to my seat?"* → step-free route via
   elevators at Gates A/D, sensory room, companion facilities.
3. **Volunteer** — switch persona → *"What are my current tasks?"* (urgent-first
   list) then *"How do I handle a lost child?"* → the exact SOP, step by step.
4. **Venue Staff** — switch persona → live incident console populates; ask *"How do
   I handle a crowd surge?"* → response procedure, lead with the priority.
5. **Organizer** — switch persona → *"Give me the operational briefing"* → AI
   synthesises crowd + transport + incidents into **recommended actions**
   ("relieve the surge via exits; nudge departing fans toward NJ Transit Rail");
   sustainability KPIs shown vs. targets.
6. **Resilience** — note the header `Fallback ●`: the LLM is offline yet every
   answer still works. *"It degrades gracefully — the demo never breaks."*

## 6. Impact

- **Fans:** less time lost, shorter queues, inclusive access, confident matchday.
- **Volunteers:** correct procedure on demand + clear priorities → effective from
  minute one, less reliance on scarce supervisors.
- **Staff:** real-time incident awareness + exact SOPs → faster, safer response.
- **Organizers:** synthesised situational awareness → better crowd, transport and
  safety decisions, faster.
- **Sustainability:** nudges + measurable KPIs against tournament targets.
- **Scale:** one platform, four personas, extensible to all 16 venues.

## 7. Roadmap

- **Now (this prototype):** four-persona grounded assistant; live crowd, transport,
  incidents, tasks, SOPs, ops briefing and sustainability; 16 venues, 1 fully
  detailed; LLM + safe fallback.
- **Next:** real feeds (turnstile counts, transit APIs, CV people-counting, incident
  dispatch), multilingual fan output, voice I/O for hands-free/accessible use, push
  alerts, per-fan ticket/section context.
- **Later:** predictive crowd/egress modeling, automated staff dispatch, offline
  on-device models for stadium dead-zones, full LangGraph multi-agent orchestration.

---
*Built as a working full-stack prototype: FastAPI backend + React frontend, with a
graceful LLM fallback so it runs anywhere, anytime.*
