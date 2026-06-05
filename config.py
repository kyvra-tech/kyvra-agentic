import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
XAI_API_KEY = os.getenv("XAI_API_KEY", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
X_BEARER_TOKEN = os.getenv("X_BEARER_TOKEN", "")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
PRODUCT_HUNT_API_KEY = os.getenv("PRODUCT_HUNT_API_KEY", "")
GROK_MODEL = os.getenv("GROK_MODEL", "grok-3-latest")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3")

# Anthropic Claude (optional — used when CONTENT_LLM_PROVIDER=claude)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")

# LLM provider routing (services/llm_provider.py)
# Options: deepseek | ollama | claude
CONTENT_LLM_PROVIDER = os.getenv("CONTENT_LLM_PROVIDER", "deepseek")
CAPTION_LLM_PROVIDER = os.getenv("CAPTION_LLM_PROVIDER", "deepseek")

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

