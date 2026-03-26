"""Tests for the LLM provider factory and related utilities."""

from __future__ import annotations

import pytest

from persona_forge.llm import create_provider
from persona_forge.llm.provider import LLMProvider


class TestCreateProvider:
    def test_unknown_provider_raises(self):
        """Unknown provider name raises ValueError."""
        with pytest.raises(ValueError, match="Unknown provider"):
            create_provider(provider_name="nonexistent")

    def test_anthropic_without_key_raises(self, monkeypatch):
        """Anthropic provider without API key raises ValueError."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(ValueError, match="API key"):
            create_provider(provider_name="anthropic")

    def test_anthropic_with_key(self, monkeypatch):
        """Anthropic provider with API key creates successfully."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-123")
        provider = create_provider(provider_name="anthropic")
        assert isinstance(provider, LLMProvider)
        assert provider.name == "anthropic"

    def test_default_provider_is_anthropic(self, monkeypatch):
        """Default provider is anthropic."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-123")
        monkeypatch.setenv("PERSONA_FORGE_PROVIDER", "anthropic")
        provider = create_provider()
        assert provider.name == "anthropic"
