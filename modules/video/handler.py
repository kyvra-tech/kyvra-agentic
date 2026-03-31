"""
Media caption handler — handles video and image URLs.
Decoupled from Telegram so it can be tested independently.
"""
import logging
from pathlib import Path

from modules.video.downloader import download_video, fetch_video_info, cleanup_video_files, is_supported_url
from modules.video.caption_agent import generate_all_captions
from modules.video.config import MAX_VIDEO_SIZE_BYTES

logger = logging.getLogger(__name__)

# Image extensions that yt-dlp may download for image posts
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mkv", ".mov", ".avi"}


def _classify_media(path: str | None) -> str:
    """Return 'video', 'image', or 'none'."""
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
    Full pipeline: download → caption.
    Handles both video and image posts (Instagram, Twitter/X, TikTok, etc.)

    Returns dict with keys:
      - caption: str
      - media_path: str | None        (main media file: video or image)
      - media_type: 'video'|'image'|'none'
      - thumbnail_path: str | None    (thumbnail for videos)
      - title: str
      - error: str | None
    """
    if not is_supported_url(url):
        return {"error": "Unsupported URL. Supported: YouTube, TikTok, Instagram, Twitter/X, Facebook, Reddit"}

    # Step 1: fetch info (fast, no download) to get title/description
    info = await fetch_video_info(url)
    if info.error:
        return {"error": f"Could not read media: {info.error}"}

    # Step 2: download media + thumbnail + subtitles
    logger.info(f"[MediaHandler] Downloading: {info.title} ({url})")
    info = await download_video(url)

    if info.error:
        return {"error": f"Download failed: {info.error}"}

    # Step 3: classify what was downloaded
    media_path = info.video_path
    media_type = _classify_media(media_path)

    # If no video found, check if thumbnail is an image post (e.g. Instagram photo)
    if media_type == "none" and info.thumbnail_path:
        media_path = info.thumbnail_path
        media_type = "image"
        info.thumbnail_path = None  # don't double-send

    # Step 4: check file size for videos
    if media_type == "video" and media_path:
        size = Path(media_path).stat().st_size
        if size > MAX_VIDEO_SIZE_BYTES:
            logger.warning(f"[MediaHandler] Video too large ({size / 1e6:.1f} MB), will skip video send")
            media_path = None
            media_type = "none"

    # Step 5: generate caption with DeepSeek
    logger.info(f"[MediaHandler] Generating captions for: {info.title}")
    try:
        caption = await generate_all_captions(
            title=info.title,
            description=info.description,
            transcript=info.transcript,
        )
    except Exception as e:
        logger.error(f"[MediaHandler] Caption generation failed: {e}")
        caption = f"⚠️ Caption generation failed: {e}"

    return {
        "caption": caption,
        "media_path": media_path,
        "media_type": media_type,
        "thumbnail_path": info.thumbnail_path,
        "title": info.title,
        "error": None,
    }
