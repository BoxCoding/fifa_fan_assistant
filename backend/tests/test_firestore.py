"""Tests for the Firestore user store and its graceful fallback.

Firestore is not configured in CI, so these verify the fallback path: the app
must keep working off the built-in demo users.
"""
from __future__ import annotations

from app.core import auth, firestore


def test_firestore_disabled_without_config():
    assert firestore.is_enabled() is False


def test_get_user_returns_none_when_disabled():
    assert firestore.get_user("organizer") is None


def test_user_lookup_falls_back_to_demo_users():
    record = auth.get_user_record("organizer")
    assert record is not None
    assert record["role"] == "organizer"


def test_unknown_user_lookup_is_none():
    assert auth.get_user_record("nobody") is None


def test_firestore_preferred_when_enabled(monkeypatch):
    # Simulate an enabled Firestore returning a user; it should win over demo.
    fs_user = {"salt": "aa", "hash": "bb", "role": "staff", "name": "From Firestore"}
    monkeypatch.setattr(firestore, "is_enabled", lambda: True)
    monkeypatch.setattr(firestore, "get_user", lambda u: fs_user if u == "organizer" else None)
    assert auth.get_user_record("organizer")["name"] == "From Firestore"
    # Unknown in Firestore -> still falls back to demo store.
    assert auth.get_user_record("fan")["role"] == "fan"
