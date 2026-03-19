"""
LLM service — xAI Grok as primary, Ollama as local fallback.

Provider selection:
  - XAI_API_KEY set   → xAI Grok (remote)
  - XAI_API_KEY unset → Ollama (local, must be running)
  - xAI returns 429   → automatically falls back to Ollama
"""
import logging
from openai import AsyncOpenAI, RateLimitError, APIStatusError
from config import XAI_API_KEY, GROK_MODEL, OLLAMA_BASE_URL, OLLAMA_MODEL

logger = logging.getLogger(__name__)

_xai_client: AsyncOpenAI | None = None
_ollama_client: AsyncOpenAI | None = None


def _get_xai_client() -> AsyncOpenAI:
    global _xai_client
    if _xai_client is None:
        _xai_client = AsyncOpenAI(
            api_key=XAI_API_KEY,
            base_url="https://api.x.ai/v1",
            max_retries=0,
        )
    return _xai_client


def _get_ollama_client() -> AsyncOpenAI:
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = AsyncOpenAI(
            api_key="ollama",  # pragma: allowlist secret
            base_url=f"{OLLAMA_BASE_URL}/v1",
        )
    return _ollama_client


async def _call_with_fallback(messages: list[dict], max_tokens: int) -> str:
    """Call xAI Grok, falling back to Ollama on 429 or if no API key is set."""
    if XAI_API_KEY:
        try:
            response = await _get_xai_client().chat.completions.create(
                model=GROK_MODEL,
                max_tokens=max_tokens,
                messages=messages,
            )
            return response.choices[0].message.content or ""
        except (RateLimitError, APIStatusError) as e:
            if isinstance(e, APIStatusError) and e.status_code != 429:
                raise
            logger.warning("[LLM] xAI rate limit / credits exhausted — falling back to Ollama")

    logger.info(f"[LLM] Using Ollama ({OLLAMA_MODEL}) at {OLLAMA_BASE_URL}")
    response = await _get_ollama_client().chat.completions.create(
        model=OLLAMA_MODEL,
        max_tokens=max_tokens,
        messages=messages,
    )
    return response.choices[0].message.content or ""


async def complete(prompt: str, max_tokens: int = 2000) -> str:
    """Single-turn completion. Falls back to Ollama on xAI 429."""
    return await _call_with_fallback([{"role": "user", "content": prompt}], max_tokens)


async def chat(messages: list[dict], max_tokens: int = 1000) -> str:
    """Multi-turn chat. Falls back to Ollama on xAI 429."""
    return await _call_with_fallback(messages, max_tokens)
