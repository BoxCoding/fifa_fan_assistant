"""Lightweight in-memory sliding-window rate limiter.

Used to throttle login attempts (brute-force protection). Per-process, so on
serverless it's best-effort per instance — front it with a shared store (KV) or
an edge/WAF rule for hard guarantees. Good enough to demonstrate the control and
to protect a single long-lived server.
"""
from __future__ import annotations

import time
from collections import defaultdict, deque

_hits: dict[str, deque[float]] = defaultdict(deque)


def check(key: str, limit: int, window: int) -> bool:
    """Return True if `key` is under `limit` events per `window` seconds.

    Records the attempt when allowed. Returns False (blocked) when the limit is
    reached.
    """
    now = time.time()
    dq = _hits[key]
    cutoff = now - window
    while dq and dq[0] <= cutoff:
        dq.popleft()
    if len(dq) >= limit:
        return False
    dq.append(now)
    return True


def reset() -> None:
    _hits.clear()
