# TODOS — Kyvra Agentic

Deferred work from engineering reviews. Items are ordered by priority within each phase.
Last updated: 2026-03-20 (T-027–T-029 added from Kyvra↔TrendPost CEO review)

---

## Phase 1 — Ship-blocking fixes ✅ DONE (merged in develop branch)

All T-001 through T-007 implemented in the `develop` branch PR.

### T-001: Fix X_BEARER_TOKEN missing from CI deploy workflow
**What:** Add `X_BEARER_TOKEN=${{ secrets.X_BEARER_TOKEN }}` to the `.env` write block in `.github/workflows/deploy.yml`.
**Why:** X sources (AI Leaders, AI Trending, Indie Dev) silently skip on every production deploy because the token is never written to the server `.env`. The bot runs but without any X data — you're measuring a degraded product without knowing it.
**Pros:** X signal restored. Silent data degradation eliminated.
**Cons:** Requires adding `X_BEARER_TOKEN` as a GitHub Secret if not already present.
**Context:** Identified in architecture review. The `config.py` reads `X_BEARER_TOKEN` from env and `api_client.py:fetch_x_search()` checks it and returns `[]` silently if missing.
**Effort:** S
**Priority:** P1
**File:** `.github/workflows/deploy.yml` line 51–63

---

### T-002: Guard None content in services/llm.py
**What:** Change `return response.choices[0].message.content` to `return response.choices[0].message.content or ""` in both `complete()` and `chat()`.
**Why:** The xAI API (OpenAI-compatible) can return `content=None` for refusals or tool call responses. This `None` flows into `split_long_message(None)` in the formatter and raises a `TypeError` — the bot sends no reply and logs a traceback.
**Effort:** S
**Priority:** P1
**File:** `services/llm.py` lines 35, 46

---

### T-003: User-safe error message in ContentWriterAgent
**What:** Replace `ctx.report_text = f"Lỗi khi tạo report: {e}"` with a generic fallback. Log the full error internally.
**Why:** The raw Python exception string (e.g., `RateLimitError: You have exceeded your quota`) is sent directly to users in Telegram and to all REPORT_CHAT_IDS via the scheduler.
**Effort:** S
**Priority:** P1
**File:** `agents/content_writer.py`

---

### T-004: Input sanitization for /chat and /topic
**What:** Cap user input at 500 chars and strip newlines/control chars: `user_message = " ".join(context.args)[:500].replace("\n", " ").strip()`
**Why:** User input is currently passed unsanitized into the LLM prompt — prompt injection vector. Also relevant when the bot is added to public groups.
**Effort:** S
**Priority:** P1
**File:** `interfaces/telegram/handlers.py` — `cmd_chat()` and `cmd_topic()`

---

### T-005: Shallow-copy ctx before asyncio.gather in supervisor
**What:** Pass a shallow copy of `ctx` to `scout.run()` in `_collect_and_score()`.
**Why:** Both `AnalystAgent` and `NarrativeScoutAgent` receive the same `ctx` object reference. Currently safe (different fields), but any future Phase 2 agent that mutates `raw_items` would cause a data race.
**Effort:** S
**Priority:** P1
**File:** `agents/supervisor.py` line 34

---

### T-006: Add bypass_keyword_filter field to DataSource
**What:** Add `bypass_keyword_filter: bool = False` to `DataSource` in `modules/base.py`. Set it `True` on all 3 X sources in `modules/tech/sources.py`. Replace the hardcoded `_KEYWORD_FILTER_BYPASS` set in `data_collector.py` with a check on `source.bypass_keyword_filter`.
**Why:** Adding a new X source (e.g., `X - Crypto Leaders` in Phase 3) requires remembering to update a hardcoded set in the agent — violating the architecture constraint "adding a new source = zero agent changes."
**Effort:** S
**Priority:** P1
**Files:** `modules/base.py`, `modules/tech/sources.py`, `agents/data_collector.py`

---

### T-007: Source health footer in daily report
**What:** When `ctx.errors` is non-empty after pipeline completion, append a small warning footer to the report text listing which sources failed.
**Why:** Source failures are currently invisible to the user. The daily report looks normal but may be running on 3 of 7 sources. Silent data degradation.
**Effort:** S
**Priority:** P1
**File:** `agents/supervisor.py:generate_report()`

---

## Phase 2 — B2C foundation (next PR after develop lands)

### T-008: /thread command — the killer demo feature ✅ DONE
**What:** New prompt in `modules/tech/prompts.py` + new `/thread` command handler in `interfaces/telegram/handlers.py`. Runs the full pipeline and generates a 7-tweet Twitter thread from the top story.
**Why:** This is the first thing a creator will screenshot and share. It transforms Kyvra from "news aggregator" to "content co-pilot." The LLM + pipeline is already there — this is a new prompt + handler.
**Pros:** Viral demo potential. Product story changes from "daily report" to "content creation assistant."
**Cons:** Quality depends on prompt engineering. May need iteration.
**Context:** Moved up from Phase 4. The pipeline already scores + writes — `/thread` is just a different output format from the same top story data. Start with `modules/tech/prompts.py` THREAD_PROMPT constant.
**Effort:** M
**Priority:** P1
**Depends on:** T-001 through T-007 (develop PR landed)
**Completed:** fix/ollama-fallback-and-markdown-parse (2026-03-19)

---

### T-009: /brief command — 3-bullet shareable summary ✅ DONE
**What:** New prompt in `modules/tech/prompts.py` + `/brief` handler. Returns 3 bullet points from today's top stories. Fits in a screenshot.
**Why:** Ultra-short output = maximum shareability. Organic distribution. Also useful as a Slack/group chat format for team use cases.
**Effort:** S
**Priority:** P2
**Depends on:** T-008 (same prompt pattern)
**Completed:** fix/ollama-fallback-and-markdown-parse (2026-03-19)

---

### T-010: User voice profile — /setvoice command ✅ Schema done
**What:** `services/memory.py` now exists with `user_voices` SQLite table (`user_id`, `voice`, `updated_at`). Next: build `/setvoice [description]` handler that saves the user's writing style. Inject the voice profile into all content format prompts (`get_thread_prompt`, `get_newsletter_prompt`, `get_script_prompt`, `get_brief_prompt`) via a new optional `voice: str | None` parameter.
**Why:** The real product differentiation — Kyvra learns *your* voice. A thread from Kyvra should sound like you wrote it, not like generic AI. The SQLite schema is live. This is the next unlock.
**Pros:** Persistent voice = consistent content. Output quality gap vs. raw ChatGPT. Killer demo for B2C.
**Cons:** Prompt injection risk if voice field is not sanitised on write (cap at 300 chars, strip control chars — same pattern as T-004).
**Context:** `services/memory.py` has `save_voice_profile(user_id, voice)` and `get_voice_profile(user_id) -> str | None`. Add `/setvoice` command to `handlers.py`. Load voice in each `generate_*` method in supervisor and append to prompt. `/setvoice` with no args shows current profile.
**Effort:** M
**Priority:** P1

---

### T-011: Signal strength labels (replace raw confidence score in output) ✅ DONE
**What:** In `interfaces/telegram/formatter.py`, replace `Score: 94/100` with a human-readable signal tier label + reason. Example: `🔥 VIRAL — 4 sources, trending 2h` or `📈 RISING — Anthropic official`.
**Why:** Creators don't understand what "94/100" means. A label that explains *why* something is hot builds trust and makes the report feel smarter.
**Context:** The data to compute the label already exists on `ScoredItem`: `confidence_score`, `is_spike`, `cross_source_count`, `authority_score`. Tiers: VIRAL (spike + cross-source), RISING (high score, recent), STEADY (RSS authority), SIGNAL (baseline).
**Effort:** S
**Priority:** P2
**File:** `interfaces/telegram/formatter.py`
**Completed:** fix/ollama-fallback-and-markdown-parse (2026-03-19)

---

### T-012: Daily content angle — add to report prompt ✅ DONE
**What:** Add one instruction to the existing report prompt in `modules/tech/prompts.py` asking for a standalone "Content angle of the day" section at the end.
**Why:** Transforms Kyvra from news aggregator to content strategist. Zero new infrastructure — the LLM is already generating the report, just ask it for a bonus hook for the top story.
**Effort:** S
**Priority:** P2
**File:** `modules/tech/prompts.py`
**Completed:** fix/ollama-fallback-and-markdown-parse (2026-03-19)

---

## Phase 3 — Growth

### T-013: load_module() registry pattern ✅ DONE
Replaced if/elif with a dict registry in `agents/supervisor.py`. Adding a new module now = add one line to the registry dict.

---

### T-014: Module-aware /chat system prompt ✅ DONE
**What:** Pass the active module's system prompt to `chat_with_llm()` from the module itself, not hardcoded to `modules/tech/prompts.CHAT_SYSTEM_PROMPT`.
**Why:** When crypto/vietnam modules are active, the `/chat` command still uses the tech niche system prompt. The coupling in `handlers.py:cmd_chat()` hardcodes the import from `modules.tech.prompts`.
**Context:** `handlers.py` line imports `from modules.tech.prompts import CHAT_SYSTEM_PROMPT`. Should become `ctx.module.get_chat_system_prompt()` — add this method to `BaseModule`.
**Effort:** S
**Priority:** P2
**Depends on:** New modules (Phase 3)
**Completed:** Already implemented — `handlers.py` calls `_get_module().get_chat_system_prompt()`

---

### T-015: asyncio launcher pattern in main.py
**What:** Refactor `main.py` to use an explicit `asyncio.run(main_async())` pattern with `asyncio.gather()` over interface tasks, rather than `Application.run_polling()` blocking the main thread.
**Why:** `python-telegram-bot` and `discord.py` both want to own the event loop. When Discord ships, this refactor is required anyway — doing it now is 15 lines and prevents a structural rewrite.
**Effort:** S
**Priority:** P2
**Depends on:** Discord interface implementation

---

### T-016: Web API authentication pattern
**What:** When `interfaces/web/app.py` (FastAPI) is implemented, all endpoints should require an API key via `Authorization: Bearer <key>` header. Key stored in env var `WEB_API_KEY`.
**Why:** An open pipeline endpoint (even on a personal server) is a rate-limit/abuse risk. The pattern should be planned before first implementation.
**Effort:** S
**Priority:** P3
**Depends on:** `interfaces/web/app.py` implementation

---

### T-017: Usage analytics logging ✅ DONE
**What:** Add structured analytics log lines per command handler: `logger.info(f"[Analytics] user={user_id} command=report module={ACTIVE_MODULE}")`.
**Why:** For B2C product decisions, you need to know which commands users actually use, which topics they search, and how often. Structured logs enable grep-based analysis even without a dashboard.
**Effort:** S
**Priority:** P3
**Completed:** fix/ollama-fallback-and-markdown-parse (2026-03-19)

---

## Phase 4 — B2B / Scale

### T-018: Job queue for concurrent /report requests
**What:** When multiple users send `/report` simultaneously, N pipeline runs execute in parallel — each hitting the same sources. At scale, this means N×7 concurrent API calls to X/GitHub/RSS. An asyncio.Queue with a worker pool (max 2 concurrent pipelines) prevents rate-limit cascades.
**Why:** Not a problem for personal use. Becomes a problem at 50+ concurrent users.
**Effort:** L
**Priority:** P3
**Depends on:** B2C launch with real user load

---

### T-019: Test suite — scoring and dedup unit tests ✅ DONE
**What:** Create `tests/test_analyst.py` and `tests/test_data_collector.py` with unit tests for `score_item()`, `_relevance_score()`, `_engagement_score()` authority floor, and `_dedup_with_cross_source()`.
**Why:** The confidence scoring algorithm is the core business logic. A silent regression (e.g., cross-source boost stops working) would produce worse reports with no visible error.
**Context:** All these functions are pure Python with no I/O — no mocking needed. Start with `pytest` + simple `RawItem` fixtures.
**Effort:** M
**Priority:** P2
**Completed:** fix/ollama-fallback-and-markdown-parse (2026-03-19) — 45 tests, all passing

---

## Phase X — Crypto module follow-ups (post-ship)

### T-020: /module command — switch active module at runtime ✅ DONE
`/module [tech|crypto]` switches the active module instantly, no restart needed.
Clears chat history on switch (stale context). `/module` with no args shows current status.

---

### T-021: Crypto spike threshold tuning
**What:** `X_SPIKE_THRESHOLD = 300` in `modules/crypto/config.py` is a first estimate. After 1 week of real data, tune this based on observed like distributions for CT posts.
**Why:** If set too low, `/breaking` floods with noise. Too high, real spikes are missed.
**Effort:** S
**Priority:** P2
**Context:** Check logs for `is_spike=True` hit rate — target ~1-3 spikes/day in normal market conditions.

---

### T-022: NarrativeScoutAgent crypto topics ✅ DONE
**What:** Add a `CRYPTO_TREND_TOPICS` dict to `agents/narrative_scout.py` (or make topics module-aware via `ctx.module`). Current topics (AI Agents, LLM, OpenAI...) are meaningless for the crypto module.
**Why:** The trend heatmap in crypto reports currently shows tech topics. Crypto needs: Bitcoin, DeFi, Layer 2, Regulation, Stablecoins.
**Effort:** S
**Priority:** P2
**File:** `agents/narrative_scout.py` — pass `ctx.module.name` to select topic set
**Completed:** fix/ollama-fallback-and-markdown-parse (2026-03-19)

---

## Phase 4 — Content personalisation

### T-023: Story rank picker for content format commands
**What:** Add an optional rank argument to `/thread`, `/newsletter`, `/script`. E.g. `/thread 2` generates a thread from the #2 scored story instead of #1. Default remains 1. Cap at 7 (MAX_REPORT_ITEMS).
**Why:** Users often know which story they want to work with — always using #1 removes agency. Power users will hit this immediately.
**Pros:** Tiny change (~10 lines in handlers + supervisor). Big UX improvement for repeat users.
**Cons:** None.
**Context:** `supervisor.generate_thread()` takes no args. Add `rank: int = 1` param. `handlers.py` passes `int(context.args[0]) if context.args else 1`. Clamp to `[1, len(ctx.top_items)]`.
**Effort:** S
**Priority:** P2

---

### T-024: Per-chat-id module mapping in scheduler
**What:** Allow `REPORT_CHAT_IDS` config to map each chat to a preferred module. E.g. `REPORT_CHAT_IDS=123456:tech,789012:indie`. Scheduler sends only that module's report to each chat.
**Why:** Enables a personal chat on `indie` and a group chat on `tech` without running two bot instances.
**Pros:** Multi-tenant feel from a single bot. Zero new infra.
**Cons:** Config format change — needs migration note in deploy docs.
**Context:** Currently `REPORT_CHAT_IDS` is a comma-separated list of ints. Extend to optional `id:module` format, fall back to sending all modules if no module specified.
**Effort:** S
**Priority:** P3

---

### T-026: Story continuity spike-override threshold tuning
**What:** After 1 week of real data, review the spike-override threshold used in the seen-item filter: `likes_per_hour >= x_spike_threshold / 24`. Check logs for "Story continuity floor" warnings (bypass activates too often = threshold too high) and for old stories resurfacing unexpectedly (threshold too low).
**Why:** The initial value (`x_spike_threshold / 24`, e.g. ~21 likes/hr for tech) is a reasonable first estimate but has not been validated against real CT data. Too tight = floor bypasses daily, negating the feature. Too loose = trending stories get suppressed even when genuinely re-viral.
**Pros:** Keeps story continuity useful. Prevents "report of already-seen stories" UX problem.
**Cons:** Requires 7 days of real production data to tune.
**Context:** Filter lives in `agents/data_collector.py`. Log line to watch: `[DataCollectorAgent] Story continuity floor: only N items after seen filter`. Target: floor activates < 1x/week in normal conditions.
**Effort:** S
**Priority:** P2
**Depends on:** 7 days of production data after Phase 1 ships

---

---

## Phase 5 — Kyvra ↔ TrendPost Integration (from CEO review 2026-03-20)

### T-027: Fix PostgresError in TrendPost Kyvra webhook handler
**What:** In TrendPost's `webhooks.routes.ts` (or controller), catch `PostgresError` during `kyvra_stories` insert and return `200 { accepted: false, reason: 'db_error' }` instead of an unhandled 500. Log `ERROR` internally.
**Why:** If TrendPost's DB is temporarily down at 8AM and Kyvra pushes stories, the 500 causes Kyvra to retry 3× aggressively. All retries fail, and the day's stories are silently lost. Returning 200 stops retry spam while leaving an internal log trail.
**Pros:** Graceful DB degradation. Kyvra doesn't retry needlessly. Error is logged and visible.
**Cons:** TrendPost returns 200 even when insertion failed — accepted as trade-off for retry behaviour.
**Context:** `creator-backend/src/routes/webhooks.routes.ts` (new file in integration). Kyvra retries 3× on 5xx. A 200 response stops retries.
**Effort:** XS
**Priority:** P1
**Depends on:** Integration implementation (Kyvra webhook push + TrendPost webhook route)

---

### T-028: Clamp and rate-limit /signal/performance feedback signals
**What:** In Kyvra's new `POST /signal/performance` endpoint (`interfaces/web/app.py`): (1) clamp `delta` to `[-5, +5]`, (2) validate `story_url` exists in DB or return 404, (3) rate-limit to 1 signal per `(user_id, story_url)` per day via a `seen_signals` SQLite table.
**Why:** A buggy TrendPost deploy could send `delta=-100` for every published post, silently destroying source authority scores. The feedback loop must be bounded.
**Pros:** Authority scores remain meaningful. Feedback loop is safe to enable.
**Cons:** Rate-limit table adds minor DB overhead. Clamp means viral posts cap at +5/day.
**Context:** `interfaces/web/app.py` — new `POST /signal/performance` endpoint. `services/memory.py` — add `seen_signals` table: `signal_key TEXT PK, sent_at TEXT`.
**Effort:** S
**Priority:** P1
**Depends on:** Analytics feedback loop integration

---

### T-029: Add kyvra_story_id tracking to TrendPost posts table
**What:** Add optional `kyvra_story_id INTEGER REFERENCES kyvra_stories(id)` column to TrendPost's `schedules` (or posts) table. Populate when user generates content from Kyvra Feed Tab. Use in `processScheduledPosts()` to emit performance signal to Kyvra after successful publish.
**Why:** The analytics feedback loop needs to know which Kyvra story a post was generated from. Without this FK, performance signals can't be attributed to sources.
**Pros:** Enables the full feedback loop. Source authority improves over time based on real publishing outcomes.
**Cons:** DB migration required. `kyvra_story_id` is null for non-Kyvra posts.
**Context:** `creator-backend/src/migrations/` — add column. `creator-backend/src/services/schedule.service.ts` — after publish, if `kyvra_story_id` non-null, call `kyvraClient.sendPerformanceSignal()`.
**Effort:** S
**Priority:** P2
**Depends on:** T-028 (signal endpoint must be safe before enabling feedback)

---

### T-025: /setvoice — user voice profile injection ✅ DONE
**What:** `/setvoice [description]` saves the user's writing style to `user_voices` SQLite table (schema already live in `services/memory.py`). Voice profile is injected into all content format prompts. `/setvoice` with no args shows current profile. `/setvoice clear` resets it.
**Why:** This is the core product differentiator. Output from `/thread`, `/newsletter`, `/script` should sound like *the user wrote it*, not generic AI. A creator who sets their voice gets dramatically better, shareable content.
**Pros:** Persistent voice = consistent brand. Zero extra API cost. Immediate perceived quality jump.
**Cons:** Prompt injection risk — cap voice at 300 chars, strip newlines/control chars on save (same pattern as T-004). Voice prompt adds ~50 tokens to each content format call.
**Context:** `services/memory.py` exposes `save_voice_profile(user_id, voice)` and `get_voice_profile(user_id)`. Add `/setvoice` handler in `handlers.py`. In `supervisor.generate_thread/newsletter/script/brief`, load voice via `get_voice_profile(user_id)` and append to each module's prompt method (add optional `voice: str | None` param).
**Effort:** M
**Priority:** P1
**Depends on:** T-010 schema (done)
