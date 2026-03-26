"""LLM provider package."""

from persona_forge.llm.provider import LLMProvider

__all__ = ["LLMProvider", "create_provider"]


def create_provider(
    provider_name: str | None = None,
    model: str | None = None,
) -> LLMProvider:
    """Factory function to create an LLM provider by name.

    Args:
        provider_name: Provider name (anthropic, openai, ollama).
            Defaults to config.DEFAULT_PROVIDER.
        model: Optional model override.

    Returns:
        An LLMProvider instance.
    """
    from persona_forge.config import DEFAULT_PROVIDER

    name = provider_name or DEFAULT_PROVIDER

    if name == "anthropic":
        from persona_forge.llm.anthropic import AnthropicProvider

        return AnthropicProvider(model=model)
    else:
        raise ValueError(
            f"Unknown provider: {name!r}. "
            f"POC supports: anthropic. (openai, ollama coming in later phases)"
        )
