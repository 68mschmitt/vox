"""LLM provider package.

Provider resolution order (when no explicit --provider flag):
  1. bedrock  -- if AWS_BEARER_TOKEN_BEDROCK is set
  2. ollama   -- if a local Ollama instance is reachable
  3. anthropic -- if ANTHROPIC_API_KEY is set

An explicit --provider flag or PERSONA_FORGE_PROVIDER env var
skips the fallback chain entirely.
"""

from __future__ import annotations

import os

from persona_forge.llm.provider import LLMProvider

__all__ = ["LLMProvider", "create_provider"]

# Fallback order when auto-detecting
_FALLBACK_CHAIN = ["bedrock", "ollama", "anthropic"]


def _is_provider_available(name: str) -> bool:
    """Check whether a provider's credentials / service are available.

    Quick checks only -- no heavy network calls except a fast local
    ping for Ollama.
    """
    if name == "bedrock":
        from persona_forge.config import AWS_BEARER_TOKEN_BEDROCK_ENV

        return bool(os.environ.get(AWS_BEARER_TOKEN_BEDROCK_ENV))

    if name == "ollama":
        from persona_forge.llm.ollama import is_available

        return is_available()

    if name == "anthropic":
        from persona_forge.config import ANTHROPIC_API_KEY_ENV

        return bool(os.environ.get(ANTHROPIC_API_KEY_ENV))

    return False


def _make_provider(name: str, model: str | None) -> LLMProvider:
    """Instantiate a provider by name. Raises ValueError on failure."""
    if name == "anthropic":
        from persona_forge.llm.anthropic import AnthropicProvider

        return AnthropicProvider(model=model)

    if name == "bedrock":
        from persona_forge.llm.bedrock import BedrockProvider

        return BedrockProvider(model=model)

    if name == "ollama":
        from persona_forge.llm.ollama import OllamaProvider

        return OllamaProvider(model=model)

    raise ValueError(
        f"Unknown provider: {name!r}. Supported providers: bedrock, ollama, anthropic."
    )


def create_provider(
    provider_name: str | None = None,
    model: str | None = None,
) -> LLMProvider:
    """Create an LLM provider, with automatic fallback when unspecified.

    If *provider_name* is given (via --provider flag), that provider is
    used directly with no fallback -- a missing credential is a hard error.

    If *provider_name* is None and PERSONA_FORGE_PROVIDER is set, that
    env var is treated the same as an explicit flag.

    Otherwise the factory walks the fallback chain:
        bedrock -> ollama -> anthropic
    and returns the first provider whose credentials are present.

    Args:
        provider_name: Explicit provider name, or None for auto-detect.
        model: Optional model override.

    Returns:
        An LLMProvider instance.

    Raises:
        ValueError: If no provider could be initialised.
    """
    # Explicit provider requested (flag or env var)
    explicit = provider_name or os.environ.get("PERSONA_FORGE_PROVIDER")
    if explicit:
        return _make_provider(explicit, model)

    # Auto-detect: walk the fallback chain
    for candidate in _FALLBACK_CHAIN:
        if _is_provider_available(candidate):
            return _make_provider(candidate, model)

    raise ValueError(
        "No LLM provider available. Set up one of the following:\n"
        "  - AWS_BEARER_TOKEN_BEDROCK  (Amazon Bedrock)\n"
        "  - Ollama running locally    (http://localhost:11434)\n"
        "  - ANTHROPIC_API_KEY         (Anthropic API)\n"
        "Or pass --provider explicitly."
    )
