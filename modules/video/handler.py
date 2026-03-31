"""
Media caption handler — fetch metadata only (no download), generate caption via Ollama.
"""
import logging

from modules.video.downloader import fetch_video_info, is_supported_url
from modules.video.caption_agent import generate_all_captions

logger = logging.getLogger(__name__)


async def process_media_url(url: str) -> dict:
    """
    Lightweight pipeline: fetch metadata → generate captions via Ollama.
    No download, no local files.

    Returns dict with keys:
      - caption: str
      - title: str
      - url: str
      - error: str | None
    """
    if not is_supported_url(url):
        return {"error": "Unsupported URL. Supported: YouTube, TikTok, Instagram, Twitter/X, Facebook, Reddit"}

    # Fetch title + description only (no download)
    info = await fetch_video_info(url)
    if info.error:
        return {"error": f"Could not read media info: {info.error}"}

    logger.info(f"[MediaHandler] Generating captions for: {info.title}")
    try:
        caption = await generate_all_captions(
            title=info.title,
            description=info.description,
            transcript="",
        )
    except Exception as e:
        logger.error(f"[MediaHandler] Caption generation failed: {e}")
        caption = f"⚠️ Caption generation failed: {e}"

    return {
        "caption": caption,
        "title": info.title,
        "url": url,
        "error": None,
    }
