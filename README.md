# Kyvra Agentic – AI Content Agent

Modular, multi-agent Telegram bot that monitors Tech/AI/Indie Dev news daily and generates reports with content angles for creators.

---

## What it does

- **Daily Morning Report** – auto-sent at 8:00 AM (GMT+7) every day
- **On-demand Report** – trigger anytime via `/report`
- **AI Chat** – ask anything about tech/AI news via `/chat`
- **Content Angles** – every insight comes with a suggested Twitter thread, TikTok, or newsletter angle

---

## Architecture

```
User / Scheduler (Telegram / Cron)
          ↓
    SupervisorAgent (Orchestrator)
          ↓
├── DataCollectorAgent   → fetches from HN, GitHub, Anthropic/OpenAI/DeepMind RSS
├── AnalystAgent         → calculates Confidence Score 0-100, flags spikes
├── NarrativeScoutAgent  → builds trend heatmap from scored items
└── ContentWriterAgent   → calls Claude to write the report
          ↓
    Telegram Bot → /report, /chat, /start, /help
```

Each agent is a plain Python class with `async def run(context) → context`. The supervisor passes a shared `context` dict through the pipeline — no tight coupling between agents.

---

## Report Format

```
🤖 KYVRA TECH REPORT – 03/03/2026

Top 7 Tech Insights today:

1. 🔥 Claude 4 launches with advanced tool use | Confidence: 94/100
   📌 Anthropic shipped Claude 4 with major improvements for agentic tasks...
   🎯 Content angle: "5-point thread: How Claude 4 changes the AI agent workflow"

2. 📈 New OSS framework hits #1 GitHub Trending | Confidence: 78/100
   ...

📊 Trend heatmap: AI Agents 🔥 | LLM / Models 📈 | Indie Dev / SaaS 🟡 | Open Source 👀

💡 TL;DR: Today was dominated by AI agent news and new model releases...
```

---

## Confidence Score (0–100)

| Signal | Points |
|---|---|
| Engagement (HN score, GitHub stars/day) | 0 – 40 |
| Source authority (Anthropic/OpenAI blog = 20) | 0 – 20 |
| Recency (< 6h = 20, < 24h = 13, < 48h = 6) | 0 – 20 |
| Relevance base (passed keyword filter) | 10 |

---

## Data Sources (Tech Module – all free)

| Source | Data |
|---|---|
| HackerNews API | Top stories, Show HN, scores + comments |
| GitHub Trending | Trending repos, stars/day |
| Anthropic Blog RSS | New models, research, announcements |
| OpenAI Blog RSS | Product launches, API updates |
| Google DeepMind Blog RSS | Research papers, Gemini updates |

---

## Stack

| Layer | Tech |
|---|---|
| Bot | python-telegram-bot v21 (async) |
| AI | Anthropic SDK – `claude-sonnet-4-6` |
| Scheduler | APScheduler 3.x (AsyncIOScheduler) |
| HTTP client | httpx (async) |
| RSS parsing | feedparser |
| HTML scraping | BeautifulSoup4 + lxml |
| Cache | In-memory TTL cache (no Redis needed) |

---

## Project Structure

```
agentic-kyvra/
├── main.py                    # Entry point – starts bot + scheduler
├── config.py                  # Env vars and global settings
├── requirements.txt
├── .env.example
│
├── agents/
│   ├── supervisor.py          # Pipeline orchestrator
│   ├── data_collector.py      # Async multi-source fetcher
│   ├── analyst.py             # Confidence Score engine
│   ├── narrative_scout.py     # Trend heatmap builder
│   └── content_writer.py      # Claude report writer + chat
│
├── modules/                   # Modular plugins – swap to change niche
│   ├── base.py                # Abstract BaseModule interface
│   └── tech/
│       ├── sources.py         # TechModule (implements BaseModule)
│       ├── prompts.py         # Claude prompt templates
│       └── config.py          # Keywords, authority scores, thresholds
│
├── bot/
│   ├── handlers.py            # Command handlers: /start /report /chat /help
│   ├── scheduler.py           # Daily report cron job
│   └── formatter.py           # Telegram message chunker (4096 char limit)
│
└── utils/
    ├── api_client.py          # Async fetchers: RSS / REST / scrape
    └── cache.py               # TTL in-memory cache
```

---

## Setup

### Local development

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Install pre-commit hooks (blocks commits that contain secrets)
pip install pre-commit
pre-commit install

# 3. Generate the secrets baseline (first time only)
detect-secrets scan > .secrets.baseline

# 4. Configure environment
cp .env.example .env
# Edit .env: add TELEGRAM_BOT_TOKEN and ANTHROPIC_API_KEY

# 5. Run
python main.py
```

### Production deployment (GitHub Actions → server)

Secrets are stored in **GitHub → Settings → Secrets and variables → Actions** — never in code.

| GitHub Secret | Description |
|---|---|
| `TELEGRAM_BOT_TOKEN` | From [@BotFather](https://t.me/BotFather) |
| `ANTHROPIC_API_KEY` | From [console.anthropic.com](https://console.anthropic.com) |
| `NEWS_API_KEY` | From [newsapi.org](https://newsapi.org) |
| `PRODUCT_HUNT_API_KEY` | From [api.producthunt.com](https://api.producthunt.com) |
| `REPORT_CHAT_IDS` | Comma-separated Telegram chat IDs |
| `SERVER_HOST` | SSH host of your server |
| `SERVER_USER` | SSH username |
| `SERVER_SSH_KEY` | Private SSH key for deployment |

On every push to `main`:
1. GitHub Actions runs `detect-secrets` — commit is blocked if any secret is found
2. If clean, the workflow SSHs into the server, writes `.env` from the secrets above, and restarts the bot via systemd

**First-time server setup:**
```bash
sudo cp kyvra-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable kyvra-bot
sudo systemctl start kyvra-bot
```

### Required env vars

| Variable | Description |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Telegram bot token |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `REPORT_CHAT_IDS` | Comma-separated Telegram chat IDs for auto-report |
| `REPORT_TIME` | Daily report time, HH:MM format (default: `08:00`) |
| `ACTIVE_MODULE` | Module to use (default: `tech`) |

---

## Telegram Commands

| Command | Description |
|---|---|
| `/start` | Welcome message + onboarding |
| `/report` | Trigger full report immediately |
| `/chat [message]` | Chat with AI about tech/AI news |
| `/help` | Show command list |

---

## Adding a New Module (Crypto, Finance, News…)

1. Create `modules/<niche>/` with `sources.py`, `prompts.py`, `config.py`
2. Implement `BaseModule` in `sources.py`
3. Add a case in `agents/supervisor.py → load_module()`
4. Set `ACTIVE_MODULE=<niche>` in `.env`

Zero changes to agents, bot, or scheduler.

---

## Roadmap

- **Phase 2** – Crypto module (whale moves, OI/Funding spikes, DeFiLlama)
- **Phase 2** – User preferences per chat (focus topics, content style)
- **Phase 3** – Auto-generate full Twitter thread / newsletter draft
- **Phase 3** – Multi-module support (user picks niche in bot)
- **Phase 4** – Pro tier, white-label API for agencies
