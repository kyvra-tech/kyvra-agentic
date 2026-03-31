# Supported URL patterns for video download
SUPPORTED_DOMAINS = [
    "youtube.com", "youtu.be",
    "tiktok.com",
    "instagram.com",
    "twitter.com", "x.com",
    "facebook.com", "fb.watch",
    "reddit.com",
]

# yt-dlp options for video download
YTDLP_VIDEO_OPTS = {
    "format": "best[ext=mp4][filesize<50M]/best[ext=mp4]/best",
    "outtmpl": "%(id)s.%(ext)s",
    "quiet": True,
    "no_warnings": True,
    "writesubtitles": True,
    "writeautomaticsub": True,
    "subtitleslangs": ["en", "vi"],
    "skip_download": False,
}

YTDLP_INFO_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "skip_download": True,
    "writesubtitles": False,
}

# Max file size Telegram allows for video (50MB)
MAX_VIDEO_SIZE_BYTES = 50 * 1024 * 1024

# Temp directory for downloads
DOWNLOAD_DIR = "/tmp/kyvra_video"
