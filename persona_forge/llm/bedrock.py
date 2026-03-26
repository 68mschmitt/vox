"""Amazon Bedrock LLM provider.

Uses the Bedrock Runtime Converse API with bearer token authentication.
Supports any model available in your Bedrock region.
"""

from __future__ import annotations

import os

import httpx

from persona_forge.config import (
    AWS_BEARER_TOKEN_BEDROCK_ENV,
    AWS_BEDROCK_REGION_ENV,
    BEDROCK_DEFAULT_MODEL,
    BEDROCK_DEFAULT_REGION,
)
from persona_forge.llm.provider import LLMProvider


class BedrockProvider:
    """Amazon Bedrock provider using the Converse API.

    Authenticates with a bearer token (AWS IAM Identity Center).
    Uses the Converse API for a model-agnostic interface.
    Reuses a single httpx client across calls.
    """

    def __init__(
        self,
        model: str | None = None,
        bearer_token: str | None = None,
        region: str | None = None,
    ):
        self._model = model or BEDROCK_DEFAULT_MODEL
        self._region = region or os.environ.get(
            AWS_BEDROCK_REGION_ENV, BEDROCK_DEFAULT_REGION
        )
        self._bearer_token = bearer_token or os.environ.get(
            AWS_BEARER_TOKEN_BEDROCK_ENV, ""
        )
        if not self._bearer_token:
            raise ValueError(
                f"AWS Bedrock bearer token not found. Set {AWS_BEARER_TOKEN_BEDROCK_ENV} "
                f"environment variable or pass bearer_token parameter."
            )
        self._base_url = f"https://bedrock-runtime.{self._region}.amazonaws.com"
        self._client = httpx.Client(timeout=120.0)

    def generate(self, system: str, user: str, temperature: float = 0.7) -> str:
        """Send a prompt via the Bedrock Converse API and return text."""
        url = f"{self._base_url}/model/{self._model}/converse"

        headers = {
            "Authorization": f"Bearer {self._bearer_token}",
            "Content-Type": "application/json",
        }

        payload: dict = {
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": user}],
                }
            ],
            "inferenceConfig": {
                "maxTokens": 4096,
                "temperature": temperature,
            },
        }

        # Converse API takes system as an array of text objects
        if system:
            payload["system"] = [{"text": system}]

        response = self._client.post(url, headers=headers, json=payload)
        response.raise_for_status()

        data = response.json()

        # Converse API response: output.message.content[0].text
        output = data.get("output", {})
        message = output.get("message", {})
        content_blocks = message.get("content", [])

        if not content_blocks:
            raise RuntimeError(
                f"Bedrock Converse API returned empty content. Response: {data}"
            )

        # Concatenate all text blocks (usually just one)
        text_parts = []
        for block in content_blocks:
            if isinstance(block, dict) and "text" in block:
                text_parts.append(block["text"])

        if not text_parts:
            raise RuntimeError(
                f"Bedrock Converse API returned no text content blocks. "
                f"Response: {data}"
            )

        return "\n".join(text_parts)

    @property
    def name(self) -> str:
        return "bedrock"

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()


def create_provider(
    model: str | None = None,
    region: str | None = None,
) -> BedrockProvider:
    """Factory function to create a Bedrock provider."""
    return BedrockProvider(model=model, region=region)
