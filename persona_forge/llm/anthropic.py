"""Anthropic (Claude) LLM provider.

POC scope: single provider implementation using httpx.
"""

from __future__ import annotations

import os

import httpx

from persona_forge.config import (
    ANTHROPIC_API_KEY_ENV,
    DEFAULT_MODEL,
)
from persona_forge.llm.provider import LLMProvider


class AnthropicProvider:
    """Anthropic Claude API provider.

    Uses the Messages API via httpx. No streaming.
    Reuses a single httpx client across calls for connection pooling.
    """

    API_URL = "https://api.anthropic.com/v1/messages"
    API_VERSION = "2023-06-01"

    def __init__(self, model: str | None = None, api_key: str | None = None):
        self._model = model or DEFAULT_MODEL
        self._api_key = api_key or os.environ.get(ANTHROPIC_API_KEY_ENV, "")
        if not self._api_key:
            raise ValueError(
                f"Anthropic API key not found. Set {ANTHROPIC_API_KEY_ENV} "
                f"environment variable or pass api_key parameter."
            )
        self._client = httpx.Client(timeout=120.0)

    def generate(self, system: str, user: str, temperature: float = 0.7) -> str:
        """Send a prompt to Claude and return the text response."""
        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": self.API_VERSION,
            "content-type": "application/json",
        }
        payload = {
            "model": self._model,
            "max_tokens": 4096,
            "temperature": temperature,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }

        response = self._client.post(self.API_URL, headers=headers, json=payload)
        response.raise_for_status()

        data = response.json()
        # Extract text from the first content block
        return data["content"][0]["text"]

    @property
    def name(self) -> str:
        return "anthropic"

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()


def create_provider(model: str | None = None) -> AnthropicProvider:
    """Factory function to create an Anthropic provider."""
    return AnthropicProvider(model=model)
