"""Firestore integration — the persistent user store (and easily extended).

Firestore is *optional*: the client is built lazily and any failure (library not
installed, no credentials, network error) degrades gracefully to the built-in
demo users, so the app always runs. This keeps local dev and CI dependency-free
while giving production a real database.

Enable it by installing `requirements-firestore.txt` and providing credentials:
  * local:      GOOGLE_APPLICATION_CREDENTIALS=./serviceAccount.json
  * serverless: FIREBASE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}'
plus FIRESTORE_PROJECT_ID.

User document shape (collection `users`, doc id = username):
  { "salt": "...", "hash": "...", "role": "fan|volunteer|staff|organizer", "name": "..." }
"""
from __future__ import annotations

import json
import logging

from app.core.config import settings

logger = logging.getLogger("kickoff.firestore")

# Sentinel so we build the client exactly once (None is a valid "disabled" state).
_UNSET = object()
_client_cache: object = _UNSET


def _build_client():
    try:
        from google.cloud import firestore  # lazy import — optional dependency
    except ImportError:
        logger.info("google-cloud-firestore not installed; Firestore disabled")
        return None
    try:
        if settings.FIREBASE_SERVICE_ACCOUNT_JSON:
            info = json.loads(settings.FIREBASE_SERVICE_ACCOUNT_JSON)
            return firestore.Client.from_service_account_info(info)
        if settings.FIRESTORE_PROJECT_ID:
            return firestore.Client(project=settings.FIRESTORE_PROJECT_ID)
        return firestore.Client()  # Application Default Credentials
    except Exception as exc:  # broad: any auth/config error -> graceful fallback
        logger.warning("Firestore init failed (%s); using demo user fallback", exc)
        return None


def client():
    global _client_cache
    if _client_cache is _UNSET:
        _client_cache = _build_client()
    return _client_cache


def is_enabled() -> bool:
    return client() is not None


def get_user(username: str) -> dict | None:
    """Fetch a user document, or None if missing / Firestore unavailable."""
    c = client()
    if c is None:
        return None
    try:
        doc = c.collection(settings.FIRESTORE_USERS_COLLECTION).document(username).get()
        return doc.to_dict() if doc.exists else None
    except Exception as exc:
        logger.warning("Firestore get_user failed (%s)", exc)
        return None


def upsert_user(username: str, data: dict) -> bool:
    """Create/update a user document (used by the seed script). Returns success."""
    c = client()
    if c is None:
        return False
    try:
        c.collection(settings.FIRESTORE_USERS_COLLECTION).document(username).set(data)
        return True
    except Exception as exc:
        logger.warning("Firestore upsert_user failed (%s)", exc)
        return False
