"""Tests for LLM success paths using a mocked HTTP client (no network)."""
from __future__ import annotations

import asyncio

from app.core import agent, cache, llm
from app.core.config import settings


class _FakeResp:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self._data


class _FakeClient:
    def __init__(self, data):
        self._data = data

    async def post(self, *args, **kwargs):
        return _FakeResp(self._data)

    async def get(self, *args, **kwargs):
        return _FakeResp(self._data)


def _use_fake(monkeypatch, data):
    # llm.py imports get_client into its own namespace, so patch it there.
    monkeypatch.setattr(llm, "get_client", lambda: _FakeClient(data))


def test_gemini_generate_parses_text(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-key")
    _use_fake(monkeypatch, {"candidates": [{"content": {"parts": [{"text": "Hello fan"}]}}]})
    out = asyncio.run(llm._gemini_generate("system", "prompt"))
    assert out == "Hello fan"


def test_gemini_health_reachable_with_key(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-key")
    _use_fake(monkeypatch, {"models": []})
    h = asyncio.run(llm.health())
    assert h["reachable"] is True


def test_ollama_generate_parses_text(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "ollama")
    _use_fake(monkeypatch, {"response": "Ollama says hi"})
    out = asyncio.run(llm.generate("system", "prompt"))
    assert out == "Ollama says hi"


def test_agent_uses_llm_when_available(monkeypatch):
    cache.clear()

    async def fake_generate(system, prompt):
        return "LLM-authored reply"

    monkeypatch.setattr(agent, "generate", fake_generate)
    r = asyncio.run(agent.handle_chat("Where is the nearest restroom?", "fan", "metlife", []))
    assert r.source == "llm"
    assert r.reply == "LLM-authored reply"
