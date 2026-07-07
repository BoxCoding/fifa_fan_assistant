"""Unit tests for the authorization hierarchy and rate limiter."""
from __future__ import annotations

from app.core import ratelimit
from app.core.auth import can_access


def test_privilege_hierarchy():
    assert can_access("organizer", "fan") is True
    assert can_access("organizer", "organizer") is True
    assert can_access("staff", "volunteer") is True
    assert can_access("staff", "organizer") is False
    assert can_access("fan", "staff") is False
    assert can_access("fan", "fan") is True


def test_rate_limiter_allows_then_blocks():
    ratelimit.reset()
    key = "unit-test"
    for _ in range(3):
        assert ratelimit.check(key, limit=3, window=60) is True
    assert ratelimit.check(key, limit=3, window=60) is False


def test_rate_limiter_isolates_keys():
    ratelimit.reset()
    assert ratelimit.check("a", limit=1, window=60) is True
    assert ratelimit.check("a", limit=1, window=60) is False
    assert ratelimit.check("b", limit=1, window=60) is True  # different key unaffected


def test_rate_limiter_reset():
    ratelimit.reset()
    assert ratelimit.check("k", limit=1, window=60) is True
    ratelimit.reset()
    assert ratelimit.check("k", limit=1, window=60) is True
