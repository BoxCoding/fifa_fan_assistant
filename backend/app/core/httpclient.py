"""A shared, connection-pooled httpx client for outbound calls.

Reusing one client (Gemini, Ollama, Vercel KV) avoids a fresh TCP + TLS
handshake on every request — a real latency/CPU win under load. Per-request
timeouts are still passed at call sites. Closed on app shutdown (see main.py).
"""
from __future__ import annotations

import httpx

_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=50),
        )
    return _client


async def aclose() -> None:
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
    _client = None
