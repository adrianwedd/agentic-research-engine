from __future__ import annotations

"""Pluggable LLM client supporting local and cloud backends."""

import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Sequence

import openai
import requests


class LLMClient(ABC):
    """Abstract base LLM client."""

    def __init__(self, model: str) -> None:
        self.model = model

    @abstractmethod
    def invoke(self, messages: Sequence[Dict[str, str]], **kwargs: Any) -> str:
        """Generate a completion from ``messages``."""
        raise NotImplementedError


class OllamaClient(LLMClient):
    """Client for a local Ollama server."""

    def __init__(self, model: str, base_url: str | None = None) -> None:
        super().__init__(model)
        self.base_url = base_url or os.getenv(
            "OLLAMA_BASE_URL", "http://localhost:11434"
        )

    def invoke(self, messages: Sequence[Dict[str, str]], **kwargs: Any) -> str:
        url = f"{self.base_url}/api/chat"
        resp = requests.post(
            url,
            json={"model": self.model, "messages": list(messages)},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        # Ollama returns {{"message": {{"content": ...}}}}
        return data.get("message", {}).get("content", data.get("content", ""))


class OpenAICompatibleClient(LLMClient):
    """Client for OpenAI-compatible endpoints using the openai library."""

    def __init__(self, model: str, api_key: str, base_url: str) -> None:
        super().__init__(model)
        self.client = openai.OpenAI(api_key=api_key, base_url=base_url)

    def invoke(self, messages: Sequence[Dict[str, str]], **kwargs: Any) -> str:
        resp = self.client.chat.completions.create(
            model=self.model, messages=list(messages), **kwargs
        )
        return resp.choices[0].message.content


def load_llm_client() -> LLMClient:
    """Instantiate an LLM client based on environment configuration."""

    provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    model = os.getenv("LLM_MODEL_NAME", "llama3")

    if provider == "ollama":
        base = os.getenv("LLM_API_BASE_URL")
        return OllamaClient(model, base)

    if provider == "openai_compatible":
        base = os.getenv("LLM_API_BASE_URL", "https://api.openai.com/v1")
        api_key = os.getenv("LLM_API_KEY")
        if not api_key:
            raise ValueError("LLM_API_KEY is required for OpenAI-compatible client")
        return OpenAICompatibleClient(model, api_key, base)

    raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")


__all__ = [
    "LLMClient",
    "OllamaClient",
    "OpenAICompatibleClient",
    "load_llm_client",
]
