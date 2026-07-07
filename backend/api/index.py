"""Vercel serverless entrypoint.

Vercel's @vercel/python runtime detects the ASGI ``app`` exported here and wraps
it as a serverless function. All routes are rewritten to this file (see
vercel.json), so FastAPI handles the full path (`/api/chat`, `/health`, ...).

Deploy with Root Directory = `backend` in the Vercel project settings.
"""
from app.main import app  # noqa: F401  (re-exported for the Vercel runtime)
