# CLAUDE.md


## Commit messages

Always end commit messages with:

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

## Project overview

Python multi-agent system that curates news daily across 11 niches, drafts creator-ready social media content, and delivers it through a Telegram bot. Self-hostable via Docker. Runs as a Telegram bot + FastAPI server.

## Tech stack

- **Runtime:** Python 3.11
- **Telegram:** python-telegram-bot v21
- **AI (news/content):** DeepSeek API (`deepseek-chat`, default) 
- **AI (video captions):** DeepSeek API (`deepseek-chat`)
- **Video download:** yt-dlp
- **Scheduler:** APScheduler (daily digest at 08:00 GMT+7)
- **HTTP:** httpx (async)
- **Feed parsing:** feedparser, BeautifulSoup4
- **API server:** FastAPI (`:8000`)
- **Pipeline:** LangGraph StateGraph

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

# Docker (DeepSeek — recommended)
docker compose -f docker-compose.deepseek.yml up -d

```

No linter is configured — no ruff, flake8, or mypy setup exists. Pre-commit hooks run `detect-secrets` and basic file checks.

## How to set up

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env   # fill in TELEGRAM_BOT_TOKEN, REPORT_CHAT_IDS, DEEPSEEK_API_KEY

# 3. Start the bot
python main.py
```


Systemd service file: `kyvra-bot.service` (production VPS). CI/CD deploys via SSH on push to `main` (`.github/workflows/deploy.yml`).

## Environment variables

```
TELEGRAM_BOT_TOKEN=<from @BotFather>
REPORT_CHAT_IDS=<comma-separated telegram chat IDs>
REPORT_TIME=08:00                     # local time in TIMEZONE
TIMEZONE=Asia/Ho_Chi_Minh
ACTIVE_MODULE=crypto                  # see available modules below

# LLM provider (pick one)
CAPTION_LLM_PROVIDER=deepseek

# DeepSeek (default — reports, content, captions)
DEEPSEEK_API_KEY=<from platform.deepseek.com>
DEEPSEEK_MODEL=deepseek-chat



# Optional: additional data sources
X_BEARER_TOKEN=<twitter api v2 bearer>
NEWS_API_KEY=<newsapi.org>
PRODUCT_HUNT_API_KEY=<producthunt.com>
```

## Architecture

```
kyvra-agentic/
├── main.py                     # Entry point: bot + scheduler startup; --once flag for one-shot
├── api_server.py               # FastAPI server — GET /report, GET /status, POST /chat
├── config.py                   # All env vars + constants
├── Dockerfile                  # Docker image
├── docker-compose.deepseek.yml # DeepSeek API stack (no GPU needed)
├── setup.sh                    # Interactive self-host wizard
├── agents/
│   ├── state.py                # KyvraState TypedDict (shared pipeline state)
│   ├── graph.py                # LangGraph StateGraph — build_graph() + kyvra_graph singleton
│   ├── graph_runner.py         # GraphRunner — wraps compiled graph, public API
│   ├── registry.py             # load_module() lazy registry
│   ├── base.py                 # BaseAgent ABC + PipelineContext (legacy)
│   ├── supervisor.py           # SupervisorAgent (legacy, used by --once)
│   ├── analyst.py              # AnalystAgent (standalone)
│   ├── data_collector.py       # DataCollectorAgent
│   ├── narrative_scout.py      # NarrativeScoutAgent
│   ├── content_writer.py       # ContentWriterAgent + chat_with_llm()
│   └── nodes/
│       ├── collect.py          # Fetch, filter, dedup, story continuity
│       ├── analyst.py          # Confidence scoring + spike detection
│       ├── scout.py            # Trend heatmap builder
│       ├── writer.py           # LLM content generation
│       ├── publisher.py        # mark_seen (story continuity)
│       └── router.py           # after_collect(), after_parallel()
├── interfaces/
│   └── telegram/
│       ├── handlers.py         # All Telegram command + message handlers; AVAILABLE_MODULES list
│       ├── formatter.py        # Message formatting helpers
│       └── scheduler.py        # APScheduler daily combined digest
├── modules/
│   ├── base.py                 # Abstract BaseModule + RawItem + DataSource
│   ├── tech/                   # Tech/AI/GitHub
│   ├── crypto/                 # Bitcoin/DeFi/Web3
│   ├── vietnam/                # Vietnamese tech focus
│   ├── indie/                  # Indie hackers/SaaS
│   ├── parody/                 # Satirical news
│   ├── sport/                  # Sports
│   ├── political/              # Politics
│   ├── war/                    # War/conflict
│   ├── humor/                  # Entertainment/humor
│   ├── energy/                 # Energy/climate
│   ├── markets/                # Financial markets
│   └── video/                  # Video/image caption pipeline
│       ├── config.py           # Supported domains, yt-dlp opts
│       ├── downloader.py       # yt-dlp wrapper + transcript extraction
│       ├── caption_agent.py    # DeepSeek caption generation
│       ├── handler.py          # Full pipeline: download → caption
│       └── prompts.py          # English caption prompts (3 platforms)
├── services/
│   └── memory.py               # SQLite: voice profiles, seen items
├── utils/
│   └── cache.py                # TTL in-memory cache
└── tests/                      # pytest test suite
```

## LangGraph pipeline

```
START
  │
[collect]          ← fetch, filter, dedup, story continuity
  │
  ├── "empty" → END
  └── "score"
        │
  ┌─────┴─────┐
[analyst]   [scout]    ← parallel, no LLM
  └─────┬─────┘
        │
  ├── "quick_end" → END   (mode: quick | breaking)
  └── "write"
        │
        │
   [publisher]           ← mark_seen (story continuity)
        │
       END
```

`KyvraState` TypedDict flows through all nodes. Each node returns only the keys it modifies — LangGraph merges the diff.

`GraphRunner` (`agents/graph_runner.py`) wraps `kyvra_graph` with a `SupervisorAgent`-compatible API for handlers.

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

### Tweet hook buttons (inline keyboard)

After `/report`, each story gets a 🐦 Tweet #N button. Tapping it:
1. Generates a viral tweet hook for that story via LLM
2. Replies with the tweet in a code block — tap to copy

### Plain-text message handler

- If message starts with `http` and matches a supported video domain → triggers caption pipeline

## LLM routing

| Feature | Default provider | Config key |
|---------|-----------------|------------|
| `/report`, `/thread`, `/brief`, `/script`, `/newsletter`, `/chat`, tweet hooks | DeepSeek | `CONTENT_LLM_PROVIDER` |
| `/caption` — video/image captions | DeepSeek | `CAPTION_LLM_PROVIDER` |


## Adding a new module

1. Create `modules/<name>/` with `sources.py`, `config.py`, `prompts.py`
2. Implement all abstract methods from `modules/base.py:BaseModule`
3. Register in `agents/registry.py:load_module()` registry
4. Add to `AVAILABLE_MODULES` list in `interfaces/telegram/handlers.py`

## Known gotchas

- `REPORT_CHAT_IDS` must be set or daily reports go nowhere
- `DEEPSEEK_API_KEY` required for `/caption` and default content generation
- The bot and FastAPI server run in the same process (`main.py` starts both)
- python-telegram-bot v21 uses `asyncio` — all handlers must be `async def`
- yt-dlp downloads go to `/tmp/kyvra_video/` and are deleted after sending
- Video files > 50 MB are not sent to Telegram (caption still generated)
