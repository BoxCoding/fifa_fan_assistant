"""Tests for LLM provider selection and graceful fallback."""
from __future__ import annotations

import asyncio

import pytest

from app.core import llm
from app.core.config import settings
from app.core.llm import LLMUnavailable


def test_gemini_without_key_raises(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    with pytest.raises(LLMUnavailable):
        asyncio.run(llm._gemini_generate("system", "prompt"))


def test_provider_none_raises(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "none")
    with pytest.raises(LLMUnavailable):
        asyncio.run(llm.generate("system", "prompt"))


def test_health_gemini_no_key_not_reachable(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    h = asyncio.run(llm.health())
    assert h["provider"] == "gemini"
    assert h["reachable"] is False
