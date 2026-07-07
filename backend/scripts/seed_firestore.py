"""Seed the Firestore `users` collection.

Usage (from backend/, with Firestore configured + credentials set):
    python -m scripts.seed_firestore                       # seed the 4 demo users
    python -m scripts.seed_firestore alice s3cret organizer "Alice A."   # one user

Passwords are hashed (PBKDF2 salted) before writing — plaintext never lands in
the database. Requires: pip install -r requirements-firestore.txt
"""
from __future__ import annotations

import sys

from app.core import firestore
from app.core.security import hash_password

# username -> (password, role, display name)
DEMO = {
    "organizer": ("kickoff2026", "organizer", "Match Organizer"),
    "staff": ("kickoff2026", "staff", "Venue Staff"),
    "volunteer": ("kickoff2026", "volunteer", "Volunteer"),
    "fan": ("kickoff2026", "fan", "Fan"),
}


def _write(username: str, password: str, role: str, name: str) -> None:
    salt, digest = hash_password(password)
    ok = firestore.upsert_user(username, {"salt": salt, "hash": digest, "role": role, "name": name})
    print(f"{'✓' if ok else '✗'} {username} ({role})")


def main(argv: list[str]) -> int:
    if not firestore.is_enabled():
        print("Firestore is not configured. Set credentials + FIRESTORE_PROJECT_ID "
              "and install requirements-firestore.txt.")
        return 1
    if len(argv) == 4:
        username, password, role, name = argv[0], argv[1], argv[2], argv[3]
        _write(username, password, role, name)
    elif not argv:
        for username, (password, role, name) in DEMO.items():
            _write(username, password, role, name)
    else:
        print("Usage: python -m scripts.seed_firestore [username password role \"name\"]")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
