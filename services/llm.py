"""
LLM service — DeepSeek API as primary model.

Get your key at: platform.deepseek.com
Set DEEPSEEK_API_KEY and DEEPSEEK_MODEL in .env
"""
import logging
from openai import AsyncOpenAI
from config import DEEPSEEK_API_KEY, DEEPSEEK_MODEL

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com/v1",
        )
    return _client


async def _call(messages: list[dict], max_tokens: int) -> str:
    logger.info(f"[LLM] Using DeepSeek ({DEEPSEEK_MODEL})")
    response = await _get_client().chat.completions.create(
        model=DEEPSEEK_MODEL,
        max_tokens=max_tokens,
        messages=messages,
    )
    return response.choices[0].message.content or ""


async def complete(prompt: str, max_tokens: int = 2000) -> str:
    """Single-turn completion via DeepSeek."""
    return await _call([{"role": "user", "content": prompt}], max_tokens)


async def chat(messages: list[dict], max_tokens: int = 1000) -> str:
    """Multi-turn chat via DeepSeek."""
    return await _call(messages, max_tokens)
