"""Application configuration.

Centralised settings for the Kickoff fan-assistant backend. Values are read from
environment variables so the same code runs locally, in a demo, or in prod.
"""
from __future__ import annotations

import os

# Load a local .env file if present (never committed — see .gitignore). Safe
# no-op when python-dotenv isn't installed or no .env exists.
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover
    pass


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    """Runtime settings, populated from the environment."""

    APP_NAME: str = "Kickoff — FIFA World Cup 2026 Fan Assistant"
    VERSION: str = "1.0.0"

    # Server
    HOST: str = os.getenv("KICKOFF_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("KICKOFF_PORT", "8090"))

    # CORS — the Vite dev server origins we allow by default.
    CORS_ORIGINS: list[str] = os.getenv(
        "KICKOFF_CORS_ORIGINS",
        "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173",
    ).split(",")
    # Regex origin allow-list. Defaults to any *.vercel.app deployment so the
    # frontend works once deployed without pinning the exact URL. Set to your
    # own domain in production if you want to lock it down.
    CORS_ORIGIN_REGEX: str = os.getenv("KICKOFF_CORS_ORIGIN_REGEX", r"https://.*\.vercel\.app")

    # LLM configuration. When the provider is unreachable the agent transparently
    # falls back to a deterministic template engine so demos never break.
    #   gemini  → Google Gemini API (needs GEMINI_API_KEY)
    #   ollama  → local Ollama server
    #   none    → force the grounded fallback
    LLM_PROVIDER: str = os.getenv("KICKOFF_LLM_PROVIDER", "gemini")
    LLM_TIMEOUT: float = float(os.getenv("KICKOFF_LLM_TIMEOUT", "20"))

    # Gemini. The API key is read ONLY from the environment (e.g. a Vercel
    # project secret) — never hardcode it. Note: "gemini 3.5 lite" is not a real
    # model id; the lightweight ids are gemini-2.5-flash-lite / gemini-2.0-flash-lite.
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("KICKOFF_GEMINI_MODEL", "gemini-2.5-flash-lite")
    GEMINI_BASE: str = os.getenv("GEMINI_BASE", "https://generativelanguage.googleapis.com/v1beta")

    # Ollama (local alternative).
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("KICKOFF_LLM_MODEL", "gemma2")

    # When true, crowd/transport numbers are simulated deterministically so a
    # live demo shows plausible, changing data without real sensor feeds.
    DEMO_MODE: bool = _as_bool(os.getenv("KICKOFF_DEMO_MODE"), default=True)

    # --- Auth -------------------------------------------------------------
    # Secret used to sign auth tokens. MUST be overridden in production via the
    # KICKOFF_SECRET_KEY env var (e.g. a Vercel project secret). The dev default
    # is only for local runs and is clearly marked as insecure.
    SECRET_KEY: str = os.getenv("KICKOFF_SECRET_KEY", "dev-insecure-change-me")
    TOKEN_TTL_MIN: int = int(os.getenv("KICKOFF_TOKEN_TTL_MIN", "480"))  # 8h

    # Login brute-force throttle: max attempts per IP per window (seconds).
    LOGIN_RATE_LIMIT: int = int(os.getenv("KICKOFF_LOGIN_RATE_LIMIT", "8"))
    LOGIN_RATE_WINDOW: int = int(os.getenv("KICKOFF_LOGIN_RATE_WINDOW", "60"))

    # --- Response cache ---------------------------------------------------
    # Repeated questions are served from a TTL cache instead of re-running the
    # LLM. Live-data intents are never cached (see agent.py).
    CACHE_TTL_SEC: int = int(os.getenv("KICKOFF_CACHE_TTL_SEC", "60"))
    CACHE_MAX_ENTRIES: int = int(os.getenv("KICKOFF_CACHE_MAX_ENTRIES", "512"))

    # Optional Vercel KV / Upstash Redis backend. When these are present the
    # cache uses KV (shared across serverless instances); otherwise it falls
    # back to a per-process in-memory cache. Vercel injects the KV_* vars when a
    # KV store is linked; we also accept the raw Upstash names.
    KV_REST_API_URL: str = os.getenv("KV_REST_API_URL") or os.getenv("UPSTASH_REDIS_REST_URL", "")
    KV_REST_API_TOKEN: str = os.getenv("KV_REST_API_TOKEN") or os.getenv("UPSTASH_REDIS_REST_TOKEN", "")

    # --- Firestore (persistent user store) --------------------------------
    # Optional. When configured, the auth user store is read from Firestore;
    # otherwise it falls back to the built-in demo users. Provide credentials
    # either as a file path (GOOGLE_APPLICATION_CREDENTIALS, local) or as the raw
    # service-account JSON (FIREBASE_SERVICE_ACCOUNT_JSON, good for serverless).
    FIRESTORE_PROJECT_ID: str = os.getenv("FIRESTORE_PROJECT_ID", "")
    FIREBASE_SERVICE_ACCOUNT_JSON: str = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "")
    FIRESTORE_USERS_COLLECTION: str = os.getenv("FIRESTORE_USERS_COLLECTION", "users")


settings = Settings()

