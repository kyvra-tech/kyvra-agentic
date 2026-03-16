# Kyvra — Project Roadmap

## Phase 0 — Foundation `[done]`
- Multi-agent pipeline: Collector → Analyst → Scout → Writer
- X as primary source (AI Leaders, AI Trending, Indie Dev queries)
- HN + GitHub + official RSS as supplementary
- Confidence Score: engagement + authority + recency + relevance + cross-source boost
- Daily 8AM report + `/report` `/chat` `/help` Telegram commands
- Modular architecture (`BaseModule`) — 1 folder per niche

---

## Phase 1 — Signal Quality `[next]`
**Goal:** make the Analyst smarter without LLM cost.

| Task | Why |
|---|---|
| Velocity signal: `likes_per_hour` for X | A 2h-old tweet with 300 likes outranks a 6h-old tweet with 500 — raw count misses momentum |
| Story continuity: detect if a story appeared yesterday | Recurring coverage = growing trend, not a one-day spike |
| Source health check on startup | Log which sources returned 0 items so silent failures are visible |
| `/status` command | Shows last run time, items fetched per source, top confidence score |

---

## Phase 2 — More Sources `[Q2]`
**Goal:** cover the full surface area of where creators find ideas.

```
modules/tech/sources.py additions:
  - Reddit       → r/MachineLearning, r/LocalLLaMA, r/SideProject  (RSS)
  - Product Hunt → daily top launches  (official API)
  - YouTube      → top AI/tech videos by views delta  (scrape)
  - TLDR Tech    → newsletter aggregators  (RSS)
```

Each source gets its own authority score and engagement normalization in `AnalystAgent`.

---

## Phase 3 — New Modules `[Q2–Q3]`
**Goal:** plug-and-play niches by adding one folder.

```
modules/
  tech/       ← current
  crypto/     ← on-chain activity + CT (Crypto Twitter) + CoinDesk RSS
  vietnam/    ← VnExpress Tech, CafeF, ICTNews — Vietnamese-first news
  indie/      ← Product Hunt + IndieHackers + r/SideProject + Maker Log
```

Each module owns `sources.py`, `config.py`, `prompts.py`. Zero changes to agent code.
Users switch via `/module crypto` command.

---

## Phase 4 — Creator Output Formats `[Q3]`
**Goal:** go from "here's the news" to "here's the content, ready to post."

| Command | Output |
|---|---|
| `/thread` | Twitter/X thread (hook + 5–7 tweets + CTA), ready to copy-paste |
| `/newsletter` | Markdown newsletter section for that day's top story |
| `/script` | TikTok/Reels voiceover script (60–90 sec) |
| `/brief` | Ultra-short Slack/group chat summary (3 bullets) |

These are new prompts in `modules/tech/prompts.py`, routed by `ContentWriterAgent`.

---

## Phase 5 — Memory & Personalization `[Q4]`
**Goal:** the bot remembers what you care about and stops repeating itself.

```
services/
  memory.py   ← SQLite: past report items (title, url, date, user_feedback)
```

- **Seen-item suppression**: skip stories already reported in the last 7 days unless they spike again
- **User feedback**: `/good` `/bad` after a report adjusts source weights per user
- **Topic subscriptions**: `/subscribe AI Agents` → user only gets reports matching those topics
- **Report history**: `/archive 2026-03-15` → retrieve a past report

---

## Phase 6 — Autonomous Agent Mode `[Q4+]`
**Goal:** the bot proactively alerts without waiting for 8AM.

- **Breaking news alert**: if an X spike (>5k likes) is detected from a top account → immediate push, skip the daily queue
- **Multi-report per day**: morning briefing (8AM) + evening digest (8PM) with different angle
- **Headless mode**: `python main.py --once` for CI/CD or n8n integration — runs pipeline once, outputs JSON, exits

---

## Architecture Constraints

```
Rule 1: Adding a new niche  = new folder under /modules/,       zero agent changes
Rule 2: Adding a new source = new DataSource + fetcher,          zero agent changes
Rule 3: LLM is called only in ContentWriterAgent (and /chat) — Analyst stays pure Python
Rule 4: Each agent has one job: Collector collects, Analyst scores, Scout patterns, Writer writes
```
