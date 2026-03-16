# Kyvra — Business Overview

## What is Kyvra?

Kyvra is an AI-powered content intelligence agent built for tech creators — indie developers, newsletter writers, Twitter/X content creators, and startup founders who need to stay on top of the fast-moving Tech and AI landscape.

Every morning, Kyvra automatically monitors the internet's most important tech signals — viral tweets, trending GitHub projects, breaking AI announcements — then distills them into a concise, actionable daily briefing delivered straight to Telegram. Each insight comes with a ready-to-use content angle: a thread hook, a newsletter intro, or a TikTok script idea.

---

## The Problem

Tech creators face a daily attention tax:
- The AI and startup news cycle moves faster than any human can manually track
- Relevant signals are scattered across X/Twitter, Hacker News, GitHub, and a dozen official blogs
- Most news aggregators surface noise — Kyvra surfaces *momentum*
- Writing daily content from scratch is time-consuming, even for experienced creators

The result: creators either miss breaking stories or spend 1–2 hours every morning just researching what to post about.

---

## The Solution

Kyvra replaces the manual morning research workflow with a fully automated pipeline:

| Without Kyvra | With Kyvra |
|---|---|
| 60–90 min daily research | 0 min — delivered at 8 AM |
| Manually checking 5–10 sources | 8+ sources monitored automatically |
| Miss viral stories if you're offline | Spike alerts sent in real time via `/breaking` |
| Blank page when writing content | Every story comes with a content angle |
| One-size-fits-all news | Filter by topic with `/topic openai` |

---

## How It Works (Non-Technical)

```
Morning (8 AM GMT+7) — or on demand:

1. COLLECT   Kyvra scans X/Twitter (AI leaders & trending), Hacker News,
             GitHub Trending, Anthropic, OpenAI, and DeepMind blogs

2. SCORE     Each story gets a Confidence Score (0–100) based on:
             how viral it is, how authoritative the source is,
             how recent it is, and how many sources covered it

3. SPOT      Kyvra detects which stories are genuine spikes —
             unusually high engagement that signals a breaking moment

4. WRITE     The top 7 stories are sent to an AI (Grok) which writes
             a polished briefing with a content angle for each story

5. DELIVER   The report lands in your Telegram in under 60 seconds
```

---

## Key Features

### Daily Morning Report (`/report`)
A full AI-written briefing of the day's top 7 stories, each with:
- A plain-English summary
- Confidence score (how trending/important it is)
- A suggested content angle (thread, TikTok, newsletter)
- Trend heatmap showing which topics are dominating the day

### Fast Scan (`/update`)
Top-scored stories delivered in ~10 seconds, no AI writing. For creators who want the raw data quickly.

### Breaking Alerts (`/breaking`)
Only the stories with unusually high engagement — the ones worth posting about *right now*.

### Topic Deep Dive (`/topic [keyword]`)
A full report scoped to a single topic. Example: `/topic openai` generates a report covering only OpenAI-related stories that day.

### AI Chat (`/chat`)
Ask anything about today's tech news in plain English. Examples:
- *"What's the most important AI story today?"*
- *"Write me a Twitter thread about the top GitHub project right now"*
- *"Summarize what Anthropic announced this week"*

---

## Target Users

| User | How they use Kyvra |
|---|---|
| **Tech Twitter creators** | Morning `/report` → turn top angles into threads |
| **Newsletter writers** | `/report` as a first draft, `/topic` for deep dives |
| **Indie developers** | `/breaking` + `/topic indie` to track the maker ecosystem |
| **Startup founders** | Daily briefing to stay informed on competitors and AI tools |
| **Content agencies** | White-label the pipeline for client niches |

---

## Confidence Score — How Kyvra Ranks Stories

Not all news is equal. Kyvra scores every story on four signals:

| Signal | What it measures |
|---|---|
| **Engagement** | How much attention it's getting right now (likes, upvotes, stars) |
| **Source authority** | How credible the source is (Anthropic blog > random tweet) |
| **Recency** | How fresh the story is (6-hour-old news scores higher than 2-day-old) |
| **Cross-source coverage** | Stories covered by multiple sources are independently validated as important |

A score of 80+ means the story is genuinely trending and worth covering. A score of 50–70 is solid context. Under 50 rarely makes the top 7.

---

## Data Sources (Phase 0 — Tech Module)

All sources are free and publicly accessible:

| Source | What it provides |
|---|---|
| **X/Twitter — AI Leaders** | Announcements and commentary from top AI accounts |
| **X/Twitter — AI Trending** | Viral AI/tech tweets across the platform |
| **X/Twitter — Indie Dev** | Indie maker launches and discussions |
| **Hacker News** | Developer community's most upvoted tech stories |
| **GitHub Trending** | Open source projects gaining the most stars today |
| **Anthropic Blog** | Claude model releases and research |
| **OpenAI Blog** | GPT/API product launches |
| **Google DeepMind Blog** | Gemini updates and AI research |

---

## Roadmap

### Phase 1 — Signal Quality (Next)
Make the scoring engine smarter: detect story momentum (velocity), recognize recurring stories as growing trends, and add a `/status` command showing pipeline health.

### Phase 2 — More Sources (Q2)
Add Reddit (r/MachineLearning, r/LocalLLaMA, r/SideProject), Product Hunt daily launches, and TLDR Tech newsletter aggregation.

### Phase 3 — New Modules (Q2–Q3)
Plug-and-play modules for new niches:
- **Crypto** — on-chain signals, Crypto Twitter, CoinDesk RSS
- **Vietnam** — VnExpress Tech, CafeF, ICTNews (Vietnamese-first)
- **Indie** — Product Hunt, IndieHackers, r/SideProject, Maker Log

### Phase 4 — Creator Output Formats (Q3)
Go beyond "here's the news" to "here's the content, ready to post":
- `/thread` — full Twitter/X thread ready to copy-paste
- `/newsletter` — Markdown newsletter section
- `/script` — TikTok/Reels voiceover script (60–90 sec)
- `/brief` — 3-bullet Slack/group chat summary

### Phase 5 — Memory & Personalization (Q4)
- Suppress stories the user has already seen
- Learn topic preferences from user feedback
- Topic subscriptions: `/subscribe AI Agents`
- Report archive: `/archive 2026-03-15`

### Phase 6 — Autonomous Agent Mode (Q4+)
- Proactive breaking news push alerts (no waiting for 8 AM)
- Morning briefing + evening digest
- Headless API mode for n8n and no-code integrations

---

## Business Model (Planned)

| Tier | Target | Features |
|---|---|---|
| **Free** | Individual creators | 1 module, daily report, standard commands |
| **Pro** | Power users & newsletters | All modules, `/thread` `/script` `/newsletter`, topic subscriptions, report archive |
| **Agency / White-label** | Content agencies, SaaS tools | Custom module per niche, branded output, API access, multi-user |

---

## Why Kyvra vs. Alternatives

| | Kyvra | Generic news apps | Manual research | Other bots |
|---|---|---|---|---|
| Auto-delivered to Telegram | ✅ | ❌ | ❌ | Varies |
| Content angles included | ✅ | ❌ | ❌ | ❌ |
| Spike / breaking detection | ✅ | ❌ | ❌ | ❌ |
| Niche-specific scoring | ✅ | ❌ | ❌ | ❌ |
| Topic filter on demand | ✅ | Limited | ❌ | ❌ |
| AI chat about today's news | ✅ | ❌ | ❌ | ❌ |
| Free to run | ✅ | Varies | ✅ | Varies |
