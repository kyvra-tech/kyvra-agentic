# Kyvra Agentic – Technical Reference

This document is the authoritative technical reference for engineers working on this codebase. It covers system architecture, data flow, every major component, extension points, and operational details.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Repository Layout](#2-repository-layout)
3. [Configuration & Environment](#3-configuration--environment)
4. [LangGraph Pipeline](#4-langgraph-pipeline)
5. [State: KyvraState](#5-state-kyvrastate)
6. [Nodes Reference](#6-nodes-reference)
7. [GraphRunner – Public API](#7-graphrunner--public-api)
8. [Module System](#8-module-system)
9. [Services](#9-services)
10. [Interfaces](#10-interfaces)
11. [Data Models](#11-data-models)
12. [TrendPost Integration](#12-trendpost-integration)
13. [Video / Caption Pipeline](#13-video--caption-pipeline)
14. [Memory & Persistence](#14-memory--persistence)
15. [Testing](#15-testing)
16. [Adding a New Module](#16-adding-a-new-module)
17. [Deployment](#17-deployment)
18. [Known Constraints](#18-known-constraints)

---

## 1. System Overview

Kyvra Agentic is a multi-agent Python system that:

1. **Collects** news from RSS feeds, Reddit, GitHub Trending, and other sources
2. **Scores** each item 0–100 using pure-Python heuristics (engagement, authority, recency)
3. **Generates** creator-ready content (reports, threads, newsletters, scripts) via a local LLM
4. **Delivers** content through a Telegram bot and a FastAPI HTTP server
5. **Pushes** top stories to TrendPost for scheduled auto-posting

The pipeline is orchestrated by a **LangGraph `StateGraph`**. All nodes are `async def` functions that receive the shared `KyvraState` TypedDict and return only the keys they modify — LangGraph merges the diff automatically.

The bot and FastAPI server share the same process (`main.py`), connected by the singleton `kyvra_graph` compiled graph instance.

---

## 2. Repository Layout

```
kyvra-agentic/
├── main.py                    # Process entry point
├── api_server.py              # FastAPI app factory
├── config.py                  # All env vars + typed constants
├── requirements.txt
├── .env.example
│
├── agents/
│   ├── state.py               # KyvraState TypedDict + empty_state()
│   ├── graph.py               # build_graph() + kyvra_graph singleton
│   ├── graph_runner.py        # GraphRunner adapter class
│   ├── registry.py            # load_module() lazy registry
│   ├── base.py                # BaseAgent ABC + PipelineContext (legacy)
│   ├── supervisor.py          # SupervisorAgent (legacy, still used by --once)
│   ├── analyst.py             # Standalone AnalystAgent (legacy)
│   ├── data_collector.py      # DataCollectorAgent (legacy)
│   ├── narrative_scout.py     # NarrativeScoutAgent (legacy)
│   ├── content_writer.py      # ContentWriterAgent (legacy)
│   └── nodes/
│       ├── collect.py         # collect_node
│       ├── analyst.py         # analyst_node
│       ├── scout.py           # scout_node
│       ├── writer.py          # writer_node
│       ├── publisher.py       # publisher_node
│       └── router.py          # after_collect(), after_parallel()
│
├── modules/
│   ├── base.py                # BaseModule ABC + RawItem + DataSource
│   ├── tech/                  # sources.py  prompts.py  config.py
│   ├── crypto/
│   ├── vietnam/
│   ├── indie/
│   ├── parody/
│   ├── sport/
│   ├── political/
│   ├── war/
│   ├── humor/
│   ├── energy/
│   ├── markets/
│   └── video/                 # downloader.py  handler.py  prompts.py  config.py
│
├── interfaces/
│   └── telegram/
│       ├── handlers.py        # All command + message handlers
│       ├── formatter.py       # Chunking + formatting helpers
│       └── scheduler.py       # APScheduler daily cron
│
├── services/
│   ├── llm.py                 # Ollama client (complete + chat modes)
│   ├── llm_provider.py        # Provider abstraction (Ollama / DeepSeek routing)
│   └── memory.py              # SQLite: seen items + voice profiles
│
├── utils/
│   └── cache.py               # TTL in-memory cache
│
└── tests/
    ├── test_analyst.py
    ├── test_data_collector.py
    ├── test_memory.py
    └── test_scheduler_push.py
```

---

## 3. Configuration & Environment

All configuration lives in `config.py`, which reads from environment variables (`.env` file via `python-dotenv`).

### Required

| Variable | Type | Description |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | str | From [@BotFather](https://t.me/BotFather) |
| `REPORT_CHAT_IDS` | str | Comma-separated Telegram chat IDs for daily auto-report |
| `ACTIVE_MODULE` | str | Active module slug, default `tech` |
| `OLLAMA_BASE_URL` | str | Ollama server URL, default `http://localhost:11434` |
| `OLLAMA_MODEL` | str | Model name, default `gemma3` |

### Optional

| Variable | Type | Description |
|---|---|---|
| `DEEPSEEK_API_KEY` | str | Required for `/caption` |
| `DEEPSEEK_MODEL` | str | Default `deepseek-chat` |
| `REPORT_TIME` | str | HH:MM for daily report, default `08:00` |
| `TIMEZONE` | str | Scheduler timezone, default `Asia/Ho_Chi_Minh` |
| `XAI_API_KEY` | str | Grok API key (alternate LLM backend) |
| `X_BEARER_TOKEN` | str | Twitter API v2 bearer token |
| `NEWS_API_KEY` | str | newsapi.org key |
| `PRODUCT_HUNT_API_KEY` | str | Product Hunt API key |
| `TRENDPOST_WEBHOOK_URL` | str | Outgoing webhook for story push |
| `TRENDPOST_WEBHOOK_SECRET` | str | HMAC-SHA256 shared secret |
| `TRENDPOST_API_URL` | str | Base URL for `/link` and STOP handler |

---

## 4. LangGraph Pipeline

### Graph shape

```
                    START
                      │
                  [collect]          ← fetch, filter, dedup, story continuity
                      │
           ┌──after_collect()──┐
         "empty"            "score"
           │                   │
          END       ┌──────────┴──────────┐
                [analyst]            [scout]    ← parallel, no dependency
                  └──────────┬──────────┘
                             │
                       after_parallel()
                      /               \
               "quick_end"          "write"
                   │                   │
                  END             [writer]      ← LLM call
                                      │
                               [publisher]      ← mark_seen + TrendPost push
                                      │
                                     END
```

### Graph construction (`agents/graph.py`)

```python
def build_graph(checkpointer=None) -> CompiledStateGraph:
    g = StateGraph(KyvraState)

    g.add_node("collect",   collect_node)
    g.add_node("analyst",   analyst_node)
    g.add_node("scout",     scout_node)
    g.add_node("join",      _parallel_join)   # fan-in pass-through
    g.add_node("writer",    writer_node)
    g.add_node("publisher", publisher_node)

    g.add_edge(START, "collect")
    g.add_conditional_edges("collect", after_collect, {"empty": END, "score": "analyst"})
    g.add_edge("collect", "scout")           # fan-out
    g.add_edge("analyst", "join")
    g.add_edge("scout",   "join")
    g.add_conditional_edges("join", after_parallel, {"quick_end": END, "write": "writer"})
    g.add_edge("writer",    "publisher")
    g.add_edge("publisher", END)

    return g.compile(checkpointer=checkpointer)

kyvra_graph = build_graph()   # module-level singleton, no checkpointer
```

### Parallel execution

LangGraph runs `analyst` and `scout` concurrently because both have an edge from `collect` and both have an edge to `join`. The `join` node (`_parallel_join`) is a pass-through that acts as the fan-in synchronization barrier — LangGraph will not advance past `join` until both upstream nodes have completed.

### Routing modes

| `mode` value | `after_collect` result | `after_parallel` result | LLM called? |
|---|---|---|---|
| `full` | `"score"` | `"write"` | Yes |
| `topic` | `"score"` | `"write"` | Yes |
| `quick` | `"score"` | `"quick_end"` | No |
| `breaking` | `"score"` | `"quick_end"` | No |

If `collect` returns no items, `after_collect` returns `"empty"` → graph exits early regardless of mode.

---

## 5. State: KyvraState

Defined in `agents/state.py`. Every node receives the full state and returns a `dict` of only the keys it modifies.

```python
class KyvraState(TypedDict):
    # ── Inputs (set before ainvoke) ──────────────────────────────────
    module_name:    str                          # "tech" | "crypto" | ...
    mode:           str                          # "full" | "quick" | "topic" | "breaking"
    topic_filter:   str | None                   # keyword for /topic command
    content_format: str                          # "report" | "thread" | "brief" | "newsletter" | "script"
    content_rank:   int                          # 1-based story rank for single-story formats

    # ── collect_node outputs ─────────────────────────────────────────
    raw_items:      list[RawItem]                # all fetched + deduped items

    # ── analyst_node outputs ─────────────────────────────────────────
    scored_items:   list[ScoredItem]             # top 14 scored items
    top_items:      list[ScoredItem]             # top 7 passed to writer

    # ── scout_node outputs ───────────────────────────────────────────
    trend_heatmap:  str                          # "AI Agents 🔥 | LLM 📈 | ..."

    # ── writer_node outputs ──────────────────────────────────────────
    report_text:    str                          # final prose

    # ── publisher_node outputs ───────────────────────────────────────
    published:      bool

    # ── shared error log ─────────────────────────────────────────────
    errors:         list[str]
```

`empty_state()` returns a fully-initialized KyvraState with safe defaults. Always use it to build the initial state before calling `ainvoke()`.

---

## 6. Nodes Reference

### `collect_node` (`agents/nodes/collect.py`)

**Responsibility:** Fetch raw items from all module sources, filter by keyword relevance, deduplicate, apply story continuity.

**Algorithm:**
1. `load_module(state["module_name"])` — gets the concrete module instance
2. `asyncio.gather(*[src.fetch() for src in module.sources])` — parallel fetch across all sources
3. Keyword filter: items must match at least one module keyword, unless the source sets `bypass_filter=True`
4. URL + title dedup: tracks `seen_urls` and `seen_titles`; increments `cross_source_count` on duplicates
5. Story continuity: recirculates spikes from X/Twitter sources if they appeared in the last 48h
6. Returns `{"raw_items": deduped_items, "errors": errors}`

### `analyst_node` (`agents/nodes/analyst.py`)

**Responsibility:** Score each item 0–100, detect spikes. Pure Python, no LLM.

**Scoring breakdown:**

| Component | Max pts | Logic |
|---|---|---|
| Engagement | 40 | GitHub stars/day or X likes/retweets scaled logarithmically |
| Authority | 20 | Source authority score from module config |
| Recency | 20 | `< 6h → 20`, `< 24h → 13`, `< 48h → 6`, older → 0 |
| Relevance | 10 | Base score for passing the keyword filter |
| Cross-source | 10 | +5 per additional source mentioning the same item (max 2 boosts) |
| Velocity | 10 | Stars/hour or engagement rate above module baseline |

**Spike detection:** Item is `is_spike=True` if GitHub stars/day ≥ module spike threshold **or** X engagement ≥ X spike threshold.

Returns `{"scored_items": top_14, "top_items": top_7}`.

### `scout_node` (`agents/nodes/scout.py`)

**Responsibility:** Build a trend heatmap string from topic extraction. Pure Python, no LLM.

**Algorithm:**
1. For each item title + summary, scan for topic keywords from a per-module topic map
2. Count keyword hits per topic
3. Assign heat emoji: 🔥 (5+), 📈 (4+), 🟡 (3+), 👀 (2+), 📉 (1+)
4. Return top 4 topics as `"Topic 🔥 | Topic 📈 | ..."`

Falls back to module-specific default topics if no keywords matched.

Returns `{"trend_heatmap": heatmap_string}`.

### `writer_node` (`agents/nodes/writer.py`)

**Responsibility:** Call the LLM to generate the requested content format.

**Algorithm:**
1. Select prompt builder based on `state["content_format"]` (report / thread / brief / newsletter / script)
2. Clamp `content_rank` to `len(top_items)` to avoid index errors
3. Call `services.llm_provider.get_content_provider().generate(prompt, top_items, trend_heatmap)`
4. On exception: append to errors, return fallback message

Returns `{"report_text": generated_text, "errors": updated_errors}`.

### `publisher_node` (`agents/nodes/publisher.py`)

**Responsibility:** Mark delivered stories as seen and push to TrendPost webhook.

**Algorithm:**
1. For each item in `top_items`: call `memory.mark_seen(url)` (SQLite)
2. If `TRENDPOST_WEBHOOK_URL` is set:
   - Serialize `top_items` to JSON
   - Sign with `HMAC-SHA256(TRENDPOST_WEBHOOK_SECRET, body)`
   - `POST` to webhook URL with header `x-kyvra-signature: sha256=<digest>`
3. Gracefully handles missing config and network errors without raising

Returns `{"published": True}`.

### `router.py` — conditional edge functions

```python
def after_collect(state: KyvraState) -> str:
    return "empty" if not state["raw_items"] else "score"

def after_parallel(state: KyvraState) -> str:
    return "quick_end" if state["mode"] in ("quick", "breaking") else "write"
```

---

## 7. GraphRunner – Public API

`GraphRunner` (`agents/graph_runner.py`) wraps `kyvra_graph` and exposes a clean interface to handlers and the API server. It is initialized with a module name: `GraphRunner("tech")`.

### Methods

| Method | Mode | LLM? | Returns |
|---|---|---|---|
| `generate_report()` | `full` | Yes | `str` — full AI report |
| `generate_report_with_ctx()` | `full` | Yes | `(str, KyvraState)` |
| `quick_scan()` | `quick` | No | `str` — scored items list |
| `generate_report_for_topic(topic)` | `topic` | Yes | `str` |
| `generate_brief(rank)` | `full` | Yes | `str` — 3-bullet summary |
| `generate_thread(rank)` | `full` | Yes | `str` — 7-tweet thread |
| `generate_newsletter(rank)` | `full` | Yes | `str` — newsletter section |
| `generate_script(rank)` | `full` | Yes | `str` — TikTok script |
| `generate_tweet_hook(rank)` | `full` | Yes | `str` — viral tweet hook |
| `get_status()` | `quick` | No | `dict` — health metrics (2h TTL cache) |
| `stream_events(mode, ...)` | any | depends | `AsyncGenerator[str, None]` — node progress events |

### `stream_events()`

Yields human-readable progress lines as each LangGraph node completes, used by Telegram handlers to send typing indicators or intermediate messages.

```python
async for event in runner.stream_events("full"):
    await bot.send_chat_action(chat_id, "typing")
```

### Status dict shape

```python
{
    "module": "tech",
    "items_fetched": 42,
    "top_score": 94,
    "spike_count": 3,
    "sources_ok": ["github", "rss_anthropic", "reddit_ml"],
    "sources_error": [],
    "last_run_at": "2026-06-05T08:00:00+07:00",
}
```

---

## 8. Module System

### BaseModule (`modules/base.py`)

Every module must subclass `BaseModule` and implement:

```python
class BaseModule(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...               # "tech", "crypto", etc.

    @property
    @abstractmethod
    def sources(self) -> list[DataSource]: ...  # list of DataSource instances

    @property
    @abstractmethod
    def keywords(self) -> list[str]: ...     # relevance filter keywords

    @property
    @abstractmethod
    def authority_scores(self) -> dict[str, int]: ...  # source → 0-20 score

    @property
    @abstractmethod
    def spike_threshold_github(self) -> int: ...

    @property
    @abstractmethod
    def spike_threshold_x(self) -> int: ...

    def get_prompt_builder(self, fmt: str) -> PromptBuilder: ...  # returns module's prompt
```

### DataSource (`modules/base.py`)

```python
@dataclass
class DataSource:
    name: str
    fetch: Callable[[], Awaitable[list[RawItem]]]
    bypass_filter: bool = False   # skip keyword filter for authoritative sources
```

### RawItem (`modules/base.py`)

```python
@dataclass
class RawItem:
    title: str
    url: str
    source: str
    published_at: str            # ISO 8601 string
    summary: str
    engagement: dict             # {"stars": 0, "likes": 0, "comments": 0, ...}
    cross_source_count: int = 1
```

### Module registry (`agents/registry.py`)

```python
_REGISTRY = {
    "tech":      "modules.tech.sources.TechModule",
    "crypto":    "modules.crypto.sources.CryptoModule",
    "vietnam":   "modules.vietnam.sources.VietnamModule",
    # ... 11 entries total
}

def load_module(name: str) -> BaseModule:
    # deferred import → instantiate → return
```

All imports are deferred inside `load_module()` for Python 3.9 compatibility and fast startup.

### Adding a module

See [Section 16](#16-adding-a-new-module).

---

## 9. Services

### `services/llm.py` — Ollama client

Low-level async client for the Ollama HTTP API.

```python
async def complete(prompt: str, model: str = OLLAMA_MODEL) -> str: ...
async def chat(messages: list[dict], model: str = OLLAMA_MODEL) -> str: ...
```

Uses `httpx.AsyncClient` with a 120s timeout. Raises `httpx.HTTPError` on failure.

### `services/llm_provider.py` — Provider abstraction

Selects the right backend based on config and the requested task.

```python
def get_content_provider() -> LLMProvider:
    # Returns OllamaProvider (default) or XAIProvider if XAI_API_KEY is set

def get_caption_provider() -> LLMProvider:
    # Always returns DeepSeekProvider (uses DEEPSEEK_API_KEY)
```

Each provider implements:

```python
class LLMProvider(ABC):
    async def generate(self, prompt: str, ...) -> str: ...
    async def chat(self, messages: list[dict], ...) -> str: ...
```

### `services/memory.py` — SQLite persistence

Backed by `~/.kyvra/memory.db` (or path from env). Two tables:

**`seen_items`** — story continuity dedup

```python
async def mark_seen(url: str) -> None: ...
async def is_seen(url: str) -> bool: ...
async def cleanup_old(days: int = 7) -> None: ...
```

**`voice_profiles`** — per-user writing style

```python
async def set_voice(chat_id: int, description: str) -> None: ...
async def get_voice(chat_id: int) -> str | None: ...
```

### `utils/cache.py` — TTL cache

Simple in-memory dict cache with per-key TTL. Used by `GraphRunner.get_status()` (2h TTL) and source fetch dedup.

```python
cache = TTLCache()
cache.set(key, value, ttl=7200)
value = cache.get(key)           # returns None if expired
```

---

## 10. Interfaces

### Telegram (`interfaces/telegram/handlers.py`)

All handlers are `async def` (python-telegram-bot v21 requirement). Each handler:
1. Sends an immediate acknowledgement (avoids Telegram timeout)
2. Instantiates `GraphRunner(module_name)`
3. Calls the appropriate `GraphRunner` method
4. Sends the result via `formatter.send_long_message()` (auto-chunks at 4096 chars)

**Inline keyboard — tweet hooks**

After `/report`, each story gets a `🐦 Tweet #N` button. `handle_tweet_callback()` is registered as a `CallbackQueryHandler`. On tap it calls `runner.generate_tweet_hook(rank)` and replies with the tweet in a code block.

**Plain-text message handler**

- URL matching a supported video domain → `handle_video_link()` → caption pipeline
- `"STOP"` (case-insensitive) → `handle_stop_message()` → TrendPost STOP webhook

**`AVAILABLE_MODULES`**

Defined at the top of `handlers.py`. Must be kept in sync with `agents/registry.py`.

### Scheduler (`interfaces/telegram/scheduler.py`)

Uses `APScheduler AsyncIOScheduler`. A single daily job runs `generate_report()` for each chat ID in `REPORT_CHAT_IDS` at `REPORT_TIME` in `TIMEZONE`.

### FastAPI (`interfaces/web/app.py` + `api_server.py`)

`api_server.py` exports `create_app() -> FastAPI`. Called by `main.py` to mount the API on port 8000 alongside the bot.

**Endpoints:**

| Method | Path | Description |
|---|---|---|
| `POST` | `/generate` | Run the full pipeline; body: `{module, mode, topic?, format?, rank?}` |
| `GET` | `/status` | Returns `GraphRunner.get_status()` for the active module |
| `POST` | `/webhook/stop` | Receives STOP signal from TrendPost UI |

Request/response bodies are Pydantic models. The `/generate` endpoint streams node events via `StreamingResponse` if `stream=true` is in the body.

### Formatter (`interfaces/telegram/formatter.py`)

```python
async def send_long_message(bot, chat_id, text, parse_mode="HTML") -> None:
    # splits at 4096 chars on paragraph boundaries
```

Also provides `format_report_html()` which wraps story sections in Telegram-safe HTML.

---

## 11. Data Models

### Confidence scoring (canonical)

```
score = engagement_score(item)     # 0-40
      + authority_score(item)      # 0-20
      + recency_score(item)        # 0-20
      + 10                         # relevance base
      + cross_source_boost(item)   # 0-10
      + velocity_score(item)       # 0-10
```

All scorer functions are exported from `agents/nodes/analyst.py` for unit test access.

### ScoredItem (legacy, `agents/base.py`)

```python
@dataclass
class ScoredItem:
    title: str
    url: str
    source: str
    published_at: str
    summary: str
    confidence_score: int    # 0-100
    is_spike: bool
    raw_score: int
    cross_source_count: int
```

In the LangGraph pipeline, `scored_items` and `top_items` in `KyvraState` hold `ScoredItem` instances (same dataclass, reused).

---

## 12. TrendPost Integration

### Story push (outgoing)

Triggered by `publisher_node` at the end of every full pipeline run.

```
POST TRENDPOST_WEBHOOK_URL
Headers:
  Content-Type: application/json
  x-kyvra-signature: sha256=<hmac-sha256(secret, body_bytes)>
Body:
{
  "stories": [{ "title", "url", "summary", "confidence_score", "source" }, ...],
  "module": "tech",
  "pushed_date": "2026-06-05"
}
```

Skipped silently if `TRENDPOST_WEBHOOK_URL` is not set.

### `/link` flow

```
User: /link
  │
  ▼
cmd_link():
  1. Generate random 6-digit code (expires 5 min)
  2. POST TRENDPOST_API_URL/api/webhooks/kyvra-link  (HMAC-signed)
     Body: { telegram_chat_id, code }
  3. Reply: "Your code: 123456 — enter it in TrendPost"
```

### STOP handler

```
User sends "STOP"
  │
  ▼
handle_stop_message():
  POST TRENDPOST_API_URL/api/webhooks/kyvra-stop  (HMAC-signed)
  Body: { telegram_chat_id }
```

TrendPost cancels the latest `pending_approval` schedule for that chat ID.

---

## 13. Video / Caption Pipeline

### Trigger

- Telegram: `/caption <url>` command or plain-text URL matching a supported domain
- Supported domains defined in `modules/video/config.py`

### Flow

```
URL
 │
 ▼
modules/video/downloader.py
  yt-dlp: download video + thumbnail + subtitles to /tmp/kyvra_video/<uuid>/
  Returns: VideoAsset { video_path, thumbnail_path, transcript, duration, title }
 │
 ▼
modules/video/handler.py
  Calls DeepSeek API (via llm_provider.get_caption_provider())
  Generates captions for 3 platforms:
    - TikTok / Reels: short hook, 3–5 hashtags
    - YouTube Shorts: longer, SEO title + description
    - Twitter/X:      1 punchy tweet
 │
 ▼
Telegram reply: media file + 3 captions in separate messages
Cleanup: /tmp/kyvra_video/<uuid>/ deleted after send
```

### Constraints

- Video files > 50 MB are not sent to Telegram (caption still generated from transcript/thumbnail)
- Transcript extraction uses yt-dlp's subtitle download; falls back to thumbnail-only caption if no subtitles

---

## 14. Memory & Persistence

### SQLite database

Path: `~/.kyvra/memory.db` by default. Created automatically on first run.

**`seen_items` table** — used by `publisher_node` and `collect_node`

| Column | Type | Notes |
|---|---|---|
| `url` | TEXT PK | normalized URL |
| `seen_at` | INTEGER | Unix timestamp |

Story continuity logic in `collect_node`: an item whose URL is in `seen_items` is dropped unless it is a spike AND was seen < 48h ago (recirculation window).

**`voice_profiles` table** — used by `/setvoice` and `writer_node`

| Column | Type | Notes |
|---|---|---|
| `chat_id` | INTEGER PK | Telegram chat ID |
| `voice` | TEXT | Free-text writing style description |
| `updated_at` | INTEGER | Unix timestamp |

`writer_node` prepends the voice profile as a system instruction when generating content for a specific chat ID.

---

## 15. Testing

```bash
pytest                          # run all tests
pytest tests/test_analyst.py   # single file
pytest -v -k "spike"           # filter by name
```

### Test files

| File | What it covers |
|---|---|
| `test_analyst.py` | Confidence scoring functions, spike detection, edge cases |
| `test_data_collector.py` | Source fetch mocking, dedup logic, keyword filter |
| `test_memory.py` | SQLite mark_seen / is_seen / voice profiles |
| `test_scheduler_push.py` | TrendPost webhook signing, HMAC verification |

All tests use `pytest-asyncio` for async test functions. External HTTP calls are mocked with `unittest.mock.AsyncMock`. No real Ollama or DeepSeek calls in tests.

---

## 16. Adding a New Module

### Step 1 — Create the module directory

```
modules/<name>/
├── __init__.py
├── config.py      # keywords, authority_scores, spike_thresholds, topic_map
├── sources.py     # concrete BaseModule subclass + DataSource list
└── prompts.py     # prompt builder functions per content format
```

### Step 2 — Implement `BaseModule` in `sources.py`

```python
from modules.base import BaseModule, DataSource, RawItem

class MyModule(BaseModule):
    @property
    def name(self) -> str:
        return "mymodule"

    @property
    def sources(self) -> list[DataSource]:
        return [
            DataSource(name="my_rss", fetch=self._fetch_rss),
            DataSource(name="my_reddit", fetch=self._fetch_reddit, bypass_filter=True),
        ]

    @property
    def keywords(self) -> list[str]:
        return ["keyword1", "keyword2"]

    @property
    def authority_scores(self) -> dict[str, int]:
        return {"my_rss": 15, "my_reddit": 8}

    @property
    def spike_threshold_github(self) -> int:
        return 200

    @property
    def spike_threshold_x(self) -> int:
        return 500

    async def _fetch_rss(self) -> list[RawItem]:
        # httpx + feedparser implementation
        ...
```

### Step 3 — Register in `agents/registry.py`

```python
_REGISTRY = {
    ...
    "mymodule": "modules.mymodule.sources.MyModule",
}
```

### Step 4 — Add to Telegram handler list

In `interfaces/telegram/handlers.py`:

```python
AVAILABLE_MODULES = ["tech", "crypto", ..., "mymodule"]
```

### Step 5 — Activate

```
ACTIVE_MODULE=mymodule  # in .env
```

Or at runtime: `/module mymodule` in Telegram.

---

## 17. Deployment

### Process model

`main.py` starts two concurrent tasks in a single asyncio event loop:
1. **python-telegram-bot** `Application.run_polling()` — handles Telegram updates
2. **uvicorn** running the FastAPI app on `:8000`

### systemd service

```ini
# kyvra-bot.service
[Unit]
Description=Kyvra Agentic Bot
After=network.target

[Service]
WorkingDirectory=/opt/kyvra-agentic
EnvironmentFile=/opt/kyvra-agentic/.env
ExecStart=/opt/kyvra-agentic/venv/bin/python main.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo cp kyvra-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable kyvra-bot
sudo systemctl start kyvra-bot
```

### CI/CD (`.github/workflows/deploy.yml`)

On push to `main`:
1. Run `detect-secrets` — blocks commit if any secret pattern found
2. SSH into production server
3. `git pull origin main`
4. Write `.env` from GitHub Actions secrets
5. `sudo systemctl restart kyvra-bot`

### Ollama (required on server)

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull gemma3
ollama serve    # or manage as a separate systemd service
```

---

## 18. Known Constraints

| Constraint | Detail |
|---|---|
| Ollama must be running | Bot will start but all LLM calls will fail with connection error if Ollama is not serving |
| `REPORT_CHAT_IDS` required | Daily auto-report silently skips if not set |
| Video files > 50 MB | Not sent to Telegram; caption still generated |
| python-telegram-bot v21 | All handlers **must** be `async def`; mixing sync handlers causes silent failures |
| Single-process model | Bot and API server share one asyncio loop; a blocking call in any handler stalls the whole process |
| SQLite concurrency | `memory.py` uses `aiosqlite`; safe for single-process use, not multi-process |
| `TRENDPOST_*` vars optional | All TrendPost features silently no-op if vars are missing — no error raised |
| yt-dlp rate limits | YouTube/Instagram may throttle; downloads go to `/tmp/kyvra_video/` and are deleted after send |
| Status cache TTL | `get_status()` caches for 2 hours per module; `/status` may show stale data after a module switch |
