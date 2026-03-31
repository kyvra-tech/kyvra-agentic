"""
CaptionAgent — uses Ollama (Gemma 3) to write viral English captions.
"""
import logging
import services.llm as llm
from modules.video.prompts import build_multi_caption_prompt

logger = logging.getLogger(__name__)


async def generate_all_captions(title: str, description: str, transcript: str) -> str:
    """Generate captions for TikTok, Reels, and YouTube Shorts via Ollama."""
    prompt = build_multi_caption_prompt(title, description, transcript)
    return await llm.complete(prompt, max_tokens=2500)
