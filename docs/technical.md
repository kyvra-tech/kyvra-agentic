# Kyvra Agentic — Technical Documentation

## Overview

Kyvra is a multi-agent Python pipeline that monitors Tech/AI news sources, scores and ranks items, and generates daily briefings delivered via Telegram. Each agent in the pipeline has a single responsibility and communicates through a shared typed context object.

---

## Architecture

### Delivery layer model

The pipeline core (`agents/`, `modules/`, `services/`) is fully decoupled from delivery. Each interface in `interfaces/` calls `SupervisorAgent` independently:

```
interfaces/telegram/   → python-telegram-bot
interfaces/discord/    → discord.py          (Phase 2)
interfaces/web/        → FastAPI             (Phase 2)
        │
        └──► SupervisorAgent → Pipeline (agents + modules + services)
```

Adding a new interface requires zero changes to agents or modules.

---

### Pipeline execution model

```
SupervisorAgent.generate_report() / quick_scan()
    │
    ├── Phase 1  [sequential]
    │   DataCollectorAgent.run(ctx)
    │   • asyncio.gather(*[fetch_source(src) for src in sources])
    │   • keyword filter → cross-source dedup
    │   → ctx.raw_items: list[RawItem]
    │
    ├── Phase 2  [parallel — asyncio.gather]
    │   AnalystAgent.run(ctx)           NarrativeScoutAgent.run(ctx)
    │   • score_item() per RawItem      • keyword counter per topic
    │   • sort by (is_spike, score)     • top-4 topics → emoji heatmap
    │   → ctx.scored_items              → ctx.trend_heatmap: str
    │     ctx.top_items
    │
    └── Phase 3  [sequential, skipped by quick_scan()]
        ContentWriterAgent.run(ctx)
        • builds prompt from top_items + trend_heatmap
        • single LLM call (xAI Grok via OpenAI-compatible SDK)
        → ctx.report_text: str
```

`quick_scan()` runs only Phases 1 + 2. Used by `/update` and `/breaking` — no LLM cost, ~10 sec.

---

## Data model

### RawItem
Produced by `DataCollectorAgent`. Defined in [modules/base.py](../modules/base.py).

| Field | Type | Description |
|---|---|---|
| `title` | `str` | Item headline |
| `url` | `str` | Canonical URL |
| `source` | `str` | Source name (e.g. `"GitHub Trending"`, `"X - AI Leaders"`) |
| `published_at` | `str` | ISO 8601 or Unix timestamp string |
| `summary` | `str` | Short description or tweet text |
| `score` | `int` | Raw engagement signal (HN points, stars/day, X likes) |
| `comments` | `int` | Comment/reply count |
| `authority_score` | `int` | 0–20, set by module config per source |
| `cross_source_count` | `int` | Number of distinct sources covering this story (post-dedup) |

### ScoredItem
Produced by `AnalystAgent`. Defined in [agents/base.py](../agents/base.py).

Inherits all `RawItem` fields plus:

| Field | Type | Description |
|---|---|---|
| `confidence_score` | `int` | 0–100 composite score |
| `is_spike` | `bool` | True if engagement exceeds spike threshold |
| `raw_score` | `int` | Original engagement value before scoring |

### PipelineContext
The single state object passed through all agents. Defined in [agents/base.py](../agents/base.py).

| Field | Type | Populated by |
|---|---|---|
| `module` | `BaseModule` | Supervisor (at init) |
| `raw_items` | `list[RawItem]` | DataCollectorAgent |
| `scored_items` | `list[ScoredItem]` | AnalystAgent |
| `top_items` | `list[ScoredItem]` | AnalystAgent |
| `trend_heatmap` | `str` | NarrativeScoutAgent |
| `report_text` | `str` | ContentWriterAgent |
| `errors` | `list[str]` | Any agent (non-fatal failures) |

---

## Confidence Score (0–100)

Calculated in `AnalystAgent.score_item()` ([agents/analyst.py](../agents/analyst.py)):

```
confidence = engagement + authority + recency + relevance + cross_boost
```

| Component | Range | Logic |
|---|---|---|
| **Engagement** | 0–40 | Source-specific: HN points/10, GitHub stars/3, X likes/15 |
| **Authority** | 0–20 | Set in `modules/tech/config.py` per source |
| **Recency** | 0–20 | <6h=20, <24h=13, <48h=6, older=0 |
| **Relevance** | 10–20 | 10 base + 2 per extra keyword match, capped at 20 |
| **Cross-source boost** | 0 or 10 | +10 if same story appeared in 2+ sources |

**Spike detection** — `is_spike=True` when raw engagement exceeds thresholds defined in `modules/tech/config.py`:
- GitHub: `score >= GITHUB_STARS_SPIKE`
- X: `score >= X_SPIKE_THRESHOLD`

**Authority account floor** — X - AI Leaders source has a minimum engagement of 15 so that low-like announcements from authoritative accounts (e.g. @AnthropicAI) are not penalized.

---

## Modules system

A module encapsulates everything domain-specific. The agents are domain-agnostic.

```
modules/
  base.py          ← BaseModule ABC + RawItem dataclass
  tech/
    sources.py     ← TechModule (implements BaseModule)
    config.py      ← Thresholds, authority scores, keyword list
    prompts.py     ← LLM prompt templates
```

### BaseModule interface ([modules/base.py](../modules/base.py))

```python
class BaseModule(ABC):
    def get_sources(self) -> list[DataSource]: ...
    def get_keywords(self) -> list[str]: ...
    def get_report_prompt(self, items, heatmap) -> str: ...
```

### DataSource

```python
@dataclass
class DataSource:
    name: str           # used as item.source
    type: str           # "rss" | "hn" | "github" | "x"
    url: str            # API or feed URL
    authority_score: int  # 0–20, injected into every RawItem from this source
```

### Adding a new module

1. Create `modules/<niche>/` with `sources.py`, `config.py`, `prompts.py`
2. Subclass `BaseModule` in `sources.py`
3. Register in `agents/supervisor.py → load_module()`
4. Set `ACTIVE_MODULE=<niche>` in `.env`

Zero changes to any agent.

---

## Source fetchers

All fetching logic lives in [utils/api_client.py](../utils/api_client.py). The `fetch_source(src: DataSource)` function dispatches by `src.type`:

| Type | Fetcher | Data returned |
|---|---|---|
| `"github"` | GitHub Trending scrape (BeautifulSoup4) | Repo name, description, stars today |
| `"rss"` | feedparser | Feed entries with title, link, summary, published |
| `"x"` | X API v2 (Bearer token) | Tweets with like/reply counts, author info |

All fetchers are `async` and called with `asyncio.gather()` in Phase 1. Source failures are caught and logged as warnings — the pipeline continues with the remaining sources.

---

## LLM integration

The LLM is called **only once per report**, in `ContentWriterAgent`. The client is initialized in [services/llm.py](../services/llm.py) using the OpenAI-compatible xAI SDK with `base_url="https://api.x.ai/v1"` and `model="grok-3-latest"`.

The `/chat` command also calls the LLM directly via `chat_with_llm()` in [agents/content_writer.py](../agents/content_writer.py), with per-user conversation history stored in-memory (resets on restart, max 10 turns).

---

## Bot commands → pipeline mapping

Defined in [interfaces/telegram/handlers.py](../interfaces/telegram/handlers.py):

| Command | Supervisor method | Phase 3 |
|---|---|---|
| `/update` | `quick_scan()` | ❌ |
| `/breaking` | `quick_scan()` + spike filter | ❌ |
| `/report` | `generate_report()` | ✅ |
| `/topic [kw]` | `generate_report_for_topic(kw)` | ✅ |
| `/chat [msg]` | direct LLM call | ✅ |

---

## Configuration

All env vars loaded via `python-dotenv` in [config.py](../config.py):

| Variable | Default | Description |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | required | From @BotFather |
| `XAI_API_KEY` | required | xAI API key |
| `REPORT_CHAT_IDS` | required | Comma-separated Telegram chat IDs for auto-report |
| `REPORT_TIME` | `08:00` | Daily report time (HH:MM, Asia/Ho_Chi_Minh) |
| `ACTIVE_MODULE` | `tech` | Module name |
| `MAX_REPORT_ITEMS` | `7` | Top N items passed to ContentWriter |
| `X_BEARER_TOKEN` | optional | Required only if X sources are enabled |

---

## Project structure

```
agentic-kyvra/
├── main.py                          # Entry point – starts Telegram interface + scheduler
├── config.py                        # Env vars and global settings
│
├── agents/                          # Pipeline agents (domain-agnostic)
│   ├── base.py                      # BaseAgent + PipelineContext + ScoredItem
│   ├── supervisor.py                # Orchestrator: quick_scan / generate_report
│   ├── data_collector.py            # Async multi-source fetch + dedup
│   ├── analyst.py                   # Confidence Score + spike detection
│   ├── narrative_scout.py           # Trend heatmap
│   └── content_writer.py            # LLM report writer + /chat
│
├── modules/                         # Niche plugins (swap to change domain)
│   ├── base.py                      # BaseModule ABC + RawItem + DataSource
│   └── tech/
│       ├── sources.py               # TechModule (X, GitHub, RSS sources)
│       ├── prompts.py               # Grok prompt templates
│       └── config.py                # Keywords, authority scores, spike thresholds
│
├── interfaces/                      # Delivery channels (one folder per platform)
│   ├── telegram/
│   │   ├── handlers.py              # /start /report /update /breaking /topic /chat
│   │   ├── formatter.py             # Telegram message formatting + chunker
│   │   └── scheduler.py             # Daily 8AM cron job
│   ├── discord/
│   │   └── bot.py                   # Placeholder — Phase 2
│   └── web/
│       └── app.py                   # Placeholder — Phase 2 (FastAPI)
│
├── services/
│   └── llm.py                       # Centralized LLM client (xAI / OpenAI-compatible)
│
└── utils/
    ├── api_client.py                # Async fetchers: RSS / scrape / X API
    └── cache.py                     # TTL in-memory cache
```

---

## Running locally

```bash
# Install dependencies
pip install -r requirements.txt

# Install + initialize pre-commit (detect-secrets hook)
pip install pre-commit detect-secrets
pre-commit install

# Configure
cp .env.example .env  # fill in TELEGRAM_BOT_TOKEN and XAI_API_KEY

# Run
python main.py
```

---

## Pre-commit hooks

Configured in [.pre-commit-config.yaml](../.pre-commit-config.yaml):

| Hook | Purpose |
|---|---|
| `detect-secrets` | Blocks commits containing API keys or tokens |
| `trailing-whitespace` | File hygiene |
| `end-of-file-fixer` | File hygiene |
| `check-added-large-files` | Max 500 KB per file |
| `check-merge-conflict` | Catches unresolved conflict markers |
| `detect-private-key` | Blocks PEM/private key files |

The `.secrets.baseline` file is tracked in git and required by the `detect-secrets` hook.

---

## Deployment (GitHub Actions → systemd)

On push to `main`:
1. `detect-secrets` scan runs in CI
2. SSH into server, write `.env` from GitHub Secrets
3. `systemctl restart kyvra-bot`

See [.github/workflows/deploy.yml](../.github/workflows/deploy.yml) for the full workflow.
