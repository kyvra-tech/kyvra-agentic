# Kyvra Agentic – AI Content Agent

Modular, multi-agent Telegram bot that monitors news across 11 niches daily and generates reports, content angles, and creator-ready formats for social media.

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
- **TrendPost Integration** – push stories to TrendPost for scheduled auto-posting

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
                              [publisher]      ← mark_seen + TrendPost push
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
| `/link` | Generate a code to link with TrendPost auto-post |

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
│       ├── publisher.py       # mark_seen + TrendPost webhook push
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

## Setup

### Local development

```bash
# 1. Start Ollama with Gemma 3
ollama pull gemma3
ollama serve

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install pre-commit hooks (blocks commits containing secrets)
pip install pre-commit detect-secrets
pre-commit install

# 4. Configure environment
cp .env.example .env
# Edit .env – fill in required vars (see below)

# 5. Run
python main.py

# Run the pipeline once and print to stdout (no bot, no scheduler)
python main.py --once
```

### Required env vars

| Variable | Description |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Telegram bot token (from [@BotFather](https://t.me/BotFather)) |
| `REPORT_CHAT_IDS` | Comma-separated Telegram chat IDs for auto-report |
| `REPORT_TIME` | Daily report time, HH:MM format (default: `08:00`) |
| `TIMEZONE` | Timezone for scheduler (default: `Asia/Ho_Chi_Minh`) |
| `ACTIVE_MODULE` | Active module slug (default: `tech`) |
| `OLLAMA_BASE_URL` | Ollama server URL (default: `http://localhost:11434`) |
| `OLLAMA_MODEL` | Ollama model name (default: `gemma3`) |
| `DEEPSEEK_API_KEY` | DeepSeek API key – required for `/caption` |

### Optional env vars

| Variable | Description |
|---|---|
| `DEEPSEEK_MODEL` | DeepSeek model (default: `deepseek-chat`) |
| `XAI_API_KEY` | Grok API key (if using xAI as LLM backend) |
| `X_BEARER_TOKEN` | Twitter API v2 bearer token |
| `NEWS_API_KEY` | newsapi.org key |
| `PRODUCT_HUNT_API_KEY` | Product Hunt API key |
| `TRENDPOST_WEBHOOK_URL` | TrendPost story push endpoint |
| `TRENDPOST_WEBHOOK_SECRET` | HMAC secret shared with TrendPost |
| `TRENDPOST_API_URL` | TrendPost API base URL (for `/link` and STOP handler) |

### Production deployment (GitHub Actions → server)

Secrets are stored in **GitHub → Settings → Secrets and variables → Actions** — never in code.

On every push to `main`:
1. GitHub Actions runs `detect-secrets` — commit is blocked if any secret is found
2. If clean, the workflow SSHs into the server, writes `.env` from secrets, and restarts the bot via systemd

**First-time server setup:**
```bash
sudo cp kyvra-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable kyvra-bot
sudo systemctl start kyvra-bot
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
| 5 – Memory & Personalization | Voice profiles, seen-item suppression, topic subscriptions | 🔜 Next |
| 6 – Autonomous Mode | Breaking news push alerts, self-scheduling | Q3 |
