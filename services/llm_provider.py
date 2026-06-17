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
CONTENT_LLM_PROVIDER  = deepseek   (default: deepseek)
CAPTION_LLM_PROVIDER  = deepseek   (default: deepseek)

Providers
---------
DeepSeekProvider — DeepSeek API; cheap, fast; uses DEEPSEEK_API_KEY
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


_PROVIDERS = {
    "deepseek": DeepSeekProvider,
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
