"""
Video downloader using yt-dlp.
Downloads video, thumbnail, and extracts transcript/subtitles.
"""
import os
import logging
import asyncio
from pathlib import Path
from dataclasses import dataclass, field

from modules.video.config import YTDLP_VIDEO_OPTS, YTDLP_INFO_OPTS, DOWNLOAD_DIR, SUPPORTED_DOMAINS

logger = logging.getLogger(__name__)


@dataclass
class VideoInfo:
    url: str
    title: str = ""
    description: str = ""
    thumbnail_url: str = ""
    duration: int = 0          # seconds
    transcript: str = ""
    video_path: str | None = None
    thumbnail_path: str | None = None
    error: str | None = None


def is_supported_url(url: str) -> bool:
    return any(domain in url for domain in SUPPORTED_DOMAINS)


def _ensure_download_dir() -> Path:
    path = Path(DOWNLOAD_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _extract_transcript_from_subs(video_id: str, download_dir: Path) -> str:
    """Try to read subtitle file (.vtt or .srt) for the video."""
    for lang in ["vi", "en"]:
        for ext in ["vtt", "srt"]:
            sub_file = download_dir / f"{video_id}.{lang}.{ext}"
            if sub_file.exists():
                try:
                    raw = sub_file.read_text(encoding="utf-8", errors="ignore")
                    return _clean_subtitle_text(raw)
                except Exception:
                    pass
    return ""


def _clean_subtitle_text(raw: str) -> str:
    """Strip VTT/SRT timestamps and return plain text."""
    import re
    # Remove VTT header
    raw = re.sub(r"WEBVTT.*?\n\n", "", raw, flags=re.DOTALL)
    # Remove timestamp lines like: 00:00:01.000 --> 00:00:03.000
    raw = re.sub(r"\d{2}:\d{2}:\d{2}[.,]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[.,]\d{3}", "", raw)
    # Remove sequence numbers
    raw = re.sub(r"^\d+\s*$", "", raw, flags=re.MULTILINE)
    # Remove HTML tags
    raw = re.sub(r"<[^>]+>", "", raw)
    # Collapse whitespace
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    # Deduplicate consecutive identical lines
    deduped = []
    for line in lines:
        if not deduped or line != deduped[-1]:
            deduped.append(line)
    return " ".join(deduped)


async def fetch_video_info(url: str) -> VideoInfo:
    """Fetch video metadata without downloading."""
    try:
        import yt_dlp
    except ImportError:
        return VideoInfo(url=url, error="yt-dlp not installed. Run: pip install yt-dlp")

    info = VideoInfo(url=url)
    try:
        opts = {**YTDLP_INFO_OPTS}

        def _run():
            with yt_dlp.YoutubeDL(opts) as ydl:
                return ydl.extract_info(url, download=False)

        data = await asyncio.to_thread(_run)
        info.title = data.get("title", "")
        info.description = (data.get("description") or "")[:1000]
        info.thumbnail_url = data.get("thumbnail", "")
        info.duration = data.get("duration", 0) or 0

        # Try auto-captions
        auto_captions = data.get("automatic_captions", {})
        subtitles = data.get("subtitles", {})
        for lang in ["vi", "en"]:
            if lang in subtitles or lang in auto_captions:
                # Mark as available; actual text extracted after download
                break

    except Exception as e:
        info.error = str(e)
        logger.error(f"[VideoInfo] Failed to fetch info for {url}: {e}")

    return info


async def download_media(url: str) -> VideoInfo:
    """
    Smart download: inspect what's available first, then download only what exists.
    - Has video  → download video + subtitles
    - Image only → download thumbnail via httpx
    - No media   → return metadata only (no error)
    """
    try:
        import yt_dlp
    except ImportError:
        return VideoInfo(url=url, error="yt-dlp not installed. Run: pip install yt-dlp")

    download_dir = _ensure_download_dir()

    # Step 1: extract info without downloading
    info = VideoInfo(url=url)
    try:
        def _get_info():
            with yt_dlp.YoutubeDL({**YTDLP_INFO_OPTS}) as ydl:
                return ydl.extract_info(url, download=False)

        data = await asyncio.to_thread(_get_info)
        info.title = data.get("title", "")
        info.description = (data.get("description") or "")[:1000]
        info.thumbnail_url = data.get("thumbnail", "")
        info.duration = data.get("duration", 0) or 0
        video_id = data.get("id", "unknown")

        # Determine if there is a real video stream
        formats = data.get("formats") or []
        has_video = any(
            f.get("vcodec", "none") != "none" and f.get("vcodec") is not None
            for f in formats
        )
    except Exception as e:
        info.error = str(e)
        logger.error(f"[Download] Info extraction failed for {url}: {e}")
        return info

    # Step 2a: has video → download it
    if has_video:
        logger.info(f"[Download] Video found, downloading: {info.title}")
        try:
            opts = {
                **YTDLP_VIDEO_OPTS,
                "outtmpl": str(download_dir / "%(id)s.%(ext)s"),
                "writethumbnail": False,
            }
            downloaded_path: dict = {}

            def _progress_hook(d: dict) -> None:
                if d["status"] == "finished":
                    downloaded_path["video"] = d.get("filename", "")

            opts["progress_hooks"] = [_progress_hook]

            def _download():
                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.extract_info(url, download=True)

            await asyncio.to_thread(_download)

            video_file = downloaded_path.get("video", "")
            if not video_file or not Path(video_file).exists():
                for f in download_dir.iterdir():
                    if f.stem == video_id and f.suffix in (".mp4", ".webm", ".mkv"):
                        video_file = str(f)
                        break

            if video_file and Path(video_file).exists():
                info.video_path = video_file

            info.transcript = _extract_transcript_from_subs(video_id, download_dir)

        except Exception as e:
            logger.warning(f"[Download] Video download failed: {e}")

    # Step 2b: no video but has thumbnail → download image via httpx
    elif info.thumbnail_url:
        logger.info(f"[Download] No video, downloading thumbnail image: {info.thumbnail_url}")
        ext = info.thumbnail_url.split("?")[0].rsplit(".", 1)[-1].lower()
        if ext not in ("jpg", "jpeg", "png", "webp", "gif"):
            ext = "jpg"
        dest = download_dir / f"{video_id}_thumb.{ext}"
        try:
            import httpx
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                resp = await client.get(info.thumbnail_url)
                resp.raise_for_status()
                dest.write_bytes(resp.content)
            info.thumbnail_path = str(dest)
            logger.info(f"[Download] Thumbnail saved: {dest}")
        except Exception as e:
            logger.warning(f"[Download] Thumbnail download failed: {e}")

    # Step 2c: no media at all → caption-only, no error
    else:
        logger.info(f"[Download] No media found for {url} — caption-only mode")

    return info


def cleanup_video_files(*paths: str | None) -> None:
    """Delete downloaded files after sending to Telegram."""
    for path in paths:
        if path and Path(path).exists():
            try:
                Path(path).unlink()
            except Exception as e:
                logger.warning(f"[Cleanup] Could not delete {path}: {e}")
    # Also clean subtitle files in the same dir
    download_dir = Path(DOWNLOAD_DIR)
    if download_dir.exists():
        for f in download_dir.iterdir():
            if f.suffix in (".vtt", ".srt"):
                try:
                    f.unlink()
                except Exception:
                    pass
