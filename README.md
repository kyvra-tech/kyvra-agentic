# Kyvra Agentic – AI Content Agent

Modular, multi-agent Telegram bot that monitors news across 11 niches daily and generates reports, content angles, and creator-ready formats for social media.

**Free and open-source. Self-host in 60 seconds.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/kyvra-tech/kyvra-agentic)](https://github.com/kyvra-tech/kyvra-agentic/stargazers)

> If Kyvra saves you time, consider [sponsoring the project](https://github.com/sponsors/kyvra-tech) or sending a tip in crypto — wallet address at the bottom of this page.

---

## What it does

- **Daily Morning Report** – auto-sent at 8:00 AM (GMT+7) every day
- **Fast Scan** – `/update` returns top scored items in ~10 sec, no LLM cost
- **Breaking Alerts** – `/breaking` shows only spike items (viral/trending signals)
- **Topic Report** – `/topic [keyword]` scopes the full AI report to one topic
- **AI Chat** – `/chat` lets you ask anything about today's news
- **Creator Formats** – every report can be turned into a Twitter thread, newsletter section, TikTok script, or 3-bullet brief
- **Video Captions** – paste any YouTube/TikTok/Instagram URL to get AI-generated captions for 3 platforms
- **Multi-Module** – switch between 11 topic niches: tech, crypto, vietnam, indie, parody, sport, political, war, humor, energy, markets

---

## Architecture

The pipeline is built on **LangGraph** (`StateGraph`). Each node is an `async def` that returns only the keys it modifies; LangGraph merges them into a shared `KyvraState` TypedDict.

```
                    START
                      │
                  [collect]          ← fetch, filter, dedup, story continuity
                      │
           ┌──after_collect──┐
         "empty"          "score"
           │                 │
          END     ┌──────────┴──────────┐
                [analyst]           [scout]    ← parallel (no dependency)
                  └──────────┬──────────┘
                             │
                     after_parallel
                    /              \
             "quick_end"         "write"
                 │                  │
                END             [writer]       ← LLM call (Ollama)
                                   │
                              [publisher]      ← mark_seen (story continuity)
                                   │
                                  END
```

`GraphRunner` (`agents/graph_runner.py`) wraps the compiled graph and exposes a `SupervisorAgent`-compatible API to the Telegram handlers and FastAPI server.

`quick_scan()` routes to `quick_end` — runs collect + analyst + scout but skips the LLM writer, keeping `/update` and `/breaking` fast and free.

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
| Engagement (GitHub stars/day, HN points, Reddit score) | 0 – 40 |
| Source authority (Anthropic/OpenAI blog = 20) | 0 – 20 |
| Recency (< 6h = 20, < 24h = 13, < 48h = 6) | 0 – 20 |
| Relevance base (passed keyword filter) | 10 |
| Cross-source boost (+5 per extra source, max 15) | 0 – 15 |

Items with engagement far above average are flagged as **spikes** (`is_spike=True`) and surfaced by `/breaking`.

---

## Telegram Commands

| Command | Description |
|---|---|
| `/start` | Welcome message + quick start guide |
| `/help` | Full command reference |
| `/update` | Fast scan – top scored items, no AI (~10 sec) |
| `/breaking` | Spike alerts only (viral/trending items) |
| `/topic [keyword]` | AI report scoped to one topic, e.g. `/topic openai` |
| `/report` | Full AI-written daily report (30–60 sec) |
| `/brief [rank]` | 3-bullet shareable summary of a story |
| `/thread [rank]` | 7-tweet X thread from a story |
| `/newsletter [rank]` | Newsletter section from a story |
| `/script [rank]` | TikTok/Reels voiceover script |
| `/status` | Source health: items fetched, top score, spikes |
| `/chat [message]` | Chat about today's news |
| `/setvoice [description]` | Save personal writing style for all content |
| `/module [name]` | Switch active module (tech, crypto, vietnam, …) |
| `/caption [url]` | Download media + generate captions (or just paste a URL) |

---

## Stack

| Layer | Tech |
|---|---|
| Bot | python-telegram-bot v21 (async) |
| Orchestration | LangGraph (StateGraph) |
| AI – reports/content | Ollama – Gemma 3 (local) |
| AI – captions | DeepSeek API (`deepseek-chat`) |
| Scheduler | APScheduler 3.x (AsyncIOScheduler) |
| HTTP client | httpx (async) |
| Feed parsing | feedparser + BeautifulSoup4 + lxml |
| Cache | In-memory TTL cache |
| API server | FastAPI (`:8000`) |
| Video download | yt-dlp |

---

## Project Structure

```
kyvra-agentic/
├── main.py                    # Entry point – starts Telegram bot + scheduler; --once flag
├── api_server.py              # FastAPI server – POST /generate endpoint
├── config.py                  # Env vars and global settings
├── requirements.txt
├── .env.example
│
├── agents/                    # Pipeline core
│   ├── state.py               # KyvraState TypedDict (shared pipeline state)
│   ├── graph.py               # LangGraph StateGraph definition + build_graph()
│   ├── graph_runner.py        # GraphRunner – wraps compiled graph, public API
│   ├── registry.py            # load_module() registry
│   ├── base.py                # BaseAgent + PipelineContext (legacy, kept for compat)
│   ├── supervisor.py          # SupervisorAgent (legacy orchestrator)
│   ├── analyst.py             # AnalystAgent (standalone, also used by analyst node)
│   ├── data_collector.py      # DataCollectorAgent
│   ├── narrative_scout.py     # NarrativeScoutAgent
│   ├── content_writer.py      # ContentWriterAgent
│   └── nodes/                 # LangGraph node functions
│       ├── collect.py         # Fetch, filter, dedup, story continuity
│       ├── analyst.py         # Confidence scoring + spike detection
│       ├── scout.py           # Trend heatmap builder
│       ├── writer.py          # LLM report/content generation
│       ├── publisher.py       # mark_seen (story continuity)
│       └── router.py          # Conditional edge functions (after_collect, after_parallel)
│
├── modules/                   # Niche plugins – swap to change domain
│   ├── base.py                # BaseModule ABC + RawItem + DataSource
│   ├── tech/                  # Tech/AI/GitHub
│   ├── crypto/                # Bitcoin/DeFi/Web3
│   ├── vietnam/               # Vietnamese tech focus
│   ├── indie/                 # Indie hackers/SaaS
│   ├── parody/                # Satirical news
│   ├── sport/                 # Sports
│   ├── political/             # Politics
│   ├── war/                   # War/conflict
│   ├── humor/                 # Humor
│   ├── energy/                # Energy/climate
│   └── markets/               # Financial markets
│
├── interfaces/
│   └── telegram/
│       ├── handlers.py        # All Telegram command + message handlers
│       ├── formatter.py       # Message formatting + chunker
│       └── scheduler.py       # Daily 8AM APScheduler cron
│
├── services/
│   ├── llm.py                 # Ollama client (complete + chat)
│   ├── llm_provider.py        # LLM provider abstraction (Ollama / DeepSeek routing)
│   └── memory.py              # SQLite: voice profiles, seen items
│
└── utils/
    └── cache.py               # TTL in-memory cache
```

---

## Self-Host in 60 Seconds

### Requirements

- [Docker Desktop](https://docs.docker.com/get-docker/) (Mac / Windows / Linux)
- A Telegram bot token — create one free at [@BotFather](https://t.me/BotFather)
- A DeepSeek API key — free tier at [platform.deepseek.com](https://platform.deepseek.com) (~$0.001/report)

### Quickstart

```bash
git clone https://github.com/kyvra-tech/kyvra-agentic.git
cd kyvra-agentic
bash setup.sh
```

The setup script walks you through config, pulls the right Docker images, and starts the bot. Open Telegram and send `/start` to your bot when it's done.

### Manual setup (if you prefer)

```bash
# 1. Clone and configure
git clone https://github.com/kyvra-tech/kyvra-agentic.git
cd kyvra-agentic
cp .env.example .env
# Edit .env — fill in TELEGRAM_BOT_TOKEN, REPORT_CHAT_IDS, DEEPSEEK_API_KEY

# 2a. Start with DeepSeek (no GPU needed — recommended)
docker compose -f docker-compose.deepseek.yml up -d

# 2b. Or start with local Ollama (free, needs a decent machine)
docker compose up -d
# First run pulls gemma3 (~5 GB) — give it a few minutes
```

### Updating

```bash
git pull
docker compose up -d --build
```

### Environment variables

**Required:**

| Variable | Description |
|---|---|
| `TELEGRAM_BOT_TOKEN` | From [@BotFather](https://t.me/BotFather) |
| `REPORT_CHAT_IDS` | Your Telegram chat ID — find it with [@userinfobot](https://t.me/userinfobot) |
| `DEEPSEEK_API_KEY` | From [platform.deepseek.com](https://platform.deepseek.com) |

**LLM provider (pick one):**

| Variable | Default | Description |
|---|---|---|
| `CONTENT_LLM_PROVIDER` | `deepseek` | `deepseek` \| `ollama` \| `claude` |
| `CAPTION_LLM_PROVIDER` | `deepseek` | Same options |
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Only if using Ollama |
| `OLLAMA_MODEL` | `gemma3` | Only if using Ollama |
| `ANTHROPIC_API_KEY` | — | Only if using Claude |

**Optional:**

| Variable | Description |
|---|---|
| `ACTIVE_MODULE` | Default module: `crypto` \| `tech` \| `vietnam` \| … (default: `crypto`) |
| `REPORT_TIME` | Daily report time HH:MM (default: `08:00`) |
| `TIMEZONE` | Scheduler timezone (default: `Asia/Ho_Chi_Minh`) |
| `X_BEARER_TOKEN` | Twitter API bearer — improves signal quality |
| `NEWS_API_KEY` | [newsapi.org](https://newsapi.org) key |

### VPS / server deployment (systemd)

```bash
# On your server
git clone https://github.com/kyvra-tech/kyvra-agentic.git /opt/kyvra-agentic
cd /opt/kyvra-agentic
cp .env.example .env && nano .env

sudo cp kyvra-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now kyvra-bot
```

CI/CD via GitHub Actions is also supported — see `.github/workflows/deploy.yml`.

### Local development (no Docker)

```bash
# 1. Start Ollama
ollama pull gemma3 && ollama serve

# 2. Install deps
pip install -r requirements.txt

# 3. Configure and run
cp .env.example .env  # fill in vars
python main.py

# Run pipeline once, print to stdout
python main.py --once
```

---

## Adding a New Module

1. Create `modules/<name>/` with `sources.py`, `prompts.py`, `config.py`
2. Implement all abstract methods from `modules/base.py:BaseModule`
3. Register in `agents/registry.py:load_module()` registry
4. Add to `AVAILABLE_MODULES` list in `interfaces/telegram/handlers.py`
5. Set `ACTIVE_MODULE=<name>` in `.env`

Zero changes to agents, graph, or scheduler.

---

## Roadmap

See [ROADMAP.md](ROADMAP.md) for the full plan.

| Phase | Goal | Status |
|---|---|---|
| 0 – Foundation | Multi-agent pipeline, Telegram bot, daily report | ✅ Done |
| 1 – Signal Quality | Velocity signal, story continuity, `/status` | ✅ Done |
| 2 – More Sources | Reddit, TLDR Tech RSS, Product Hunt | ✅ Done |
| 3 – New Modules + Creator Formats | Crypto, Vietnam, Indie + `/thread` `/newsletter` `/script` `/brief` | ✅ Done |
| 4 – LangGraph Migration | StateGraph pipeline, parallel nodes, typed state | ✅ Done |
| 5 – Self-Host + Docker | One-command setup, open-source distribution | ✅ Done |
| 6 – Memory & Personalization | Voice profiles, seen-item suppression, topic subscriptions | 🔜 Next |
| 7 – Autonomous Mode | Breaking news push alerts, self-scheduling | Q3 |

---

## Contributing

Pull requests are welcome. For major changes, open an issue first.

```bash
# Run tests
pytest

# Run a single test
pytest tests/test_analyst.py -v
```

---

## Support the project

Kyvra is free and open-source. If it saves you time, consider supporting development:

- **GitHub Sponsors:** [github.com/sponsors/kyvra-tech](https://github.com/sponsors/kyvra-tech)
- **USDT:** `0x03496bd8005a48843e2Bda7450bEeba9dB42Dbfd`
- **Star the repo** — it helps more people find the project

Built with love for crypto creators.
