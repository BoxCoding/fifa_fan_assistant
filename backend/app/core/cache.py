"""TTL cache for repeated assistant answers, with a pluggable backend.

Two backends, chosen automatically:

  * **Vercel KV / Upstash Redis** (when ``KV_REST_API_URL`` + ``KV_REST_API_TOKEN``
    are set) — a shared store that survives across serverless instances, so a
    cache entry written by one Vercel function invocation is seen by the next.
  * **In-process memory** (LRU + TTL) otherwise — great for a single long-lived
    server or local dev.

Values are JSON strings (so both backends store the same thing). Callers
serialise/deserialise their own objects. All operations are async; the memory
path just doesn't await anything. Any KV error degrades gracefully to a miss /
no-op so the assistant keeps working.
"""
from __future__ import annotations

import logging
import re
import time
from collections import OrderedDict

import httpx

from app.core.config import settings
from app.core.httpclient import get_client

logger = logging.getLogger("kickoff.cache")

_WS = re.compile(r"\s+")
_hits = 0
_misses = 0

# In-memory backend: key -> (expires_at, json_string)
_store: "OrderedDict[str, tuple[float, str]]" = OrderedDict()


def make_key(role: str, message: str) -> str:
    """Normalise so trivial variations (case, spacing) hit the same entry."""
    normalised = _WS.sub(" ", message.strip().lower())
    return f"kickoff:{role}::{normalised}"


def _kv_enabled() -> bool:
    return bool(settings.KV_REST_API_URL and settings.KV_REST_API_TOKEN)


# ---------------------------------------------------------------------------
# In-memory backend
# ---------------------------------------------------------------------------
def _mem_get(key: str) -> str | None:
    entry = _store.get(key)
    if entry is None:
        return None
    expires_at, value = entry
    if expires_at < time.time():
        _store.pop(key, None)
        return None
    _store.move_to_end(key)
    return value


def _mem_set(key: str, value: str, ttl: int) -> None:
    _store[key] = (time.time() + ttl, value)
    _store.move_to_end(key)
    while len(_store) > settings.CACHE_MAX_ENTRIES:
        _store.popitem(last=False)  # evict least-recently-used


# ---------------------------------------------------------------------------
# Vercel KV / Upstash REST backend
# ---------------------------------------------------------------------------
async def _kv_command(command: list[str]):
    """Run a single Redis command via the Upstash REST API. Returns `result`."""
    headers = {"Authorization": f"Bearer {settings.KV_REST_API_TOKEN}"}  # token never logged
    resp = await get_client().post(settings.KV_REST_API_URL, json=command, headers=headers, timeout=5)
    resp.raise_for_status()
    return resp.json().get("result")


# ---------------------------------------------------------------------------
# Public async API
# ---------------------------------------------------------------------------
async def get(key: str) -> str | None:
    global _hits, _misses
    value: str | None = None
    try:
        value = await _kv_command(["GET", key]) if _kv_enabled() else _mem_get(key)
    except httpx.HTTPError as exc:
        logger.warning("cache GET failed (%s); treating as miss", exc)
        value = None
    if value is None:
        _misses += 1
    else:
        _hits += 1
    return value


async def set(key: str, value: str, ttl: int | None = None) -> None:
    ttl = settings.CACHE_TTL_SEC if ttl is None else ttl
    try:
        if _kv_enabled():
            await _kv_command(["SET", key, value, "EX", str(ttl)])
        else:
            _mem_set(key, value, ttl)
    except httpx.HTTPError as exc:
        logger.warning("cache SET failed (%s); skipping", exc)


def clear() -> None:
    """Clear the in-memory store and reset counters (does not flush remote KV)."""
    global _hits, _misses
    _store.clear()
    _hits = _misses = 0


def stats() -> dict:
    total = _hits + _misses
    return {
        "backend": "vercel-kv" if _kv_enabled() else "memory",
        "entries": None if _kv_enabled() else len(_store),
        "hits": _hits,
        "misses": _misses,
        "hit_rate": round(_hits / total, 3) if total else 0.0,
    }
