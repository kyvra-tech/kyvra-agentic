"""
LLM provider abstraction for the Kyvra pipeline.

Teaching notes — why this exists
---------------------------------
Previously all LLM calls were hardcoded to one provider (DeepSeek / Ollama).
This module introduces a pluggable provider layer so you can swap models
by changing a single env var — no code change needed.

The pattern here is the classic Strategy pattern:
  - LLMProvider (ABC) defines the interface
  - Concrete classes implement it for each backend
  - get_provider() is the factory that reads config and returns the right one

Usage
-----
    from services.llm_provider import get_content_provider, get_caption_provider

    text = await get_content_provider().complete(prompt, max_tokens=2000)

Environment variables
---------------------
CONTENT_LLM_PROVIDER  = ollama | deepseek | claude   (default: deepseek)
CAPTION_LLM_PROVIDER  = deepseek | claude            (default: deepseek)

Providers
---------
OllamaProvider  — local Ollama (Gemma 3); free, no API key needed
DeepSeekProvider — DeepSeek API; cheap, fast; uses DEEPSEEK_API_KEY
ClaudeProvider  — Anthropic Claude; most capable; uses ANTHROPIC_API_KEY
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------

class LLMProvider(ABC):
    """Unified interface for all LLM backends used in the pipeline."""

    @abstractmethod
    async def complete(self, prompt: str, max_tokens: int = 2000) -> str:
        """Single-turn completion.  Returns the model's reply as a string."""
        ...

    @abstractmethod
    async def chat(self, messages: list[dict], max_tokens: int = 1000) -> str:
        """Multi-turn chat.  messages = [{role, content}, ...]."""
        ...


# ---------------------------------------------------------------------------
# DeepSeek (OpenAI-compatible API)
# ---------------------------------------------------------------------------

class DeepSeekProvider(LLMProvider):
    """Uses the DeepSeek API via the OpenAI SDK (same wire protocol)."""

    def __init__(self) -> None:
        from openai import AsyncOpenAI
        from config import DEEPSEEK_API_KEY, DEEPSEEK_MODEL
        self._model = DEEPSEEK_MODEL
        self._client = AsyncOpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com/v1",
        )

    async def _call(self, messages: list[dict], max_tokens: int) -> str:
        logger.info("[LLM] DeepSeek → %s (max_tokens=%d)", self._model, max_tokens)
        response = await self._client.chat.completions.create(
            model=self._model,
            max_tokens=max_tokens,
            messages=messages,
        )
        return response.choices[0].message.content or ""

    async def complete(self, prompt: str, max_tokens: int = 2000) -> str:
        return await self._call([{"role": "user", "content": prompt}], max_tokens)

    async def chat(self, messages: list[dict], max_tokens: int = 1000) -> str:
        return await self._call(messages, max_tokens)


# ---------------------------------------------------------------------------
# Ollama (local)
# ---------------------------------------------------------------------------

class OllamaProvider(LLMProvider):
    """Calls a locally-running Ollama server (e.g. Gemma 3).

    Teaching note: Ollama exposes an OpenAI-compatible endpoint at
    /v1/chat/completions, so we reuse the same AsyncOpenAI client trick.
    """

    def __init__(self) -> None:
        from openai import AsyncOpenAI
        from config import OLLAMA_BASE_URL, OLLAMA_MODEL
        self._model = OLLAMA_MODEL
        self._client = AsyncOpenAI(
            api_key="ollama",                      # Ollama ignores the key
            base_url=f"{OLLAMA_BASE_URL}/v1",
        )

    async def _call(self, messages: list[dict], max_tokens: int) -> str:
        logger.info("[LLM] Ollama → %s (max_tokens=%d)", self._model, max_tokens)
        response = await self._client.chat.completions.create(
            model=self._model,
            max_tokens=max_tokens,
            messages=messages,
        )
        return response.choices[0].message.content or ""

    async def complete(self, prompt: str, max_tokens: int = 2000) -> str:
        return await self._call([{"role": "user", "content": prompt}], max_tokens)

    async def chat(self, messages: list[dict], max_tokens: int = 1000) -> str:
        return await self._call(messages, max_tokens)


# ---------------------------------------------------------------------------
# Claude (Anthropic SDK)
# ---------------------------------------------------------------------------

class ClaudeProvider(LLMProvider):
    """Calls Claude via the Anthropic SDK.

    Teaching note: Anthropic's SDK is NOT OpenAI-compatible — it has its
    own message format.  This class bridges that difference.
    Set ANTHROPIC_API_KEY in your .env to use this provider.
    """

    def __init__(self) -> None:
        import anthropic
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self._model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
        self._client = anthropic.AsyncAnthropic(api_key=api_key)

    async def complete(self, prompt: str, max_tokens: int = 2000) -> str:
        logger.info("[LLM] Claude → %s (max_tokens=%d)", self._model, max_tokens)
        message = await self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text if message.content else ""

    async def chat(self, messages: list[dict], max_tokens: int = 1000) -> str:
        """Multi-turn chat.  Extracts system message if present (Anthropic requires it separately)."""
        logger.info("[LLM] Claude chat → %s (max_tokens=%d)", self._model, max_tokens)
        system = ""
        user_messages = []
        for m in messages:
            if m["role"] == "system":
                system = m["content"]
            else:
                user_messages.append(m)

        kwargs = {"model": self._model, "max_tokens": max_tokens, "messages": user_messages}
        if system:
            kwargs["system"] = system

        message = await self._client.messages.create(**kwargs)
        return message.content[0].text if message.content else ""


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

_PROVIDERS = {
    "deepseek": DeepSeekProvider,
    "ollama":   OllamaProvider,
    "claude":   ClaudeProvider,
}


def get_provider(name: str) -> LLMProvider:
    """Return an instantiated provider by name.

    Raises ValueError for unknown names so misconfiguration is caught early.
    """
    cls = _PROVIDERS.get(name.lower())
    if cls is None:
        raise ValueError(f"Unknown LLM provider '{name}'. Available: {sorted(_PROVIDERS)}")
    return cls()


def get_content_provider() -> LLMProvider:
    """Provider for report/thread/brief/newsletter/script generation.
    Controlled by CONTENT_LLM_PROVIDER env var (default: deepseek).
    """
    name = os.getenv("CONTENT_LLM_PROVIDER", "deepseek")
    return get_provider(name)


def get_caption_provider() -> LLMProvider:
    """Provider for video/image captions.
    Controlled by CAPTION_LLM_PROVIDER env var (default: deepseek).
    """
    name = os.getenv("CAPTION_LLM_PROVIDER", "deepseek")
    return get_provider(name)
