"""LLM response parsing utilities.

LLMs often wrap JSON in markdown code fences or add preamble text.
This module provides robust extraction of JSON from LLM responses.
"""

from __future__ import annotations

import json
import re
import time
from typing import Any

from persona_forge.llm.provider import LLMProvider


def extract_json(text: str) -> dict[str, Any]:
    """Extract a JSON object from LLM response text.

    Handles common LLM response patterns:
    - Raw JSON
    - JSON wrapped in ```json ... ``` fences
    - JSON wrapped in ``` ... ``` fences
    - JSON preceded/followed by prose text

    Args:
        text: Raw LLM response text.

    Returns:
        Parsed JSON as a dict.

    Raises:
        ValueError: If no valid JSON object can be extracted.
    """
    # Try 1: Direct parse (cleanest case)
    stripped = text.strip()
    if stripped.startswith("{"):
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            pass

    # Try 2: Extract from markdown code fence
    fence_pattern = re.compile(r"```(?:json)?\s*\n?(.*?)\n?\s*```", re.DOTALL)
    match = fence_pattern.search(text)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Try 3: Find a valid { ... } block, scanning forward on failure
    brace_start = text.find("{")
    while brace_start != -1:
        depth = 0
        for i in range(brace_start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[brace_start : i + 1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        pass
                    break
        brace_start = text.find("{", brace_start + 1)

    raise ValueError(
        f"Could not extract valid JSON from LLM response. "
        f"Response starts with: {text[:200]!r}"
    )


def generate_with_retry(
    provider: LLMProvider,
    system: str,
    user: str,
    temperature: float = 0.7,
    retries: int = 2,
) -> str:
    """Call provider.generate() with simple retry and exponential backoff.

    Retries on any exception (transient API errors, rate limits, etc.).

    Args:
        provider: LLM provider.
        system: System prompt.
        user: User prompt.
        temperature: Sampling temperature.
        retries: Number of retry attempts after initial failure.

    Returns:
        The generated text response.
    """
    for attempt in range(retries + 1):
        try:
            return provider.generate(system, user, temperature)
        except Exception:
            if attempt == retries:
                raise
            time.sleep(2**attempt)
    # Unreachable, but satisfies type checker
    raise RuntimeError("Retry loop exited unexpectedly")
