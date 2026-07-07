"""Unit tests for password hashing and signed tokens."""
from __future__ import annotations

import time

from app.core import security


def test_password_hash_roundtrip():
    salt, digest = security.hash_password("s3cret-pw")
    assert security.verify_password("s3cret-pw", salt, digest) is True
    assert security.verify_password("wrong", salt, digest) is False


def test_password_hash_is_salted():
    s1, h1 = security.hash_password("same")
    s2, h2 = security.hash_password("same")
    assert (s1, h1) != (s2, h2)  # different salts -> different hashes


def test_verify_password_bad_salt():
    assert security.verify_password("x", "not-hex!!", "deadbeef") is False


def test_token_roundtrip():
    token, exp = security.create_token("alice", "organizer")
    assert exp > time.time()
    payload = security.verify_token(token)
    assert payload is not None
    assert payload["sub"] == "alice"
    assert payload["role"] == "organizer"


def test_token_tampering_rejected():
    token, _ = security.create_token("alice", "fan")
    payload_b64, sig = token.split(".")
    tampered = payload_b64[:-1] + ("A" if payload_b64[-1] != "A" else "B") + "." + sig
    assert security.verify_token(tampered) is None


def test_token_expired_rejected():
    token, _ = security.create_token("bob", "staff", ttl_min=-1)  # already expired
    assert security.verify_token(token) is None


def test_token_garbage_rejected():
    assert security.verify_token("") is None
    assert security.verify_token("no-dot") is None
    assert security.verify_token("a.b.c") is None
