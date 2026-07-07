"""Unit tests for the TTL response cache (in-memory backend)."""
from __future__ import annotations

import asyncio
import time

from app.core import cache


def setup_function():
    cache.clear()


def test_set_get_roundtrip():
    key = cache.make_key("fan:metlife", "Where is the nearest restroom?")
    asyncio.run(cache.set(key, '{"reply": "here"}', ttl=60))
    assert asyncio.run(cache.get(key)) == '{"reply": "here"}'


def test_normalisation_collapses_variants():
    a = cache.make_key("fan", "  Where   is  the  RESTROOM? ")
    b = cache.make_key("fan", "where is the restroom?")
    assert a == b


def test_role_scopes_key():
    assert cache.make_key("fan", "x") != cache.make_key("staff", "x")


def test_ttl_expiry():
    key = cache.make_key("fan", "q")
    asyncio.run(cache.set(key, "v", ttl=0))  # expires immediately
    time.sleep(0.01)
    assert asyncio.run(cache.get(key)) is None


def test_miss_returns_none():
    assert asyncio.run(cache.get(cache.make_key("fan", "never-set"))) is None


def test_stats_track_hits_and_misses():
    cache.clear()
    key = cache.make_key("fan", "q")
    asyncio.run(cache.set(key, "1"))
    asyncio.run(cache.get(key))          # hit
    asyncio.run(cache.get("missing"))    # miss
    s = cache.stats()
    assert s["backend"] == "memory"
    assert s["hits"] == 1 and s["misses"] == 1
    assert s["hit_rate"] == 0.5


def test_lru_eviction(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "CACHE_MAX_ENTRIES", 3)
    cache.clear()
    for i in range(5):
        asyncio.run(cache.set(cache.make_key("fan", f"q{i}"), str(i)))
    # Only the 3 most-recent keys survive.
    assert asyncio.run(cache.get(cache.make_key("fan", "q0"))) is None
    assert asyncio.run(cache.get(cache.make_key("fan", "q4"))) == "4"


def test_kv_backend_selected_when_configured(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "KV_REST_API_URL", "https://example-kv.upstash.io")
    monkeypatch.setattr(settings, "KV_REST_API_TOKEN", "token")
    assert cache.stats()["backend"] == "vercel-kv"


def test_kv_failure_degrades_to_miss(monkeypatch):
    # Point KV at an unroutable host; a failed GET must degrade to a miss (None),
    # never raise — so the assistant keeps working if KV is down.
    from app.core.config import settings
    monkeypatch.setattr(settings, "KV_REST_API_URL", "http://127.0.0.1:1")
    monkeypatch.setattr(settings, "KV_REST_API_TOKEN", "token")
    assert asyncio.run(cache.get(cache.make_key("fan", "q"))) is None
