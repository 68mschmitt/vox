"""Tests for LLM JSON response parsing and retry logic."""

from __future__ import annotations

import pytest

from persona_forge.llm.parse import extract_json, generate_with_retry


class TestExtractJson:
    def test_raw_json(self):
        """Raw JSON string parses directly."""
        text = '{"key": "value", "num": 42}'
        result = extract_json(text)
        assert result == {"key": "value", "num": 42}

    def test_json_with_whitespace(self):
        """JSON with leading/trailing whitespace."""
        text = '  \n  {"key": "value"}  \n  '
        result = extract_json(text)
        assert result == {"key": "value"}

    def test_json_in_markdown_fence(self):
        """JSON wrapped in ```json ... ``` fences."""
        text = """Here's the result:

```json
{"key": "value", "list": [1, 2, 3]}
```

That's the output."""
        result = extract_json(text)
        assert result == {"key": "value", "list": [1, 2, 3]}

    def test_json_in_plain_fence(self):
        """JSON wrapped in ``` ... ``` fences (no language tag)."""
        text = """```
{"key": "value"}
```"""
        result = extract_json(text)
        assert result == {"key": "value"}

    def test_json_with_prose_before(self):
        """JSON preceded by prose text."""
        text = 'Here are the scores:\n\n{"content": {"score": 7, "gap": "minor"}}'
        result = extract_json(text)
        assert result["content"]["score"] == 7

    def test_nested_json(self):
        """Nested JSON objects parse correctly."""
        text = '{"outer": {"inner": {"deep": true}}, "list": [{"a": 1}]}'
        result = extract_json(text)
        assert result["outer"]["inner"]["deep"] is True

    def test_invalid_json_raises(self):
        """Non-JSON text raises ValueError."""
        with pytest.raises(ValueError, match="Could not extract valid JSON"):
            extract_json("This is just plain text with no JSON.")

    def test_empty_string_raises(self):
        """Empty string raises ValueError."""
        with pytest.raises(ValueError):
            extract_json("")

    def test_broken_fence_with_valid_json_after(self):
        """When code fence has invalid JSON but valid JSON exists later."""
        text = '```json\n{not valid\n```\nBut: {"real": "data"}'
        result = extract_json(text)
        assert result == {"real": "data"}

    def test_multiple_json_objects_returns_first_valid(self):
        """When multiple JSON objects exist, returns the first valid one."""
        text = '{bad json here} {"good": true}'
        result = extract_json(text)
        assert result == {"good": True}

    def test_json_with_trailing_comma_in_prose(self):
        """JSON embedded in prose with commas around it."""
        text = 'The analysis shows: {"score": 8.5} and that is the result.'
        result = extract_json(text)
        assert result == {"score": 8.5}


class TestGenerateWithRetry:
    def test_succeeds_first_try(self):
        """Returns result on first successful call."""

        class GoodProvider:
            def generate(self, system, user, temperature=0.7):
                return "response"

            @property
            def name(self):
                return "good"

        result = generate_with_retry(GoodProvider(), "sys", "usr")
        assert result == "response"

    def test_retries_on_failure(self):
        """Retries after transient failure and succeeds."""

        class FlakeyProvider:
            def __init__(self):
                self.calls = 0

            def generate(self, system, user, temperature=0.7):
                self.calls += 1
                if self.calls == 1:
                    raise ConnectionError("transient failure")
                return "recovered"

            @property
            def name(self):
                return "flakey"

        provider = FlakeyProvider()
        result = generate_with_retry(provider, "sys", "usr", retries=2)
        assert result == "recovered"
        assert provider.calls == 2

    def test_raises_after_all_retries_exhausted(self):
        """Raises the exception after all retries are exhausted."""

        class BadProvider:
            def generate(self, system, user, temperature=0.7):
                raise RuntimeError("permanent failure")

            @property
            def name(self):
                return "bad"

        with pytest.raises(RuntimeError, match="permanent failure"):
            generate_with_retry(BadProvider(), "sys", "usr", retries=1)
