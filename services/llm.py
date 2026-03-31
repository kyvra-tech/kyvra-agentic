"""
LLM service — Ollama (Gemma 3) as primary model.

Requires Ollama running locally: https://ollama.com
Run: ollama pull gemma3
"""
import logging
from openai import AsyncOpenAI
from config import OLLAMA_BASE_URL, OLLAMA_MODEL

logger = logging.getLogger(__name__)

_ollama_client: AsyncOpenAI | None = None


def _get_ollama_client() -> AsyncOpenAI:
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = AsyncOpenAI(
            api_key="ollama",  # pragma: allowlist secret
            base_url=f"{OLLAMA_BASE_URL}/v1",
        )
    return _ollama_client


async def _call_ollama(messages: list[dict], max_tokens: int) -> str:
    logger.info(f"[LLM] Using Ollama ({OLLAMA_MODEL}) at {OLLAMA_BASE_URL}")
    response = await _get_ollama_client().chat.completions.create(
        model=OLLAMA_MODEL,
        max_tokens=max_tokens,
        messages=messages,
    )
    return response.choices[0].message.content or ""


async def complete(prompt: str, max_tokens: int = 2000) -> str:
    """Single-turn completion via Ollama."""
    return await _call_ollama([{"role": "user", "content": prompt}], max_tokens)


async def chat(messages: list[dict], max_tokens: int = 1000) -> str:
    """Multi-turn chat via Ollama."""
    return await _call_ollama(messages, max_tokens)
