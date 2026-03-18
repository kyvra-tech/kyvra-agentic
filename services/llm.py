"""
LLM service — xAI Grok as primary, Ollama as local fallback.

Provider selection:
  - XAI_API_KEY set   → xAI Grok (remote)
  - XAI_API_KEY unset → Ollama (local, must be running)
"""
import logging
from openai import AsyncOpenAI
from config import XAI_API_KEY, GROK_MODEL, OLLAMA_BASE_URL, OLLAMA_MODEL

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def _use_ollama() -> bool:
    return not XAI_API_KEY


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        if _use_ollama():
            logger.info(f"[LLM] XAI_API_KEY not set — using Ollama at {OLLAMA_BASE_URL} (model: {OLLAMA_MODEL})")
            _client = AsyncOpenAI(
                api_key="ollama",  # pragma: allowlist secret
                base_url=f"{OLLAMA_BASE_URL}/v1",
            )
        else:
            _client = AsyncOpenAI(
                api_key=XAI_API_KEY,
                base_url="https://api.x.ai/v1",
            )
    return _client


def _model() -> str:
    return OLLAMA_MODEL if _use_ollama() else GROK_MODEL


async def complete(prompt: str, max_tokens: int = 2000) -> str:
    """Single-turn completion. Returns the response text."""
    client = get_client()
    response = await client.chat.completions.create(
        model=_model(),
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content or ""


async def chat(messages: list[dict], max_tokens: int = 1000) -> str:
    """Multi-turn chat. messages = list of {role, content} dicts."""
    client = get_client()
    response = await client.chat.completions.create(
        model=_model(),
        max_tokens=max_tokens,
        messages=messages,
    )
    return response.choices[0].message.content or ""
