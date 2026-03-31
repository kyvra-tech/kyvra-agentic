"""
CaptionAgent — uses DeepSeek API to write viral English captions.
"""
import logging
from openai import AsyncOpenAI
from config import DEEPSEEK_API_KEY, DEEPSEEK_MODEL
from modules.video.prompts import build_multi_caption_prompt

logger = logging.getLogger(__name__)

_deepseek_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _deepseek_client
    if _deepseek_client is None:
        _deepseek_client = AsyncOpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com/v1",
            max_retries=2,
        )
    return _deepseek_client


async def generate_all_captions(title: str, description: str, transcript: str) -> str:
    """Generate captions for TikTok, Reels, and YouTube Shorts via DeepSeek."""
    prompt = build_multi_caption_prompt(title, description, transcript)
    try:
        response = await _get_client().chat.completions.create(
            model=DEEPSEEK_MODEL,
            max_tokens=2500,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        logger.error(f"[CaptionAgent] DeepSeek API error: {e}")
        raise
