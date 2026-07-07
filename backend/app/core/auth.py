"""Authentication: user store, credential check, and the auth dependency.

The demo user store holds ONLY salted PBKDF2 hashes — never plaintext passwords
— so no credential secret lives in source. For real deployments, override the
store via the KICKOFF_USERS env var (JSON: username -> {salt, hash, role, name}).

Demo credentials are documented in the README, not here.
"""
from __future__ import annotations

import json
import os

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core import firestore
from app.core.security import verify_password, verify_token

# username -> {salt, hash, role, name}. Passwords are all the documented demo
# password; only their salted hashes are stored here.
_DEFAULT_USERS: dict[str, dict] = {
    "organizer": {"salt": "3f885a227a17556cad241df75d88a12d", "hash": "ab5c1d6e9392b5793562d8d363abeb6cd1aa7844aaecdf8c274977556b0b09b3", "role": "organizer", "name": "Match Organizer"},
    "staff": {"salt": "26e2de73bce870c515fd1c73db1e599d", "hash": "ee428034d26730df0b24b176208a0d9c4d5fbc6c8cbe97f257b5e0ad54be4c90", "role": "staff", "name": "Venue Staff"},
    "volunteer": {"salt": "d7a09db19a9517753479dd4394677188", "hash": "89c054decfc6659609408993ad179279d6f5490fda702f54b20d9b421cddf7b7", "role": "volunteer", "name": "Volunteer"},
    "fan": {"salt": "821bc056335149ef3a12a84ab8bc7244", "hash": "bf694c26c9338a816f8fd00c396eddf3d67dea8ce43ec775eeffa4089ed94d14", "role": "fan", "name": "Fan"},
}


def _load_users() -> dict[str, dict]:
    raw = os.getenv("KICKOFF_USERS")
    if not raw:
        return _DEFAULT_USERS
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    return _DEFAULT_USERS


USERS = _load_users()

_bearer = HTTPBearer(auto_error=False)

# Privilege hierarchy: a higher-level user may act in any lower-level persona.
# organizer ⊇ staff ⊇ volunteer ⊇ fan. This gates both the chat `role` param and
# the staff/organizer-only data endpoints.
ROLE_LEVEL = {"fan": 0, "volunteer": 1, "staff": 2, "organizer": 3}


def can_access(user_role: str, target_role: str) -> bool:
    return ROLE_LEVEL.get(user_role, 0) >= ROLE_LEVEL.get(target_role, 99)


def get_user_record(username: str) -> dict | None:
    """Look up a user, preferring Firestore, then the built-in demo store."""
    if firestore.is_enabled():
        record = firestore.get_user(username)
        if record:
            return record
    return USERS.get(username)


def authenticate(username: str, password: str) -> dict | None:
    """Return a public user dict if credentials are valid, else None."""
    record = get_user_record(username)
    if not record:
        # Still run a verify to keep timing roughly constant for unknown users.
        verify_password(password, "00" * 16, "00" * 32)
        return None
    if not verify_password(password, record["salt"], record["hash"]):
        return None
    return {"username": username, "role": record["role"], "name": record["name"]}


async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict:
    """FastAPI dependency: require a valid Bearer token, return the token payload."""
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = verify_token(creds.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


def require_role(target: str):
    """Dependency factory: require the caller to have >= `target` privilege."""

    async def checker(payload: dict = Depends(get_current_user)) -> dict:
        if not can_access(payload.get("role", "fan"), target):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {target}-level access",
            )
        return payload

    return checker
