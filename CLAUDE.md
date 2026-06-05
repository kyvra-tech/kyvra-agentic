# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commit messages

Always end commit messages with:

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

## Project overview

Python multi-agent system that curates AI/tech news daily, drafts English social media content, and integrates with TrendPost (creator-backend) for auto-posting. Runs as a Telegram bot + FastAPI server.

## Tech stack

- **Runtime:** Python 3.11
- **Telegram:** python-telegram-bot v21
- **AI (news/content):** Ollama — Gemma 3 (local, primary)
- **AI (video captions):** DeepSeek API (`deepseek-chat`)
- **Video download:** yt-dlp
- **Scheduler:** APScheduler (daily report at 08:00 GMT+7)
- **HTTP:** httpx (async)
- **Feed parsing:** feedparser, BeautifulSoup4
- **API server:** FastAPI (`:8000`) — called by creator-backend

## Commands

```bash
# Run tests
pytest

# Run a single test file
pytest tests/test_analyst.py

# Run a single test by name
pytest tests/test_analyst.py::test_function_name -v

# Start the bot (normal mode)
python main.py

# Run the pipeline once and print to stdout (no bot, no scheduler)
python main.py --once
```

No linter is configured — no ruff, flake8, or mypy setup exists. Pre-commit hooks run `detect-secrets` and basic file checks.

## How to set up

```bash
# 1. Start Ollama with Gemma 3
ollama pull gemma3
ollama serve

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env   # fill in required vars

# 4. Start the bot
python main.py
```

Systemd service file: `kyvra-bot.service` (production VPS). CI/CD deploys via SSH on push to `main` (`.github/workflows/deploy.yml`).

## Environment variables

```
TELEGRAM_BOT_TOKEN=<from @BotFather>
ACTIVE_MODULE=tech                    # see available modules below
REPORT_CHAT_IDS=<comma-separated telegram chat IDs>
REPORT_TIME=08:00                     # local time in TIMEZONE
TIMEZONE=Asia/Ho_Chi_Minh

# Ollama (local LLM — news reports, content generation)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3

# DeepSeek (video/image caption generation)
DEEPSEEK_API_KEY=<from platform.deepseek.com>
DEEPSEEK_MODEL=deepseek-chat

# Optional: additional AI/news APIs
XAI_API_KEY=<Grok API key>
X_BEARER_TOKEN=<twitter api v2 bearer>
NEWS_API_KEY=<newsapi.org>
PRODUCT_HUNT_API_KEY=<producthunt.com>

# Optional: TrendPost integration
TRENDPOST_WEBHOOK_URL=https://api.trendpost.co/api/webhooks/kyvra-stories
TRENDPOST_WEBHOOK_SECRET=<hmac secret shared with creator-backend>
TRENDPOST_API_URL=https://api.trendpost.co
```

## Architecture

```
agentic-kyvra/
├── main.py                     # Entry point: bot + scheduler startup; --once flag for one-shot
├── config.py                   # All env vars + constants
├── api_server.py               # FastAPI server — POST /generate endpoint
├── agents/
│   ├── supervisor.py           # Orchestrates the full pipeline; load_module() registry
│   ├── data_collector.py       # Fetches GitHub Trending, RSS, Reddit
│   ├── analyst.py              # Confidence score (0-100)
│   ├── narrative_scout.py      # Angle / narrative selection
│   ├── content_writer.py       # Content draft via Ollama
│   └── base.py                 # BaseAgent (ABC) + PipelineContext dataclass
├── interfaces/
│   └── telegram/
│       ├── handlers.py         # All Telegram command + message handlers; AVAILABLE_MODULES list
│       ├── formatter.py        # Message formatting helpers
│       └── scheduler.py        # APScheduler setup (daily report)
├── modules/
│   ├── base.py                 # Abstract BaseModule class
│   ├── tech/                   # Tech/AI/Indie module
│   ├── crypto/                 # Bitcoin/DeFi/Web3 module
│   ├── vietnam/                # Vietnamese tech focus module
│   ├── indie/                  # Indie hackers/SaaS module
│   ├── parody/                 # Parody/satirical news module
│   ├── sport/                  # Sports module
│   ├── political/              # Politics module
│   ├── war/                    # War/conflict module
│   ├── humor/                  # Humor module
│   ├── energy/                 # Energy/climate module
│   ├── markets/                # Financial markets module
│   └── video/                  # Video/image caption module
│       ├── config.py           # Supported domains, yt-dlp opts
│       ├── downloader.py       # yt-dlp wrapper + transcript extraction
│       ├── caption_agent.py    # DeepSeek caption generation
│       ├── handler.py          # Full pipeline: download → caption
│       └── prompts.py          # English caption prompts (3 platforms)
├── services/
│   ├── llm.py                  # Ollama client (complete + chat)
│   └── memory.py               # SQLite: voice profiles, seen items
└── tests/                      # pytest test suite
```

## Agent pipeline

```
SupervisorAgent
  │
  ├─► DataCollectorAgent
  │     Sources: GitHub Trending (scrape), Reddit (ML, LocalLLaMA, SideProject),
  │              TLDR Tech RSS, Anthropic/OpenAI/DeepMind RSS
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
        Drafts English content via Ollama (Gemma 3)
        Formats for: report | thread | brief | newsletter | script
```

Context object `PipelineContext` (dataclass in `agents/base.py`) is threaded immutably through each agent: `module`, `raw_items`, `scored_items`, `top_items`, `trend_heatmap`, `report_text`, `errors`.

## Video/Image caption pipeline

```
User pastes URL (or /caption <url>)
  │
  ├─► modules/video/downloader.py
  │     yt-dlp: download video + thumbnail + subtitles
  │     Supported: YouTube, TikTok, Instagram, Twitter/X, Facebook, Reddit
  │
  └─► modules/video/caption_agent.py
        DeepSeek API: generate English captions for 3 platforms:
          - TikTok / Reels (short, viral hook, hashtags)
          - YouTube Shorts (detailed, SEO-friendly)
          - Twitter/X hook (1 compelling tweet)
        Bot sends back: media file + 3 captions
```

## Telegram commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message + quick start guide |
| `/help` | Full command reference with descriptions |
| `/update` | Fast news scan, no AI writing (~10 sec) |
| `/breaking` | Spike alerts only — viral or trending signals |
| `/topic [keyword]` | AI report scoped to one topic |
| `/report` | Full AI daily report + 🐦 Tweet buttons per story |
| `/brief [rank]` | 3-bullet shareable summary |
| `/thread [rank]` | 7-tweet X thread from top story |
| `/newsletter [rank]` | Newsletter section from top story |
| `/script [rank]` | TikTok/Reels voiceover script |
| `/status` | Source health: items fetched, top score, spikes |
| `/chat [message]` | Chat about today's news |
| `/setvoice [description]` | Save personal writing style for all content |
| `/module [name]` | Switch active module: tech \| crypto \| vietnam \| indie \| parody \| sport \| political \| war \| humor \| energy \| markets |
| `/caption [url]` | Download media + generate captions (or just paste a URL) |
| `/link` | Generate code to link with TrendPost auto-post |

### Tweet hook buttons (inline keyboard)

After `/report`, each story gets a 🐦 Tweet #N button. Tapping it:
1. Generates a viral tweet hook for that story via Ollama
2. Replies with the tweet in a code block — tap to copy

### Plain-text message handler

- If message starts with `http` and matches a supported video domain → triggers caption pipeline
- If message is `STOP` (case-insensitive) → cancels latest TrendPost pending auto-post

## LLM routing

| Feature | Model | Provider |
|---------|-------|----------|
| `/report`, `/thread`, `/brief`, `/script`, `/newsletter`, `/chat`, tweet hooks | Gemma 3 | Ollama (local) |
| `/caption` — video/image captions | deepseek-chat | DeepSeek API |

## TrendPost integration

### Story push (outgoing — agentic-kyvra → creator-backend)

After the daily pipeline runs, stories are pushed via HMAC-signed webhook:

```
POST TRENDPOST_WEBHOOK_URL
Header: x-kyvra-signature: sha256=<hmac-sha256(TRENDPOST_WEBHOOK_SECRET, body)>
Body: { stories: [...], module: "tech", pushed_date: "2026-03-22" }
```

### Telegram /link flow

```
User: /link
  │
  ▼
handlers.cmd_link():
  1. Generate random 6-digit code
  2. POST TRENDPOST_API_URL/api/webhooks/kyvra-link (HMAC-signed)
  3. Reply to user: "Your code: 123456 (expires in 5 minutes)"
  │
  ▼
User enters code in TrendPost web UI → creator-backend verifies + links account
```

### STOP handler

```
User sends "STOP" in Telegram
  │
  ▼
handlers.handle_stop_message()
  POST TRENDPOST_API_URL/api/webhooks/kyvra-stop (HMAC-signed)
  Body: { telegram_chat_id }
  │
  ▼
creator-backend cancels latest pending_approval schedule for that chat_id
```

## Adding a new module

1. Create `modules/<name>/` with `sources.py`, `config.py`, `prompts.py`
2. Implement all abstract methods from `modules/base.py:BaseModule`
3. Register in `agents/supervisor.py:load_module()` registry
4. Add to `AVAILABLE_MODULES` list in `interfaces/telegram/handlers.py`

## Known gotchas

- Ollama must be running before starting the bot (`ollama serve`)
- `REPORT_CHAT_IDS` must be set or daily reports go nowhere
- `TRENDPOST_WEBHOOK_URL` and `TRENDPOST_WEBHOOK_SECRET` are optional — if empty, push is skipped silently
- `TRENDPOST_API_URL` is needed for `/link` and STOP handler — fails gracefully if empty
- The bot and FastAPI server run in the same process (`main.py` starts both)
- python-telegram-bot v21 uses `asyncio` — all handlers must be `async def`
- yt-dlp downloads go to `/tmp/kyvra_video/` and are deleted after sending
- Video files > 50 MB are not sent to Telegram (caption still generated)
