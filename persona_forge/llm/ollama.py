"""Ollama (local) LLM provider.

Uses the Ollama REST API for local model inference.
No API key needed -- just a running Ollama instance.
"""

from __future__ import annotations

import os

import httpx

from persona_forge.config import (
    OLLAMA_DEFAULT_HOST,
    OLLAMA_HOST_ENV,
)
from persona_forge.llm.provider import LLMProvider

# Default model for Ollama -- a capable local model
OLLAMA_DEFAULT_MODEL = "llama3.1"


class OllamaProvider:
    """Ollama local LLM provider.

    Uses the /api/chat endpoint. No streaming.
    Reuses a single httpx client across calls.
    """

    def __init__(
        self,
        model: str | None = None,
        host: str | None = None,
    ):
        self._model = model or OLLAMA_DEFAULT_MODEL
        self._host = (
            host or os.environ.get(OLLAMA_HOST_ENV) or OLLAMA_DEFAULT_HOST
        ).rstrip("/")
        self._client = httpx.Client(timeout=300.0)  # local models can be slow

    def generate(self, system: str, user: str, temperature: float = 0.7) -> str:
        """Send a prompt to Ollama and return the text response."""
        url = f"{self._host}/api/chat"

        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }

        response = self._client.post(url, json=payload)
        response.raise_for_status()

        data = response.json()
        message = data.get("message", {})
        return message.get("content", "")

    @property
    def name(self) -> str:
        return "ollama"

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()


def is_available(host: str | None = None) -> bool:
    """Check if Ollama is reachable at the given host.

    Makes a quick GET to the Ollama root endpoint.
    Returns False on any connection error or timeout.
    """
    target = (host or os.environ.get(OLLAMA_HOST_ENV) or OLLAMA_DEFAULT_HOST).rstrip(
        "/"
    )
    try:
        resp = httpx.get(target, timeout=2.0)
        return resp.status_code == 200
    except (httpx.ConnectError, httpx.TimeoutException, OSError):
        return False
