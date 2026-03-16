"""
LLM service — single AsyncOpenAI client shared across all agents.

Using AsyncOpenAI (not OpenAI) so API calls don't block the event loop.
"""
import logging
from openai import AsyncOpenAI
from config import XAI_API_KEY, GROK_MODEL

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        if not XAI_API_KEY:
            raise RuntimeError("XAI_API_KEY is not set")
        _client = AsyncOpenAI(
            api_key=XAI_API_KEY,
            base_url="https://api.x.ai/v1",
        )
    return _client


async def complete(prompt: str, max_tokens: int = 2000) -> str:
    """Single-turn completion. Returns the response text."""
    client = get_client()
    response = await client.chat.completions.create(
        model=GROK_MODEL,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


async def chat(messages: list[dict], max_tokens: int = 1000) -> str:
    """Multi-turn chat. messages = list of {role, content} dicts."""
    client = get_client()
    response = await client.chat.completions.create(
        model=GROK_MODEL,
        max_tokens=max_tokens,
        messages=messages,
    )
    return response.choices[0].message.content
