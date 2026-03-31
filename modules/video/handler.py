"""
Media caption handler — download video/image, generate Twitter caption via DeepSeek.
"""
import logging
from pathlib import Path

from modules.video.downloader import download_video, fetch_video_info, cleanup_video_files, is_supported_url
from modules.video.caption_agent import generate_twitter_caption
from modules.video.config import MAX_VIDEO_SIZE_BYTES

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mkv", ".mov", ".avi"}


def _classify_media(path: str | None) -> str:
    if not path:
        return "none"
    suffix = Path(path).suffix.lower()
    if suffix in VIDEO_EXTENSIONS:
        return "video"
    if suffix in IMAGE_EXTENSIONS:
        return "image"
    return "none"


async def process_media_url(url: str) -> dict:
    """
    Download media → generate Twitter caption.

    Returns dict with keys:
      - caption: str          (ready-to-copy tweet)
      - media_path: str | None
      - media_type: 'video'|'image'|'none'
      - thumbnail_path: str | None
      - title: str
      - error: str | None
    """
    if not is_supported_url(url):
        return {"error": "Unsupported URL. Supported: YouTube, TikTok, Instagram, Twitter/X, Facebook, Reddit"}

    # Step 1: fetch metadata (fast, no download)
    info = await fetch_video_info(url)
    if info.error:
        # Metadata fetch failed — still try to generate caption from URL alone
        logger.warning(f"[MediaHandler] Could not fetch metadata: {info.error}")

    # Step 2: try to download media (best-effort, skip on failure)
    media_path = None
    media_type = "none"
    thumbnail_path = None

    if not info.error:
        logger.info(f"[MediaHandler] Downloading: {info.title} ({url})")
        downloaded = await download_video(url)

        if downloaded.error:
            logger.warning(f"[MediaHandler] Download failed (caption-only mode): {downloaded.error}")
            # Keep metadata from fetch_video_info, skip media files
        else:
            info = downloaded
            media_path = info.video_path
            media_type = _classify_media(media_path)

            if media_type == "none" and info.thumbnail_path:
                media_path = info.thumbnail_path
                media_type = "image"
                info.thumbnail_path = None

            if media_type == "video" and media_path:
                size = Path(media_path).stat().st_size
                if size > MAX_VIDEO_SIZE_BYTES:
                    logger.warning(f"[MediaHandler] Video too large ({size / 1e6:.1f} MB), skipping send")
                    media_path = None
                    media_type = "none"

            thumbnail_path = info.thumbnail_path

    # Step 3: generate Twitter caption regardless of whether media was downloaded
    logger.info(f"[MediaHandler] Generating Twitter caption for: {info.title or url}")
    try:
        caption = await generate_twitter_caption(
            title=info.title,
            description=info.description,
            transcript=info.transcript,
            url=url,
        )
    except Exception as e:
        logger.error(f"[MediaHandler] Caption generation failed: {e}")
        caption = f"⚠️ Caption generation failed: {e}"

    return {
        "caption": caption,
        "media_path": media_path,
        "media_type": media_type,
        "thumbnail_path": thumbnail_path,
        "title": info.title,
        "error": None,
    }
