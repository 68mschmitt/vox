"""LLM provider abstraction.

Thin protocol over LLM API calls. Every provider implements the same
interface: prompt in, text out. No streaming, no tool use.

Provider selection is via CLI flag (--provider anthropic|openai|ollama).

Schema reference: design/ARCHITECTURE.md
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    """Abstract interface for LLM API providers.

    All providers must implement:
    - generate(): send a system+user prompt, get text back
    - name: provider identifier string
    """

    def generate(self, system: str, user: str, temperature: float = 0.7) -> str:
        """Send a prompt and return the generated text response.

        Args:
            system: The system prompt (role/context).
            user: The user prompt (task/question).
            temperature: Sampling temperature (0.0-1.0).

        Returns:
            The generated text response.
        """
        ...

    @property
    def name(self) -> str:
        """Return the provider name (e.g. 'anthropic', 'openai', 'ollama')."""
        ...
