import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
PRODUCT_HUNT_API_KEY = os.getenv("PRODUCT_HUNT_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")

ACTIVE_MODULE = os.getenv("ACTIVE_MODULE", "tech")

REPORT_TIME = os.getenv("REPORT_TIME", "08:00")
REPORT_CHAT_IDS: list[int] = [
    int(cid.strip())
    for cid in os.getenv("REPORT_CHAT_IDS", "").split(",")
    if cid.strip().lstrip("-").isdigit()
]

TIMEZONE = "Asia/Ho_Chi_Minh"

# Max items per report
MAX_REPORT_ITEMS = 7

# Cache TTL in seconds
CACHE_TTL = 3600
