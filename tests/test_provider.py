"""Tests for the LLM provider factory, fallback chain, and individual providers."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from persona_forge.llm import create_provider, _is_provider_available, _FALLBACK_CHAIN
from persona_forge.llm.provider import LLMProvider


class TestFallbackChain:
    def test_fallback_order(self):
        """Fallback chain is bedrock -> ollama -> anthropic."""
        assert _FALLBACK_CHAIN == ["bedrock", "ollama", "anthropic"]

    def test_explicit_provider_skips_fallback(self, monkeypatch):
        """Explicit --provider flag uses that provider directly."""
        monkeypatch.setenv("AWS_BEARER_TOKEN_BEDROCK", "tok")
        provider = create_provider(provider_name="bedrock")
        assert provider.name == "bedrock"

    def test_env_var_acts_as_explicit(self, monkeypatch):
        """PERSONA_FORGE_PROVIDER env var skips fallback chain."""
        monkeypatch.setenv("PERSONA_FORGE_PROVIDER", "anthropic")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "key")
        provider = create_provider()
        assert provider.name == "anthropic"

    def test_bedrock_wins_when_available(self, monkeypatch):
        """Bedrock is preferred when its token is set."""
        monkeypatch.delenv("PERSONA_FORGE_PROVIDER", raising=False)
        monkeypatch.setenv("AWS_BEARER_TOKEN_BEDROCK", "tok")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "key")
        provider = create_provider()
        assert provider.name == "bedrock"

    @patch("persona_forge.llm.ollama.is_available", return_value=True)
    def test_ollama_fallback_when_no_bedrock(self, mock_avail, monkeypatch):
        """Ollama is used when bedrock token is missing but ollama is up."""
        monkeypatch.delenv("PERSONA_FORGE_PROVIDER", raising=False)
        monkeypatch.delenv("AWS_BEARER_TOKEN_BEDROCK", raising=False)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "key")
        provider = create_provider()
        assert provider.name == "ollama"

    @patch("persona_forge.llm.ollama.is_available", return_value=False)
    def test_anthropic_fallback_when_no_bedrock_or_ollama(
        self, mock_avail, monkeypatch
    ):
        """Anthropic is used when bedrock and ollama are both unavailable."""
        monkeypatch.delenv("PERSONA_FORGE_PROVIDER", raising=False)
        monkeypatch.delenv("AWS_BEARER_TOKEN_BEDROCK", raising=False)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "key")
        provider = create_provider()
        assert provider.name == "anthropic"

    @patch("persona_forge.llm.ollama.is_available", return_value=False)
    def test_no_providers_available_raises(self, mock_avail, monkeypatch):
        """Raises ValueError when nothing is configured."""
        monkeypatch.delenv("PERSONA_FORGE_PROVIDER", raising=False)
        monkeypatch.delenv("AWS_BEARER_TOKEN_BEDROCK", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(ValueError, match="No LLM provider available"):
            create_provider()

    def test_unknown_explicit_provider_raises(self):
        """Unknown explicit provider name raises ValueError."""
        with pytest.raises(ValueError, match="Unknown provider"):
            create_provider(provider_name="nonexistent")


class TestIsProviderAvailable:
    def test_bedrock_available(self, monkeypatch):
        monkeypatch.setenv("AWS_BEARER_TOKEN_BEDROCK", "tok")
        assert _is_provider_available("bedrock") is True

    def test_bedrock_unavailable(self, monkeypatch):
        monkeypatch.delenv("AWS_BEARER_TOKEN_BEDROCK", raising=False)
        assert _is_provider_available("bedrock") is False

    def test_anthropic_available(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "key")
        assert _is_provider_available("anthropic") is True

    def test_anthropic_unavailable(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        assert _is_provider_available("anthropic") is False

    @patch("persona_forge.llm.ollama.is_available", return_value=True)
    def test_ollama_available(self, mock_avail):
        assert _is_provider_available("ollama") is True

    @patch("persona_forge.llm.ollama.is_available", return_value=False)
    def test_ollama_unavailable(self, mock_avail):
        assert _is_provider_available("ollama") is False

    def test_unknown_provider(self):
        assert _is_provider_available("unknown") is False


class TestAnthropicProvider:
    def test_without_key_raises(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(ValueError, match="API key"):
            create_provider(provider_name="anthropic")

    def test_with_key(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-123")
        provider = create_provider(provider_name="anthropic")
        assert isinstance(provider, LLMProvider)
        assert provider.name == "anthropic"


class TestBedrockProvider:
    def test_without_token_raises(self, monkeypatch):
        monkeypatch.delenv("AWS_BEARER_TOKEN_BEDROCK", raising=False)
        with pytest.raises(ValueError, match="bearer token"):
            create_provider(provider_name="bedrock")

    def test_with_token(self, monkeypatch):
        monkeypatch.setenv("AWS_BEARER_TOKEN_BEDROCK", "test-token-abc")
        provider = create_provider(provider_name="bedrock")
        assert isinstance(provider, LLMProvider)
        assert provider.name == "bedrock"

    def test_default_model(self, monkeypatch):
        monkeypatch.setenv("AWS_BEARER_TOKEN_BEDROCK", "test-token-abc")
        from persona_forge.llm.bedrock import BedrockProvider

        provider = BedrockProvider()
        assert "claude" in provider._model
        assert "anthropic" in provider._model

    def test_custom_model(self, monkeypatch):
        monkeypatch.setenv("AWS_BEARER_TOKEN_BEDROCK", "test-token-abc")
        from persona_forge.llm.bedrock import BedrockProvider

        provider = BedrockProvider(model="anthropic.claude-3-haiku-20240307-v1:0")
        assert provider._model == "anthropic.claude-3-haiku-20240307-v1:0"

    def test_custom_region(self, monkeypatch):
        monkeypatch.setenv("AWS_BEARER_TOKEN_BEDROCK", "test-token-abc")
        from persona_forge.llm.bedrock import BedrockProvider

        provider = BedrockProvider(region="us-west-2")
        assert "us-west-2" in provider._base_url

    def test_region_from_env(self, monkeypatch):
        monkeypatch.setenv("AWS_BEARER_TOKEN_BEDROCK", "test-token-abc")
        monkeypatch.setenv("AWS_BEDROCK_REGION", "eu-west-1")
        from persona_forge.llm.bedrock import BedrockProvider

        provider = BedrockProvider()
        assert "eu-west-1" in provider._base_url

    def test_default_region(self, monkeypatch):
        monkeypatch.setenv("AWS_BEARER_TOKEN_BEDROCK", "test-token-abc")
        monkeypatch.delenv("AWS_BEDROCK_REGION", raising=False)
        from persona_forge.llm.bedrock import BedrockProvider

        provider = BedrockProvider()
        assert "us-east-1" in provider._base_url


class TestOllamaProvider:
    def test_creates_with_defaults(self):
        from persona_forge.llm.ollama import OllamaProvider

        provider = OllamaProvider()
        assert provider.name == "ollama"
        assert "localhost" in provider._host
        assert "11434" in provider._host

    def test_custom_host(self):
        from persona_forge.llm.ollama import OllamaProvider

        provider = OllamaProvider(host="http://my-server:11434")
        assert "my-server" in provider._host

    def test_host_from_env(self, monkeypatch):
        monkeypatch.setenv("OLLAMA_HOST", "http://remote:11434")
        from persona_forge.llm.ollama import OllamaProvider

        provider = OllamaProvider()
        assert "remote" in provider._host

    def test_custom_model(self):
        from persona_forge.llm.ollama import OllamaProvider

        provider = OllamaProvider(model="codellama")
        assert provider._model == "codellama"
