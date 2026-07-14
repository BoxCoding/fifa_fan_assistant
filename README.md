# ⚽ Kickoff — FIFA World Cup 2026 Stadium Operations & Fan Experience Platform

A GenAI-powered platform that serves **four personas** — fans, volunteers, venue
staff and organizers — from one assistant, covering navigation, crowd management,
accessibility, transportation, sustainability, operational intelligence and
real-time decision support during the FIFA World Cup 2026. Every answer is grounded
in live venue data. English-language interface.

> **Pitch & architecture:** see [`docs/PROPOSAL.md`](docs/PROPOSAL.md).

![stack](https://img.shields.io/badge/backend-FastAPI-009688) ![stack](https://img.shields.io/badge/frontend-React%20%2B%20Vite-61dafb) ![stack](https://img.shields.io/badge/LLM-Gemini-7c5cff)

---

## Problem statement & how we address it

> **Build a GenAI-enabled solution that enhances stadium operations and the overall
> tournament experience for fans, organizers, volunteers, or venue staff — leveraging
> Generative AI to improve navigation, crowd management, accessibility, transportation,
> sustainability, multilingual assistance, operational intelligence, or real-time
> decision support during the FIFA World Cup 2026.**

Kickoff addresses **every** listed capability, for **all four** audiences, through one
grounded GenAI assistant:

| Challenge capability | How Kickoff delivers it | Where |
|---|---|---|
| **Navigation** | Section/gate/amenity lookup + step-by-step (accessible) routing narrated by the LLM | `/api/navigate`, agent `navigation` intent |
| **Crowd management** | Live per-zone density + "quietest zone now"; redirect recommendations for staff | `/api/crowd`, `data/live.py`, briefing |
| **Accessibility** | Step-free routes, sensory room, companion facilities; wheelchair intent prioritised; a11y-first UI | agent `accessibility`, `data/stadiums.py` |
| **Transportation** | Live per-mode wait times + recommended option; egress nudges in the briefing | `/api/transport` |
| **Sustainability** | Fan nudges (refill/recycle/transit) + organizer KPI dashboard vs. targets | `data/sustainability.py` |
| **Operational intelligence** | Live incident feed + AI briefing synthesising crowd + transport + incidents | `/api/incidents`, `/api/ops/briefing` |
| **Real-time decision support** | Deterministic, grounded recommended actions surfaced to staff/organizers | `data/ops.py` |

**Audiences served:** 🎟️ Fans · 🦺 Volunteers · 🎧 Venue staff · 📋 Organizers — each with a
tailored assistant, live panel, and role-scoped access.

---

## Four personas, one platform

| Persona | Assistant focus | Live panel |
|---|---|---|
| **🎟️ Fan** | Navigation, food (halal/kosher/vegan), crowds, transport, accessibility, sustainability | Live crowd + transport |
| **🦺 Volunteer** | Step-by-step SOPs + fan support | Prioritised task list |
| **🎧 Venue Staff** | Live incidents + response procedures + crowd/transport | Incident console |
| **📋 Organizer** | Synthesised operational briefings + real-time decisions | Incidents + crowd + transport + sustainability |

## What it does

- **Multi-persona GenAI assistant** — one agent adapts its knowledge, tone and tools
  to the active persona.
- **Navigation & amenities** — nearest restroom, food, first aid, water, prayer &
  sensory rooms, with live queue estimates and step-by-step routing.
- **Crowd management** — per-zone density with the quietest zone right now.
- **Transport intelligence** — live wait times per mode + a recommendation.
- **Accessibility-first** — step-free routing, sensory room, companion facilities;
  wheelchair queries are prioritized.
- **Operational intelligence & real-time decision support** — live incident feed +
  an AI briefing that synthesises crowd, transport and incidents into recommended
  actions for organizers.
- **Volunteer enablement** — SOP guidance (lost child, medical, evacuation, etc.)
  and a live, urgent-first task list.
- **Sustainability** — fan nudges (refills, recycling, transit) + organizer KPIs.
- **Grounded GenAI** — the LLM only phrases facts from structured data, so it never
  invents gates, times, procedures or policies.
- **Graceful fallback** — if the LLM is offline, a deterministic grounded templater
  keeps everything working. **The demo never breaks.**
- **Login authentication + authorization** — token-gated access; PBKDF2-salted
  passwords, stateless HMAC-signed tokens, secret from an env var, **role-based
  authorization** (privilege hierarchy), and **login rate-limiting**. No plaintext
  credential or secret lives in source.
- **Efficient transport** — gzip-compressed responses and a pooled, reused HTTP
  client for outbound LLM/KV calls (no per-request TLS handshake).
- **Local response cache** — repeated questions are served from an in-process TTL
  cache instead of re-running the LLM (faster + cheaper). Live-data intents
  (crowd, transport, incidents, briefings, KPIs) are never cached, so answers are
  never stale. Cached replies are flagged with a ⚡ badge.

## Architecture

```
React + Vite frontend  ──HTTP──►  FastAPI backend
  • role switcher                  /api/chat            (agent: classify→retrieve→ground→generate, per persona)
  • persona-specific panels        /api/crowd           (live crowd simulator)
  • dynamic action chips           /api/transport       (transport intelligence)
                                   /api/incidents       (live incident feed)
                                   /api/ops/briefing    (AI operational briefing)
                                   /api/volunteer/tasks  (task list)
                                   /api/procedures      (SOP lookup)
                                   /api/sustainability  (KPIs)
                                   /api/navigate        (deterministic routing)
                                   LLM: Gemini (or Ollama) with safe fallback
```

## Prerequisites

- Python 3.11+ (tested on 3.14)
- Node.js 18+
- **For AI-generated replies:** a Google **Gemini** API key. Set it as an env var
  (never hardcode it):
  ```bash
  export GEMINI_API_KEY="your-key-here"   # or a Vercel project secret
  ```
  The default model is `gemini-2.5-flash-lite` (override with `KICKOFF_GEMINI_MODEL`).
  *(Alternatively set `KICKOFF_LLM_PROVIDER=ollama` and run [Ollama](https://ollama.com)
  with `ollama pull gemma2`.)* **With no key/provider reachable, the app runs on the
  grounded fallback — the chat still works, it just isn't LLM-phrased.**

## Configuration files

Copy the example env files and fill in your values. **`.env` is git-ignored — never
commit real secrets** (the repo `.gitignore` also excludes service-account keys):

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

The backend auto-loads `backend/.env` (via python-dotenv); Vite auto-loads
`frontend/.env`.

## Run it

### 1. Backend (port 8090)
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8090
```
API docs at http://localhost:8090/docs · health at http://localhost:8090/health

### 2. Frontend (port 5173)
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173 . The Vite dev server proxies `/api` and `/health` to
the backend automatically.

## Configuration (env vars)

| Variable | Default | Purpose |
|---|---|---|
| `KICKOFF_PORT` | `8090` | Backend port |
| `KICKOFF_LLM_PROVIDER` | `gemini` | `gemini`, `ollama`, or `none` (force fallback) |
| `GEMINI_API_KEY` | *(empty)* | Google Gemini API key — **set via env/secret, never in source** |
| `KICKOFF_GEMINI_MODEL` | `gemini-2.5-flash-lite` | Gemini model id |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama endpoint (if using ollama) |
| `KICKOFF_LLM_MODEL` | `gemma2` | Ollama model name |
| `KICKOFF_DEMO_MODE` | `true` | Simulated live crowd/transport data |
| `KICKOFF_SECRET_KEY` | `dev-insecure-change-me` | **Set in production** — signs auth tokens (use a Vercel/host secret) |
| `KICKOFF_TOKEN_TTL_MIN` | `480` | Auth token lifetime (minutes) |
| `KICKOFF_LOGIN_RATE_LIMIT` | `8` | Max login attempts per IP per window |
| `KICKOFF_LOGIN_RATE_WINDOW` | `60` | Login rate-limit window (seconds) |
| `KICKOFF_CACHE_TTL_SEC` | `60` | Response cache TTL |
| `KICKOFF_CORS_ORIGINS` | *(localhost)* | Comma-separated allowed origins (add your frontend URL in prod) |
| `KV_REST_API_URL` / `KV_REST_API_TOKEN` | *(empty)* | Vercel KV / Upstash Redis — enables the shared cache backend |
| `KICKOFF_USERS` | *(demo users)* | JSON override of the user store (`{username: {salt, hash, role, name}}`) |

## Authentication

The app is login-gated. Demo accounts (all use password **`kickoff2026`**). Access
follows a **privilege hierarchy** — a higher role can act in any lower persona, so
**sign in as `organizer` to explore all four personas**:

| Username | Level | Can access personas |
|---|---|---|
| `organizer` | 3 | fan, volunteer, staff, organizer |
| `staff` | 2 | fan, volunteer, staff |
| `volunteer` | 1 | fan, volunteer |
| `fan` | 0 | fan |

Security notes:
- Passwords: **PBKDF2-HMAC-SHA256 (200k rounds) salted hashes** — no plaintext in source.
- Tokens: **stateless HMAC-SHA256-signed** (JWT-style), constant-time verified, signed
  with `KICKOFF_SECRET_KEY` (set via a host secret in prod; never commit it).
- **Role-based authorization:** the chat `role` and the staff/organizer-only endpoints
  (`/api/incidents`, `/api/ops/briefing`, `/api/sustainability`, `/api/volunteer/tasks`,
  `/api/procedures`) are gated by the hierarchy above — unauthorized → `403`. The UI
  only shows persona tabs you're allowed to use.
- **Login rate-limiting:** brute-force attempts are throttled per IP (`429` after
  `KICKOFF_LOGIN_RATE_LIMIT` tries per `KICKOFF_LOGIN_RATE_WINDOW`s).
- Login is generic on failure (no username enumeration).

### User store: Firestore (optional, with fallback)

The user store reads from **Google Cloud Firestore** when configured, and
transparently falls back to the built-in demo users otherwise — so local dev and
CI need no database. Enable it:

```bash
pip install -r requirements-firestore.txt      # optional dependency
# credentials — either:
export GOOGLE_APPLICATION_CREDENTIALS=./serviceAccount.json   # local key file
# or (serverless): set FIREBASE_SERVICE_ACCOUNT_JSON to the raw JSON
export FIRESTORE_PROJECT_ID=your-gcp-project

python -m scripts.seed_firestore               # seed the demo users (hashed)
python -m scripts.seed_firestore alice s3cret organizer "Alice"   # add one user
```

Users live in the `users` collection (doc id = username), shape
`{salt, hash, role, name}`. Passwords are hashed before writing — plaintext never
reaches the database. Any Firestore/credential error degrades gracefully to the
demo store, and `/health`-time auth keeps working.

## API reference

All `/api/*` endpoints except `/api/auth/login` require an `Authorization: Bearer
<token>` header (obtained from login). `/health` and `/` are public.

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/login` | Exchange `{username, password}` for a signed token |
| `GET` | `/api/auth/me` | Current user (validates the token) |
| `POST` | `/api/chat` | Main assistant. Body: `{message, role, stadium_id, history}` — `role` ∈ fan/volunteer/staff/organizer. Response includes `cached` |
| `GET` | `/api/roles` | Available personas |
| `GET` | `/api/venues` | All 16 host venues |
| `GET` | `/api/stadium/{id}` | Venue + detailed layout |
| `GET` | `/api/amenities/{id}?type=` | Amenities (+ live queue) |
| `GET` | `/api/crowd/{id}` | Live crowd snapshot |
| `GET` | `/api/transport/{id}` | Live transport snapshot |
| `GET` | `/api/incidents/{id}` | Live incident feed + severity counts |
| `GET` | `/api/ops/briefing/{id}` | AI operational briefing + recommendations |
| `GET` | `/api/volunteer/tasks` | Prioritised volunteer task list |
| `GET` | `/api/procedures?role=&q=` | SOP lookup |
| `GET` | `/api/sustainability/{id}` | Sustainability KPIs |
| `POST` | `/api/navigate` | Step-by-step (optionally accessible) route |
| `GET` | `/health` | Status + LLM reachability |

### Example
```bash
# 1) Log in to get a token
TOKEN=$(curl -s -X POST localhost:8090/api/auth/login -H 'Content-Type: application/json' \
  -d '{"username":"organizer","password":"kickoff2026"}' | python -c "import sys,json;print(json.load(sys.stdin)['token'])")

# 2) Call the assistant with the token
curl -X POST localhost:8090/api/chat -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message":"Give me the operational briefing","role":"organizer"}'
```

## Tests

```bash
cd backend && source .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest -q                          # 79 tests
python -m pytest --cov=app --cov-report=term-missing   # with coverage (~90%)

# Linting / formatting
ruff check .                                 # backend (Python)
cd ../frontend && npm run lint               # frontend (ESLint)
```
Covers: security (hashing/tokens), authorization hierarchy, rate limiting, cache
(incl. KV selection + degradation), LLM provider selection + success paths,
Firestore fallback, every agent intent, all stadium/transport/ops endpoints, and
full auth + chat API integration.

## Deploy to Vercel

Deploy backend and frontend as **two Vercel projects** from this one repo.

### Backend (FastAPI → serverless)
- `backend/api/index.py` exposes the ASGI `app`; `backend/vercel.json` rewrites
  every route to it. `requirements.txt` holds runtime deps only (tests excluded).
- In Vercel: **New Project → Root Directory = `backend`**.
- Set environment variables:
  - `GEMINI_API_KEY` — your Gemini key (Vercel encrypts it)
  - `KICKOFF_SECRET_KEY` — a long random string (signs auth tokens)
  - CORS: any `*.vercel.app` origin is allowed by default (`KICKOFF_CORS_ORIGIN_REGEX`),
    so cross-origin login works out of the box. To lock it down, set
    `KICKOFF_CORS_ORIGINS` to your exact frontend URL and clear the regex.
  - **After deploying, sanity-check** `https://<backend>.vercel.app/health` returns JSON.
  - *(optional, Firestore user store)* `FIRESTORE_PROJECT_ID` +
    `FIREBASE_SERVICE_ACCOUNT_JSON` (paste the service-account JSON), and add
    `google-cloud-firestore` to `requirements.txt` for the deployed build
- **Shared cache:** in the project's **Storage** tab, create a **KV** store and
  link it. Vercel injects `KV_REST_API_URL` + `KV_REST_API_TOKEN`, and the cache
  automatically switches from per-instance memory to the shared KV backend
  (confirm via `/health` → `cache.backend: "vercel-kv"`). This matters on
  serverless, where in-memory caches don't survive between invocations.

### Frontend (Vite → static)
- In Vercel: **New Project → Root Directory = `frontend`** (framework preset: Vite).
- Set `VITE_API_BASE` to the backend URL (e.g. `https://kickoff-api.vercel.app`)
  so the app calls the deployed API instead of the local dev proxy.

> Locally nothing changes: leave `VITE_API_BASE` and the `KV_*` vars unset — the
> app uses the Vite proxy and the in-memory cache.

## Project layout

```
worldcup-fan-assistant/
├── backend/
│   └── app/
│       ├── main.py            # FastAPI app + routes
│       ├── models.py          # Pydantic schemas (personas)
│       ├── core/
│       │   ├── config.py      # env-driven settings (LLM, auth, cache)
│       │   ├── llm.py         # Ollama client + graceful fallback
│       │   ├── security.py    # PBKDF2 password hashing + signed tokens
│       │   ├── auth.py        # user store + auth + role-based authorization
│       │   ├── firestore.py   # optional Firestore user store (graceful fallback)
│       │   ├── ratelimit.py   # login brute-force throttle
│       │   ├── httpclient.py  # shared pooled httpx client (efficiency)
│       │   ├── cache.py       # TTL response cache (memory ↔ Vercel KV)
│       │   ├── matching.py    # word-boundary / stem keyword matcher
│       │   └── agent.py       # per-persona: classify → cache → retrieve → ground → generate
│       ├── data/
│       │   ├── stadiums.py    # 16 venues + detailed MetLife layout
│       │   ├── knowledge.py   # curated fan knowledge base (RAG source)
│       │   ├── procedures.py  # volunteer/staff SOPs
│       │   ├── incidents.py   # simulated live incident feed
│       │   ├── sustainability.py # sustainability KPIs
│       │   ├── ops.py         # tasks + operational-briefing synthesis
│       │   └── live.py        # simulated real-time crowd/transport
│       ├── routers/           # auth / chat / stadium / transport / ops
│       ├── tests/             # pytest: security, cache, LLM, firestore, auth + chat
│       ├── scripts/seed_firestore.py  # seed the Firestore users collection
│       ├── api/index.py       # Vercel serverless entrypoint (ASGI app)
│       ├── vercel.json        # Vercel routing (all routes → api/index)
│       └── .env.example       # backend env template (copy to .env)
├── frontend/
│   └── src/
│       ├── App.jsx            # auth gate + role switcher + chat UI
│       ├── api.js             # API client (attaches Bearer token)
│       ├── auth.js            # token/user persistence
│       └── components/
│           ├── Login.jsx         # accessible login screen
│           ├── LiveOps.jsx       # crowd + transport (fan/organizer)
│           ├── Incidents.jsx     # incident console (staff/organizer)
│           ├── Tasks.jsx         # volunteer task list
│           └── Sustainability.jsx # organizer KPIs
└── docs/PROPOSAL.md           # technical proposal & pitch
```

## Notes on the demo data

`app/data/live.py` deterministically **simulates** crowd density and transport
wait times so the UI shows plausible, changing data without real sensor feeds.
In production, swap those functions for real turnstile counts, transit APIs, and
CV people-counting — the rest of the stack is unchanged.
