# Kyvra Agentic – AI Content Agent

Modular, multi-agent Telegram bot that monitors Tech/AI/Indie Dev news daily and generates reports with content angles for creators.

---

## What it does

- **Daily Morning Report** – auto-sent at 8:00 AM (GMT+7) every day
- **Fast Scan** – `/update` returns top scored items in ~10 sec, no LLM cost
- **Breaking Alerts** – `/breaking` shows only spike items (viral X tweets, HN front page)
- **Topic Report** – `/topic [keyword]` scopes the full AI report to one topic
- **AI Chat** – `/chat` lets you ask anything about tech/AI news with conversation history
- **Content Angles** – every insight comes with a suggested Twitter thread, TikTok, or newsletter angle

---

## Architecture

```
User / Scheduler (Telegram / Cron)
          ↓
    SupervisorAgent (Orchestrator)
          ↓
Phase 1:  DataCollectorAgent   → parallel fetch from all sources, keyword filter, cross-source dedup
          ↓
Phase 2:  AnalystAgent         ─┐  (run in parallel)
          NarrativeScoutAgent  ─┘
          ↓
Phase 3:  ContentWriterAgent   → calls Grok LLM to write the report
          ↓
    Telegram Bot → /report /update /breaking /topic /chat /start /help
```

Each agent implements `BaseAgent.run(ctx: PipelineContext) → PipelineContext`. The supervisor passes a typed `PipelineContext` dataclass through the pipeline — no tight coupling between agents.

`quick_scan()` runs only Phases 1 + 2 (no LLM), used by `/update` and `/breaking` for fast, cheap responses.

---

## Report Format

```
🤖 KYVRA TECH REPORT – 16/03/2026

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
| Engagement (HN score, GitHub stars/day, X likes) | 0 – 40 |
| Source authority (Anthropic/OpenAI blog = 20) | 0 – 20 |
| Recency (< 6h = 20, < 24h = 13, < 48h = 6) | 0 – 20 |
| Relevance base (passed keyword filter) | 10 |
| Cross-source boost (+5 per extra source, max 15) | 0 – 15 |

Items with engagement far above average are flagged as **spikes** (`is_spike=True`) and surfaced by `/breaking`.

---

## Data Sources (Tech Module – all free)

| Source | Data |
|---|---|
| X – AI Leaders | Tweets from top AI accounts (pre-curated list) |
| X – AI Trending | AI/LLM keyword search, min engagement filter |
| X – Indie Dev | Indie maker keyword search |
| HackerNews API | Top stories, Show HN, scores + comments |
| GitHub Trending | Trending repos, stars/day |
| Anthropic Blog RSS | New models, research, announcements |
| OpenAI Blog RSS | Product launches, API updates |
| Google DeepMind Blog RSS | Research papers, Gemini updates |

---

## Telegram Commands

| Command | Description |
|---|---|
| `/start` | Welcome message + command list |
| `/help` | Full command reference |
| `/update` | Fast scan – top scored items, no AI (~10 sec) |
| `/breaking` | Spike alerts only (viral/trending items) |
| `/topic [keyword]` | AI report scoped to one topic, e.g. `/topic openai` |
| `/report` | Full AI-written daily report (30–60 sec) |
| `/chat [question]` | Chat about tech news with conversation memory |

---

## Stack

| Layer | Tech |
|---|---|
| Bot | python-telegram-bot v21 (async) |
| AI | xAI SDK (OpenAI-compatible) – `grok-3-latest` |
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
│   ├── base.py                # BaseAgent + PipelineContext typed dataclass
│   ├── supervisor.py          # Pipeline orchestrator (quick_scan / generate_report)
│   ├── data_collector.py      # Async multi-source fetcher + cross-source dedup
│   ├── analyst.py             # Confidence Score engine + spike detection
│   ├── narrative_scout.py     # Trend heatmap builder
│   └── content_writer.py      # Grok report writer + /chat handler
│
├── modules/                   # Modular plugins – swap to change niche
│   ├── base.py                # Abstract BaseModule interface
│   └── tech/
│       ├── sources.py         # TechModule (implements BaseModule)
│       ├── prompts.py         # Grok prompt templates
│       └── config.py          # Keywords, authority scores, thresholds
│
├── bot/
│   ├── handlers.py            # Command handlers: /start /report /chat /help /update /breaking /topic
│   ├── scheduler.py           # Daily report cron job
│   └── formatter.py           # Telegram message chunker + update/breaking formatters
│
├── services/
│   └── llm.py                 # Centralized LLM client (xAI / OpenAI-compatible)
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

# 2. Install pre-commit hooks (blocks commits containing secrets)
pip install pre-commit detect-secrets
pre-commit install

# 3. Configure environment
cp .env.example .env
# Edit .env: add TELEGRAM_BOT_TOKEN and XAI_API_KEY

# 4. Run
python main.py
```

### Required env vars

| Variable | Description |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Telegram bot token (from [@BotFather](https://t.me/BotFather)) |
| `XAI_API_KEY` | xAI API key (from [console.x.ai](https://console.x.ai)) |
| `REPORT_CHAT_IDS` | Comma-separated Telegram chat IDs for auto-report |
| `REPORT_TIME` | Daily report time, HH:MM format (default: `08:00`) |
| `ACTIVE_MODULE` | Module to use (default: `tech`) |

### Production deployment (GitHub Actions → server)

Secrets are stored in **GitHub → Settings → Secrets and variables → Actions** — never in code.

| GitHub Secret | Description |
|---|---|
| `TELEGRAM_BOT_TOKEN` | From [@BotFather](https://t.me/BotFather) |
| `XAI_API_KEY` | From [console.x.ai](https://console.x.ai) |
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

---

## Adding a New Module (Crypto, Finance, Vietnam…)

1. Create `modules/<niche>/` with `sources.py`, `prompts.py`, `config.py`
2. Implement `BaseModule` in `sources.py`
3. Add a case in `agents/supervisor.py → load_module()`
4. Set `ACTIVE_MODULE=<niche>` in `.env`

Zero changes to agents, bot, or scheduler.

---

## Roadmap

See [ROADMAP.md](ROADMAP.md) for the full plan. High-level phases:

| Phase | Goal | Status |
|---|---|---|
| 0 – Foundation | Multi-agent pipeline, Telegram bot, daily report | ✅ Done |
| 1 – Signal Quality | Velocity signal, story continuity, `/status` command | 🔜 Next |
| 2 – More Sources | Reddit, Product Hunt, YouTube, TLDR Tech | Q2 |
| 3 – New Modules | Crypto, Vietnam, Indie niches | Q2–Q3 |
| 4 – Creator Outputs | `/thread` `/newsletter` `/script` `/brief` | Q3 |
| 5 – Memory | Seen-item suppression, user feedback, topic subscriptions | Q4 |
| 6 – Autonomous Mode | Breaking news push alerts, headless `--once` mode | Q4+ |
