"""Security primitives: password hashing and stateless signed tokens.

Deliberately dependency-free (standard library only) so it runs anywhere,
including newer Python where some crypto wheels lag. Uses:

  * PBKDF2-HMAC-SHA256 (200k iterations) with a per-user random salt for passwords.
  * A compact JWT-style token: base64url(payload) + "." + base64url(HMAC-SHA256),
    signed with the server SECRET_KEY. Stateless and tamper-evident.

All comparisons are constant-time (`hmac.compare_digest`) to avoid timing leaks.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import os
import time

from app.core.config import settings

_PBKDF2_ROUNDS = 200_000


# ---------------------------------------------------------------------------
# Passwords
# ---------------------------------------------------------------------------
def hash_password(password: str) -> tuple[str, str]:
    """Return (salt_hex, hash_hex) for storing a new password."""
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _PBKDF2_ROUNDS)
    return binascii.hexlify(salt).decode(), binascii.hexlify(dk).decode()


def verify_password(password: str, salt_hex: str, hash_hex: str) -> bool:
    """Constant-time verification of a password against a stored salt+hash."""
    try:
        salt = binascii.unhexlify(salt_hex)
    except (binascii.Error, ValueError):
        return False
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _PBKDF2_ROUNDS)
    return hmac.compare_digest(binascii.hexlify(dk).decode(), hash_hex)


# ---------------------------------------------------------------------------
# Tokens
# ---------------------------------------------------------------------------
def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _sign(payload_b64: str) -> str:
    sig = hmac.new(settings.SECRET_KEY.encode(), payload_b64.encode(), hashlib.sha256).digest()
    return _b64url_encode(sig)


def create_token(username: str, role: str, ttl_min: int | None = None) -> tuple[str, int]:
    """Create a signed token. Returns (token, expires_at_epoch)."""
    ttl = (ttl_min if ttl_min is not None else settings.TOKEN_TTL_MIN) * 60
    exp = int(time.time()) + ttl
    payload = {"sub": username, "role": role, "exp": exp}
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    return f"{payload_b64}.{_sign(payload_b64)}", exp


def verify_token(token: str) -> dict | None:
    """Return the payload dict if the token is valid and unexpired, else None."""
    if not token or token.count(".") != 1:
        return None
    payload_b64, sig = token.split(".", 1)
    # Constant-time signature check first (reject tampering before parsing).
    if not hmac.compare_digest(sig, _sign(payload_b64)):
        return None
    try:
        payload = json.loads(_b64url_decode(payload_b64))
    except (ValueError, binascii.Error):
        return None
    if not isinstance(payload, dict) or "exp" not in payload:
        return None
    if int(payload["exp"]) < int(time.time()):
        return None
    return payload
