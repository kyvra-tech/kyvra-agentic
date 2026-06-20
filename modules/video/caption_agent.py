"""
CaptionAgent — uses DeepSeek API to write a viral Twitter/X caption.
"""
import logging
from openai import AsyncOpenAI
from config import DEEPSEEK_API_KEY, DEEPSEEK_MODEL
from modules.video.prompts import build_twitter_caption_prompt

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


async def generate_twitter_caption(
    title: str,
    description: str,
    transcript: str,
    url: str,
) -> str:
    """Generate a single viral Twitter/X caption ready to copy-paste."""
    import services.memory as memory

    prompt = build_twitter_caption_prompt(title, description, transcript, url)

    # Inject global voice profile
    voice = memory.get_voice_profile(0)
    if voice:
        prompt += f"\n\nVoice profile (write in this style): {voice}"

    # Inject language preference
    prompt += memory.get_language_instruction()

    try:
        response = await _get_client().chat.completions.create(
            model=DEEPSEEK_MODEL,
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        logger.error(f"[CaptionAgent] DeepSeek API error: {e}")
        raise
