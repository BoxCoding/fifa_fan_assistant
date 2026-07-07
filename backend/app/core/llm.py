"""LLM client with graceful degradation.

Primary path: a local Ollama server running a Gemma model. If Ollama is
unreachable (common in a demo/CI environment), callers get a clean signal so
the agent can fall back to a deterministic template engine. This guarantees the
product always responds — the GenAI layer enhances, but never blocks, the UX.
"""
from __future__ import annotations

import logging

import httpx

from app.core.config import settings
from app.core.httpclient import get_client

logger = logging.getLogger("kickoff.llm")


class LLMUnavailable(Exception):
    """Raised when no generative backend can serve the request."""


async def generate(system: str, prompt: str) -> str:
    """Return a completion string, or raise LLMUnavailable.

    Kept intentionally small: one system prompt + one user prompt. The agent is
    responsible for assembling grounding context into ``prompt``.
    """
    if settings.LLM_PROVIDER == "none":
        raise LLMUnavailable("LLM provider disabled by configuration")

    if settings.LLM_PROVIDER == "gemini":
        return await _gemini_generate(system, prompt)

    if settings.LLM_PROVIDER == "ollama":
        return await _ollama_generate(system, prompt)

    raise LLMUnavailable(f"Unknown LLM provider: {settings.LLM_PROVIDER}")


async def _gemini_generate(system: str, prompt: str) -> str:
    if not settings.GEMINI_API_KEY:
        raise LLMUnavailable("GEMINI_API_KEY is not set")
    url = f"{settings.GEMINI_BASE}/models/{settings.GEMINI_MODEL}:generateContent"
    payload = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 512},
    }
    headers = {
        "x-goog-api-key": settings.GEMINI_API_KEY,  # key sent as header, never logged
        "Content-Type": "application/json",
    }
    try:
        resp = await get_client().post(url, json=payload, headers=headers, timeout=settings.LLM_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        candidates = data.get("candidates") or []
        if not candidates:
            raise LLMUnavailable("Gemini returned no candidates")
        parts = candidates[0].get("content", {}).get("parts", [])
        text = "".join(p.get("text", "") for p in parts).strip()
        if not text:
            raise LLMUnavailable("Empty response from Gemini")
        return text
    except (httpx.HTTPError, LLMUnavailable) as exc:
        logger.warning("Gemini generation failed (%s); using fallback", exc)
        raise LLMUnavailable(str(exc)) from exc


async def _ollama_generate(system: str, prompt: str) -> str:
    url = f"{settings.OLLAMA_HOST}/api/generate"
    payload = {
        "model": settings.OLLAMA_MODEL,
        "system": system,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.3},
    }
    try:
        resp = await get_client().post(url, json=payload, timeout=settings.LLM_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        text = (data.get("response") or "").strip()
        if not text:
            raise LLMUnavailable("Empty response from Ollama")
        return text
    except (httpx.HTTPError, LLMUnavailable) as exc:
        logger.warning("Ollama generation failed (%s); using fallback", exc)
        raise LLMUnavailable(str(exc)) from exc


async def health() -> dict:
    """Report whether the generative backend is reachable (for /health)."""
    provider = settings.LLM_PROVIDER
    if provider == "none":
        return {"provider": "none", "reachable": False, "model": None}

    if provider == "gemini":
        if not settings.GEMINI_API_KEY:
            return {"provider": "gemini", "reachable": False, "model": settings.GEMINI_MODEL}
        try:
            resp = await get_client().get(
                f"{settings.GEMINI_BASE}/models",
                headers={"x-goog-api-key": settings.GEMINI_API_KEY},
                timeout=3,
            )
            resp.raise_for_status()
            return {"provider": "gemini", "reachable": True, "model": settings.GEMINI_MODEL}
        except httpx.HTTPError:
            return {"provider": "gemini", "reachable": False, "model": settings.GEMINI_MODEL}

    # ollama
    try:
        resp = await get_client().get(f"{settings.OLLAMA_HOST}/api/tags", timeout=3)
        resp.raise_for_status()
        return {"provider": "ollama", "reachable": True, "model": settings.OLLAMA_MODEL}
    except httpx.HTTPError:
        return {"provider": "ollama", "reachable": False, "model": settings.OLLAMA_MODEL}
