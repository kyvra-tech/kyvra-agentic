# agentic-kyvra — CLAUDE.md

AI assistant context for the agentic-kyvra Python Telegram bot and AI news pipeline.

## Commit messages

Always end commit messages with:

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

## Project overview

Python multi-agent system that curates AI/tech news daily, drafts Vietnamese social media content, and integrates with TrendPost (creator-backend) for auto-posting. Runs as a Telegram bot + FastAPI server.

## Tech stack

- **Runtime:** Python 3.11
- **Telegram:** python-telegram-bot v21
- **AI:** Anthropic SDK (claude-sonnet-4-6), xAI Grok (optional)
- **Scheduler:** APScheduler (daily report at 08:00 GMT+7)
- **HTTP:** httpx (async)
- **Feed parsing:** feedparser, BeautifulSoup4
- **API server:** FastAPI (`:8000`) — called by creator-backend

## How to run

```bash
cd agentic-kyvra
pip install -r requirements.txt
cp .env.example .env   # fill in required vars
python main.py
```

Systemd service file: `kyvra-bot.service`

## Environment variables

```
TELEGRAM_BOT_TOKEN=<shared with creator-backend>
ANTHROPIC_API_KEY=<claude api key>
XAI_API_KEY=<grok api key, optional>
X_BEARER_TOKEN=<twitter api v2 bearer>
NEWS_API_KEY=<newsapi.org>
ACTIVE_MODULE=tech                    # tech | crypto | vietnam | indie
REPORT_CHAT_IDS=<comma-separated telegram chat IDs>
REPORT_TIME=08:00                     # local time in TIMEZONE
TIMEZONE=Asia/Ho_Chi_Minh
TRENDPOST_WEBHOOK_URL=https://api.trendpost.co/api/webhooks/kyvra-stories
TRENDPOST_WEBHOOK_SECRET=<hmac secret shared with creator-backend>
TRENDPOST_API_URL=https://api.trendpost.co   # for /link + STOP endpoints
```

## Architecture

```
agentic-kyvra/
├── main.py                     # Entry point: bot + scheduler startup
├── config.py                   # All env vars + constants
├── api_server.py               # FastAPI server — POST /generate endpoint
├── agents/
│   ├── supervisor.py           # Orchestrates the full pipeline
│   ├── data_collector.py       # Fetches HN, GitHub Trending, RSS
│   ├── analyst.py              # Confidence score (0-100)
│   ├── narrative_scout.py      # Angle / narrative selection
│   ├── content_writer.py       # Vietnamese draft via Claude
│   └── base.py                 # Base agent class
├── interfaces/
│   └── telegram/
│       ├── handlers.py         # Telegram command + message handlers
│       ├── formatter.py        # Message formatting helpers
│       └── scheduler.py        # APScheduler setup (daily report)
├── modules/
│   └── tech/                   # Tech/AI/Indie module data sources
│       └── sources.py          # HN, GitHub Trending, Anthropic/OpenAI/DeepMind RSS
├── services/                   # Shared utilities
└── tests/                      # pytest test suite
```

## Agent pipeline

```
SupervisorAgent
  │
  ├─► DataCollectorAgent
  │     Sources: HackerNews API, GitHub Trending (scrape), Anthropic RSS,
  │              OpenAI RSS, Google DeepMind RSS, X Bearer Token
  │
  ├─► AnalystAgent
  │     Confidence score 0-100:
  │       engagement  (0-40) — HN points/comments, GitHub stars
  │       authority   (0-20) — source credibility
  │       recency     (0-20) — hours since publish
  │       relevance   (10)   — base score for being in feed
  │
  ├─► NarrativeScoutAgent
  │     Selects angle: "first principles", "implications", "comparison", etc.
  │
  └─► ContentWriterAgent
        Drafts Vietnamese content via Claude claude-sonnet-4-6
        Formats for: thread | brief | newsletter | script
```

## Telegram commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message + feature overview |
| `/report` | Trigger a manual daily report now |
| `/chat <message>` | Chat with the AI about the latest stories |
| `/link` | Generate a 6-digit code to link with TrendPost auto-post |
| `/help` | Command reference |

### Plain-text message handler

Any plain-text message (not a command) is checked for the word **STOP** (case-insensitive). If matched:

1. Look up the user's Telegram `chat_id`
2. POST to `TRENDPOST_API_URL/api/webhooks/kyvra-stop` (HMAC-signed)
3. creator-backend cancels the user's latest `pending_approval` schedule

## TrendPost integration

### Story push (outgoing — agentic-kyvra → creator-backend)

After the daily pipeline runs, stories are pushed via HMAC-signed webhook:

```
POST TRENDPOST_WEBHOOK_URL
Header: x-kyvra-signature: sha256=<hmac-sha256(TRENDPOST_WEBHOOK_SECRET, body)>
Body: { stories: [...], module: "tech", pushed_date: "2026-03-22" }
```

### Telegram /link flow (agentic-kyvra → creator-backend)

```
User: /link
  │
  ▼
handlers.cmd_link():
  1. Generate random 6-digit code
  2. POST TRENDPOST_API_URL/api/webhooks/kyvra-link (HMAC-signed)
     Body: { telegram_chat_id, link_code }
  3. Reply to user: "Your code: 123456 (expires in 10 minutes)"
  │
  ▼
User enters code in TrendPost web UI → creator-backend verifies + links account
```

### STOP handler (agentic-kyvra → creator-backend)

```
User sends "STOP" in Telegram
  │
  ▼
handlers.handle_stop_message():
  POST TRENDPOST_API_URL/api/webhooks/kyvra-stop (HMAC-signed)
  Body: { telegram_chat_id }
  │
  ▼
creator-backend cancels latest pending_approval schedule for that chat_id
```

## HMAC signing (all outgoing calls to creator-backend)

```python
import hmac, hashlib, json

def _sign(payload: dict, secret: str) -> str:
    body = json.dumps(payload, separators=(',', ':')).encode()
    sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={sig}"

headers = {
    "x-kyvra-signature": _sign(payload, TRENDPOST_WEBHOOK_SECRET),
    "Content-Type": "application/json",
}
```

## FastAPI server (`api_server.py`)

The FastAPI app runs on `:8000` alongside the bot. creator-backend calls it:

```
POST /generate
  Body: { story_url, format, platform, voice_style }
  Returns: { content: "..." }

GET /health
  Returns: { status: "ok" }
```

Authentication: Bearer token (`KYVRA_API_KEY` on creator-backend side).

## Adding a new module

1. Create `modules/<name>/sources.py` — define data sources
2. Add `<name>` to the `ACTIVE_MODULE` env var options
3. Register sources in `DataCollectorAgent`
4. Add to `MODULES` list in creator-frontend `KyvraFeed.tsx`

## Known gotchas

- `REPORT_CHAT_IDS` must be set or daily reports go nowhere
- `TRENDPOST_WEBHOOK_URL` and `TRENDPOST_WEBHOOK_SECRET` are optional — if empty, the push step is skipped silently (integration disabled)
- `TRENDPOST_API_URL` is needed for `/link` and STOP handler — if empty those features fail gracefully
- The bot and FastAPI server run in the same process (`main.py` starts both)
- python-telegram-bot v21 uses `asyncio` — all handlers must be `async def`
