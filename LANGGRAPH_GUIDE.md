# LangGraph & Multi-Agent Orchestration — Complete Learning Guide

This guide explains every phase of the Kyvra LangGraph migration from first principles.
It is written so you can **learn LangGraph concepts** by reading the actual code we built.

---

## Table of Contents

1. [Why LangGraph? The Problem We Solved](#1-why-langgraph-the-problem-we-solved)
2. [Core Concepts — Read This First](#2-core-concepts--read-this-first)
3. [Phase 0 — Dependencies](#3-phase-0--dependencies)
4. [Phase 1 — State Layer (`agents/state.py`)](#4-phase-1--state-layer)
5. [Phase 2 — Nodes (`agents/nodes/`)](#5-phase-2--nodes)
6. [Phase 3 — The Graph (`agents/graph.py`)](#6-phase-3--the-graph)
7. [Phase 4 — LLM Provider Abstraction (`services/llm_provider.py`)](#7-phase-4--llm-provider-abstraction)
8. [Phase 5 — Graph Runner & Interface Wiring](#8-phase-5--graph-runner--interface-wiring)
9. [Phase 6 — Streaming Progress](#9-phase-6--streaming-progress)
10. [How Everything Connects — The Full Data Flow](#10-how-everything-connects--the-full-data-flow)
11. [Mental Models & Common Mistakes](#11-mental-models--common-mistakes)
12. [What to Learn Next](#12-what-to-learn-next)

---

## 1. Why LangGraph? The Problem We Solved

### The old system (before LangGraph)

Before this migration, Kyvra used a hand-written `SupervisorAgent` class in
`agents/supervisor.py`. Here is exactly what it did (simplified):

```python
class SupervisorAgent:
    async def generate_report(self):
        ctx = PipelineContext(module=self.module)   # 1. create a context object

        ctx = await self.collector.run(ctx)          # 2. fetch news
        
        # 3. run analyst and scout in parallel (manual asyncio trick)
        analyst_ctx, scout_ctx = await asyncio.gather(
            self.analyst.run(copy.copy(ctx)),
            self.scout.run(copy.copy(ctx)),
        )
        ctx.scored_items  = analyst_ctx.scored_items
        ctx.top_items     = analyst_ctx.top_items
        ctx.trend_heatmap = scout_ctx.trend_heatmap

        ctx = await self.writer.run(ctx)             # 4. write report with LLM

        memory.mark_seen(...)                        # 5. record what was shown
        return ctx.report_text
```

**What is wrong with this?**

| Problem | Why it hurts |
|---|---|
| The "graph" is invisible — it only exists as sequential Python calls | You can't see the structure; you have to read all the code to understand the flow |
| Parallelism is a manual hack (`copy.copy(ctx)` + `asyncio.gather`) | Easy to make mistakes, hard to add more parallel steps |
| Routing is buried in `if/else` blocks | No way to see all the paths the code can take |
| No streaming — caller waits until everything is done | Telegram users see a frozen "please wait" with no feedback |
| No checkpointing — if the bot restarts mid-pipeline, state is lost | Chat history evaporates on every deploy |

### What LangGraph gives us

LangGraph makes the **structure explicit**:

```
START → collect → [analyst ∥ scout] → join → writer → publisher → END
                       ↑                  ↑
                 parallel nodes      fan-in (wait for both)
```

Every decision point (conditional edges), every parallel branch, every node is
**declared in code** and **visible as a graph**. The orchestration is not hidden
inside a class — it IS the class.

---

## 2. Core Concepts — Read This First

Before looking at any Kyvra code, understand these 5 LangGraph primitives.
Everything else builds on them.

### 2.1 State

State is a **typed dictionary** that flows through the entire graph.
Every node reads from it and returns a dict of **only the keys it changed**.
LangGraph merges those changes into the running state automatically.

```python
from typing_extensions import TypedDict

class MyState(TypedDict):
    name: str
    count: int
    result: str
```

**Key insight:** State is like a shared whiteboard. Nodes write on it; other
nodes read from it. No node needs to know about any other node — they just
read what they need and write what they produce.

### 2.2 Nodes

A node is any `async def` function that takes state and returns a dict:

```python
async def my_node(state: MyState) -> dict:
    # read from state
    current_count = state["count"]

    # do work
    new_count = current_count + 1

    # return ONLY the keys you changed
    return {"count": new_count}
```

**Key insight:** The function returns `{"count": new_count}`, NOT the full
state object. LangGraph merges this partial update into the full state
automatically. Other keys are untouched.

### 2.3 Edges

Edges connect nodes. There are two types:

```python
# Unconditional: A always goes to B
graph.add_edge("A", "B")

# Conditional: the router function decides which node runs next
def my_router(state: MyState) -> str:
    if state["count"] > 10:
        return "done"      # maps to END
    return "keep_going"    # maps to "A" (runs A again)

graph.add_conditional_edges("A", my_router, {
    "done":       END,
    "keep_going": "A",
})
```

**Key insight:** Conditional edges are how you implement `if/else` routing in
a graph. The router function returns a **string key**, and the mapping dict
translates that key to the next node name. This makes all routing decisions
visible in one place.

### 2.4 The Graph Builder

```python
from langgraph.graph import StateGraph, START, END

g = StateGraph(MyState)        # create the graph, tell it the state type

g.add_node("A", node_a)        # register nodes
g.add_node("B", node_b)

g.add_edge(START, "A")         # START is a special source node
g.add_edge("A", "B")
g.add_edge("B", END)           # END is a special sink node

app = g.compile()              # compile = validate + optimize the graph
```

After `compile()` you get a `CompiledGraph` object. Call it with:
- `await app.ainvoke(initial_state)` → run to completion, return final state
- `async for event in app.astream(initial_state)` → stream one event per node

### 2.5 Parallel Execution

LangGraph automatically runs nodes **in parallel** when:
1. Multiple nodes have an edge from the same source
2. Those nodes have no dependency on each other

```python
# After "collect" completes, LangGraph runs "analyst" and "scout" at the same time
g.add_edge("collect", "analyst")
g.add_edge("collect", "scout")

# "join" only starts after BOTH "analyst" AND "scout" have finished
g.add_edge("analyst", "join")
g.add_edge("scout",   "join")
```

This is the **fan-out / fan-in** pattern. No `asyncio.gather` needed —
LangGraph handles it.

---

## 3. Phase 0 — Dependencies

**File:** `requirements.txt`

```
langgraph>=0.2.0
langgraph-checkpoint-sqlite>=0.1.0
anthropic>=0.25.0
```

**What each package does:**

| Package | Purpose |
|---|---|
| `langgraph` | The graph engine: StateGraph, nodes, edges, conditional routing, streaming |
| `langgraph-checkpoint-sqlite` | Persistence layer: saves graph state to SQLite so runs can be resumed after crashes. Used in Phase 7 (human-in-the-loop) |
| `anthropic` | Anthropic Claude SDK — used by `ClaudeProvider` in Phase 4 |

**Verify the install:**
```bash
python -c "from langgraph.graph import StateGraph, START, END; print('OK')"
```

---

## 4. Phase 1 — State Layer

**File:** `agents/state.py`

### What we built

```python
from typing_extensions import TypedDict
from typing import Optional, Any

class KyvraState(TypedDict, total=False):
    # --- Set by caller before invoking the graph ---
    module_name: str          # "tech", "crypto", "vietnam", ...
    mode: str                 # "full" | "quick" | "topic" | "breaking"
    topic_filter: Optional[str]
    content_format: str       # "report" | "thread" | "brief" | ...
    content_rank: int

    # --- Written by collect_node ---
    raw_items: list[Any]

    # --- Written by analyst_node ---
    scored_items: list[Any]
    top_items: list[Any]

    # --- Written by scout_node ---
    trend_heatmap: str

    # --- Written by writer_node ---
    report_text: str

    # --- Written by publisher_node ---
    published: bool

    # --- Accumulated by any node ---
    errors: list[str]
```

### What `total=False` means

In Python's `TypedDict`, `total=False` means **all keys are optional** — no
key is required to be present. This matters because LangGraph builds up the
state incrementally: `raw_items` only exists after `collect_node` runs, so it
should not be required at graph start.

### The `empty_state()` factory

```python
def empty_state(module_name: str, mode: str = "full", ...) -> KyvraState:
    return KyvraState(
        module_name=module_name,
        mode=mode,
        raw_items=[],
        scored_items=[],
        ...
    )
```

This is the **initialiser** — you call it to create a fresh, fully-populated
state before passing it to `graph.ainvoke()`. It ensures every key has a
sensible default so nodes don't have to guard against `KeyError`.

### Before vs. After

**Before (PipelineContext):**
```python
@dataclass
class PipelineContext:
    module: BaseModule      # a live object — hard to serialise
    raw_items: list[RawItem] = field(default_factory=list)
    ...
```

**After (KyvraState):**
```python
class KyvraState(TypedDict, total=False):
    module_name: str        # just the name — the object is loaded inside each node
    raw_items: list[Any]
    ...
```

The key difference: `KyvraState` stores `module_name` (a string) not a live
`BaseModule` object. Why? Because LangGraph needs to be able to **serialise**
state to JSON (for checkpointing). A live Python object can't be serialised.
Each node loads the module from the name using `load_module(state["module_name"])`.

---

## 5. Phase 2 — Nodes

**Directory:** `agents/nodes/`

### The node contract

Every LangGraph node is an `async def` function with this exact signature:

```python
async def run(state: KyvraState) -> dict:
    # 1. Read what you need from state
    # 2. Do your work
    # 3. Return ONLY the keys you changed
    return {"key_i_changed": new_value}
```

**This is the most important thing to understand about nodes:**
- You return a `dict`, NOT the full state
- LangGraph merges your `dict` into the running state
- Keys you don't return are left unchanged

### Node 1: `collect.py` — Fetching news

```python
async def run(state: KyvraState) -> dict:
    module_name = state["module_name"]
    module = load_module(module_name)        # load the active module
    errors = list(state.get("errors") or [])

    # Fetch all sources in parallel (asyncio.gather)
    results = await asyncio.gather(
        *[fetch_source(src) for src in module.get_sources()],
        return_exceptions=True,              # don't crash if one source fails
    )

    # Filter, dedup, story continuity...
    deduped = _dedup_with_cross_source(filtered)

    return {"raw_items": deduped, "errors": errors}
    #        ↑ only the keys this node owns
```

**Teaching point:** Notice `return_exceptions=True` in `asyncio.gather`. This
means if one news source times out, the gather doesn't crash — it returns the
exception as a value, and the `for` loop handles it gracefully. This pattern
is essential for resilient data collection.

**What `_dedup_with_cross_source` does:**

```
Input:  20 items (some are the same story from different sources)
            ↓
Step 1: Group by exact URL
Step 2: Within each URL group, group by title prefix (first 60 chars)
Step 3: Pick the item with the highest authority score as representative
Step 4: Record how many sources covered this story (cross_source_count)
            ↓
Output: 10 unique items, each knowing how many sources covered it
```

A story covered by 3 sources gets a `cross_source_count=3`, which later gives
it a `+10` boost in the analyst's confidence score.

### Node 2: `analyst.py` — Scoring stories

```python
async def run(state: KyvraState) -> dict:
    raw_items = state.get("raw_items") or []
    module = load_module(state["module_name"])

    scored = sorted(
        [score_item(item, keywords, ...) for item in raw_items],
        key=lambda x: (x.is_spike, x.confidence_score),
        reverse=True,
    )

    return {
        "scored_items": scored[:14],   # top 14
        "top_items":    scored[:7],    # top 7 for LLM
    }
```

**The scoring formula** (0–100 points):

```
confidence = engagement   (0–40)   ← likes, GitHub stars, RSS baseline
           + authority    (0–20)   ← how trusted is this source?
           + recency      (0–20)   ← <6h=20, <24h=13, <48h=6, older=0
           + relevance    (10–20)  ← how many module keywords matched?
           + cross_boost  (0–10)   ← +10 if 2+ sources covered this story
           + velocity     (0–10)   ← X tweets: likes per hour (momentum)
```

**Teaching point:** This node is **pure Python** — no LLM call, no network
call. It's just math. LangGraph lets it run in parallel with `scout_node`
because both only *read* `raw_items` and write to different keys. No conflict
is possible.

### Node 3: `scout.py` — Trend heatmap

```python
async def run(state: KyvraState) -> dict:
    raw_items = state.get("raw_items") or []

    counts: Counter = Counter()
    for item in raw_items:
        text = (item.title + " " + item.summary).lower()
        for topic, keywords in topics.items():
            if any(kw in text for kw in keywords):
                counts[topic] += 1

    top = counts.most_common(4)
    heatmap = " | ".join(f"{topic} {_heat(n)}" for topic, n in top if n > 0)

    return {"trend_heatmap": heatmap}
    # e.g. → "AI Agents 🔥 | LLM 📈 | OpenAI 🟡"
```

**Teaching point:** This node runs **in parallel with analyst_node**. Both
start as soon as `collect_node` finishes. They cannot conflict because:
- `analyst_node` writes to `scored_items` and `top_items`
- `scout_node` writes to `trend_heatmap`

These are **different keys**. LangGraph safely merges both dicts into state.

### Node 4: `writer.py` — LLM content generation

```python
async def run(state: KyvraState) -> dict:
    top_items = state.get("top_items") or []
    fmt = state.get("content_format") or "report"

    if not top_items:
        return {"report_text": "No scored items today. Try again later! 🤷"}

    # Build enriched payload (items + heatmap)
    enriched = [{**_item_dict(item), "trend_heatmap": trend_heatmap}
                for item in top_items]

    # Choose the right prompt based on content_format
    if fmt == "report":
        prompt = module.get_report_prompt(enriched)
    elif fmt == "thread":
        prompt = module.get_thread_prompt(selected)
    # ...

    # Call LLM via provider abstraction (Phase 4)
    from services.llm_provider import get_content_provider
    text = await get_content_provider().complete(prompt, max_tokens=max_tokens)

    return {"report_text": text, "errors": errors}
```

**Teaching point:** This is the only node that makes an LLM call. It reads
`top_items` (written by analyst) AND `trend_heatmap` (written by scout). This
is why it must run **after** both analyst and scout finish — the `join` node
acts as the barrier.

### Node 5: `publisher.py` — Mark seen + push webhook

```python
async def run(state: KyvraState) -> dict:
    top_items = state.get("top_items") or []
    module_name = state["module_name"]

    # Story continuity: record URLs so they don't appear in tomorrow's report
    if top_items:
        memory.mark_seen([i.url for i in top_items], module_name)

    # Push to TrendPost (optional — skipped if env vars not set)
    if TRENDPOST_WEBHOOK_URL and TRENDPOST_WEBHOOK_SECRET and top_items:
        payload = {"stories": [...], "module": module_name, ...}
        body = json.dumps(payload).encode()
        sig = "sha256=" + hmac.new(secret, body, hashlib.sha256).hexdigest()
        async with httpx.AsyncClient() as client:
            await client.post(TRENDPOST_WEBHOOK_URL, content=body, headers={...})

    return {"published": True}
```

**Teaching point:** This node is the "side effect" node. It writes to external
systems (SQLite, TrendPost webhook). It runs **after** the writer node so it
only marks stories as "seen" when they were actually included in a report.

### Node 6: `router.py` — Conditional routing

```python
def after_collect(state: KyvraState) -> str:
    if not state.get("raw_items"):
        return "empty"   # → END (no items, skip everything)
    return "score"        # → analyst node (normal flow)

def after_parallel(state: KyvraState) -> str:
    mode = state.get("mode") or "full"
    if mode in ("quick", "breaking"):
        return "quick_end"  # → END (no LLM needed)
    return "write"           # → writer node
```

**Teaching point:** Router functions are **plain Python functions**, not async.
They inspect state and return a string. The string is a key that LangGraph
looks up in the mapping dict you provided in `add_conditional_edges()`.

---

## 6. Phase 3 — The Graph

**File:** `agents/graph.py`

This is where all the nodes are wired together into a compiled graph.

```python
from langgraph.graph import StateGraph, START, END
from agents.state import KyvraState
from agents.nodes import collect, analyst, scout, writer, publisher, router

async def _parallel_join(state: KyvraState) -> dict:
    """Fan-in node: does nothing, just waits for analyst + scout."""
    return {}

def build_graph(checkpointer=None):
    g = StateGraph(KyvraState)

    # 1. Register all nodes
    g.add_node("collect",   collect.run)
    g.add_node("analyst",   analyst.run)
    g.add_node("scout",     scout.run)
    g.add_node("join",      _parallel_join)   # ← fan-in barrier
    g.add_node("writer",    writer.run)
    g.add_node("publisher", publisher.run)

    # 2. Wire edges
    g.add_edge(START, "collect")

    # After collect: empty → END, else → analyst AND scout (parallel)
    g.add_conditional_edges("collect", router.after_collect, {
        "empty": END,
        "score": "analyst",
    })
    g.add_edge("collect", "scout")            # fan-out: scout starts in parallel

    # Analyst and scout both flow into join (fan-in)
    g.add_edge("analyst", "join")
    g.add_edge("scout",   "join")

    # After join: quick/breaking → END, full/topic → writer
    g.add_conditional_edges("join", router.after_parallel, {
        "quick_end": END,
        "write":     "writer",
    })

    # Writer → publisher → END (always)
    g.add_edge("writer",    "publisher")
    g.add_edge("publisher", END)

    return g.compile(checkpointer=checkpointer)

kyvra_graph = build_graph()    # module-level singleton
```

### Understanding the fan-out / fan-in pattern

```
collect
  │
  ├──────────────┐
  ↓              ↓
analyst        scout     ← both start immediately when collect finishes
  │              │
  └──────┬───────┘
         ↓
        join             ← only starts when BOTH analyst AND scout have finished
         │
       [route]
         │
       writer
```

The `join` node is a **dummy node** that does nothing (`return {}`). Its sole
purpose is to be a meeting point: LangGraph will not call `join` until all
its upstream nodes have finished. This is the fan-in barrier.

### The `_parallel_join` trick explained

Why do we need a dummy node at all? Because `add_conditional_edges` attaches
to a single source node. We need ONE node to be the decision point after both
analyst and scout finish. The dummy join node provides that single point.

```
Without join (wrong):
  analyst → conditional_edge
  scout   → conditional_edge    ← which one fires first? race condition

With join (correct):
  analyst → join
  scout   → join
  join    → conditional_edge    ← fires exactly once, after both finish
```

### Compiled graph edges (from our verification)

```
__start__ → collect          (unconditional)
collect   → __end__          (conditional: "empty")
collect   → analyst          (conditional: "score")
collect   → scout            (unconditional — parallel fan-out)
analyst   → join             (unconditional)
scout     → join             (unconditional)
join      → __end__          (conditional: "quick_end")
join      → writer           (conditional: "write")
writer    → publisher        (unconditional)
publisher → __end__          (unconditional)
```

### The `kyvra_graph` singleton

```python
kyvra_graph = build_graph()   # called once at module import time
```

This compiled graph is imported by `GraphRunner` and used for every request.
It is stateless — the same graph object handles all concurrent requests safely
because each `ainvoke()` call gets its own fresh state dict.

---

## 7. Phase 4 — LLM Provider Abstraction

**File:** `services/llm_provider.py`

### The problem

Before this phase, `writer_node` had this hardcoded:

```python
import services.llm as llm
text = await llm.complete(prompt, max_tokens=2000)
```

If you wanted to switch from DeepSeek to Claude, you had to edit `writer.py`.
That's a code change for a configuration decision.

### The solution: Strategy Pattern

The Strategy pattern says: define an interface, then swap implementations
via configuration. Here's the whole abstraction:

```python
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    """The interface — all providers must implement these two methods."""

    @abstractmethod
    async def complete(self, prompt: str, max_tokens: int = 2000) -> str: ...

    @abstractmethod
    async def chat(self, messages: list[dict], max_tokens: int = 1000) -> str: ...
```

Three implementations:

```python
class DeepSeekProvider(LLMProvider):
    """Uses DeepSeek API (OpenAI-compatible)."""
    async def complete(self, prompt, max_tokens=2000):
        response = await self._client.chat.completions.create(
            model=self._model, messages=[{"role": "user", "content": prompt}], ...
        )
        return response.choices[0].message.content

class OllamaProvider(LLMProvider):
    """Uses local Ollama server — same OpenAI wire protocol, different URL."""
    async def complete(self, prompt, max_tokens=2000):
        # Ollama exposes /v1/chat/completions — same AsyncOpenAI client works!
        response = await self._client.chat.completions.create(...)
        return response.choices[0].message.content

class ClaudeProvider(LLMProvider):
    """Uses Anthropic Claude — different SDK, different message format."""
    async def complete(self, prompt, max_tokens=2000):
        message = await self._client.messages.create(
            model=self._model, max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text
```

The factory selects which one to use:

```python
def get_content_provider() -> LLMProvider:
    name = os.getenv("CONTENT_LLM_PROVIDER", "deepseek")   # read from .env
    return get_provider(name)
```

### Switching providers

Change ONE line in your `.env` file:

```bash
# Use local Ollama (free, no API key)
CONTENT_LLM_PROVIDER=ollama

# Use DeepSeek (cheap API)
CONTENT_LLM_PROVIDER=deepseek

# Use Claude (most capable)
CONTENT_LLM_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-...
```

No code changes. This is what the Strategy pattern achieves.

### Why Ollama uses the OpenAI SDK

Ollama exposes an OpenAI-compatible REST API at `/v1/chat/completions`.
The `AsyncOpenAI` client just sends HTTP — it doesn't care if the server
is OpenAI, DeepSeek, or Ollama. We just point `base_url` at Ollama:

```python
self._client = AsyncOpenAI(
    api_key="ollama",                         # Ollama ignores the key
    base_url=f"{OLLAMA_BASE_URL}/v1",         # http://localhost:11434/v1
)
```

### Why Claude needs a different approach

Anthropic's SDK does NOT use the OpenAI wire protocol. It has its own:
- Different endpoint (`/v1/messages` not `/v1/chat/completions`)
- Different request format (system prompt is a separate field)
- Different response structure (`message.content[0].text` not `choices[0].message.content`)

`ClaudeProvider.chat()` handles this by extracting the system message:

```python
async def chat(self, messages, max_tokens=1000):
    system = ""
    user_messages = []
    for m in messages:
        if m["role"] == "system":
            system = m["content"]   # Anthropic requires system as a separate field
        else:
            user_messages.append(m)

    kwargs = {"model": ..., "messages": user_messages}
    if system:
        kwargs["system"] = system   # only add if present
    ...
```

---

## 8. Phase 5 — Graph Runner & Interface Wiring

**Files:** `agents/graph_runner.py`, `interfaces/telegram/handlers.py`, `interfaces/web/app.py`

### The Adapter Pattern

`handlers.py` and `web/app.py` were written to call `SupervisorAgent` methods
like `.generate_report_with_ctx()`, `.quick_scan()`, `.generate_thread()`, etc.

We did NOT want to rewrite all 15 Telegram commands at once. Instead, we built
a **GraphRunner** that presents the same API as SupervisorAgent but routes
everything through `kyvra_graph` internally:

```
Before:
  handlers.py  →  SupervisorAgent  →  manual asyncio pipeline

After:
  handlers.py  →  GraphRunner  →  kyvra_graph  →  LangGraph nodes
```

The interface (`handlers.py`) sees no difference. The orchestration underneath
changed completely.

### GraphRunner core

```python
class GraphRunner:
    def __init__(self, module_name: str) -> None:
        self.module_name = module_name
        self._module = load_module(module_name)

    async def _run(self, mode, topic_filter=None, content_format="report", content_rank=1):
        """The core: build initial state, invoke graph, return final state."""
        initial = empty_state(
            module_name=self.module_name,
            mode=mode,
            topic_filter=topic_filter,
            content_format=content_format,
            content_rank=content_rank,
        )
        result: KyvraState = await kyvra_graph.ainvoke(initial)
        return result

    async def generate_report(self) -> str:
        state = await self._run("full")
        return self._format_report(state)

    async def quick_scan(self) -> KyvraState:
        return await self._run("quick")
```

### How `ainvoke` works

```python
result = await kyvra_graph.ainvoke(initial_state)
```

`ainvoke` does the following:
1. Starts at `START`
2. Runs `collect_node` with `initial_state`
3. Merges `collect_node`'s returned dict into state
4. Calls `router.after_collect(state)` to decide what comes next
5. If `"score"` → starts `analyst_node` AND `scout_node` simultaneously
6. Waits for both to finish, merges both results into state
7. Calls `_parallel_join` (does nothing, just a barrier)
8. Calls `router.after_parallel(state)` to decide next
9. If `"write"` → runs `writer_node`
10. Runs `publisher_node`
11. Reaches `END`, returns the final state dict

The final state dict contains ALL the keys accumulated across all nodes.

### Handler migration example

**Before:**
```python
# handlers.py
supervisor = SupervisorAgent(_get_module())
report, ctx = await supervisor.generate_report_with_ctx()
top_items = ctx.top_items          # attribute access on PipelineContext
```

**After:**
```python
# handlers.py
runner = _runner()                 # GraphRunner(_active_module)
report, state = await runner.generate_report_with_ctx()
top_items = state.get("top_items") # dict key access on KyvraState
```

Two differences:
1. `GraphRunner` instead of `SupervisorAgent`
2. `state.get("top_items")` instead of `ctx.top_items` (dict, not object)

### The `_runner()` helper

```python
# In handlers.py
_active_module: str = ACTIVE_MODULE   # global, changed by /module command

def _runner() -> GraphRunner:
    return GraphRunner(_active_module)
```

Every Telegram command calls `_runner()` to get a fresh `GraphRunner` for the
currently active module. The module can be switched at runtime by `/module
crypto` without restarting the bot.

---

## 9. Phase 6 — Streaming Progress

**Files:** `agents/graph_runner.py` (`stream_events`), `interfaces/telegram/handlers.py` (`cmd_report`)

### The problem

Before streaming, the user saw:

```
User: /report
Bot:  ⏳ Gathering news and writing report... (30-60 sec)
       ... 45 seconds of silence ...
Bot:  [full report]
```

With streaming, the user sees:

```
User: /report
Bot:  ⏳ Starting pipeline...
Bot:  📡 Fetching news sources...
Bot:  📊 Scoring stories...
Bot:  🔍 Scanning trends...
Bot:  ✍️ Writing report...
Bot:  [full report]
```

### How `astream` works

`kyvra_graph.astream(state)` is an async generator that yields one event per
completed node. Each event is a `dict` where the key is the node name and the
value is the state *output* from that node.

```python
async for event in kyvra_graph.astream(initial_state):
    # event looks like: {"collect": {"raw_items": [...], "errors": []}}
    node_name = list(event.keys())[0]   # "collect"
    node_output = event[node_name]      # {"raw_items": [...], "errors": []}
```

The `stream_events` generator in `GraphRunner` wraps this with a simpler API:

```python
async def stream_events(self, mode="full", ...) -> AsyncIterator[tuple[str, KyvraState | None]]:
    """Yields (node_name, None) for each completed node,
       then ("__end__", final_state) when done."""

    final_state = initial.copy()
    async for event in kyvra_graph.astream(initial):
        for node_name, node_state in event.items():
            if isinstance(node_state, dict):
                final_state.update(node_state)
            yield node_name, None           # progress signal

    yield "__end__", final_state            # done signal with final state
```

### The streaming `cmd_report` handler

```python
_STREAM_LABELS = {
    "collect":   "📡 Fetching news sources...",
    "analyst":   "📊 Scoring stories...",
    "scout":     "🔍 Scanning trends...",
    "join":      "🔗 Analysing...",
    "writer":    "✍️ Writing report...",
    "publisher": "📬 Saving results...",
}

async def cmd_report(update, context):
    msg = await update.message.reply_text("⏳ Starting pipeline...")

    final_state = None
    runner = _runner()

    async for node_name, state in runner.stream_events(mode="full"):
        if node_name == "__end__":
            final_state = state              # capture the final state
        elif node_name in _STREAM_LABELS:
            try:
                await msg.edit_text(_STREAM_LABELS[node_name])  # update the spinner
            except Exception:
                pass                         # ignore Telegram "not modified" errors

    # Build report and send
    report = final_state.get("report_text") or "Could not generate report."
    await msg.delete()
    for chunk in split_long_message(report):
        await update.message.reply_text(chunk, ...)
```

**Key design decisions:**

1. **Edit the same message** (`msg.edit_text`) rather than sending new ones —
   this creates a "spinner" effect where one message transitions through states.

2. **Ignore edit errors** — Telegram returns an error if you try to edit a
   message with the same text as before. The `try/except pass` handles this
   cleanly. (This can happen because analyst and scout both feed into `join`,
   so two events arrive close together.)

3. **Capture final_state at `"__end__"`** — the last yield from `stream_events`
   is `("__end__", final_state)`, so the handler knows when the graph is done
   and can access the complete final state.

---

## 10. How Everything Connects — The Full Data Flow

Here is the complete journey of a `/report` command from Telegram to response:

```
User types: /report
     │
     ▼
handlers.cmd_report()
     │
     ├─ Creates: msg = "⏳ Starting pipeline..."
     ├─ Creates: runner = GraphRunner("tech")
     │
     ▼
runner.stream_events(mode="full")
     │
     ▼
kyvra_graph.astream(empty_state("tech", mode="full"))
     │
     ├─ Node: collect_node
     │    reads:  state["module_name"] = "tech"
     │    does:   loads TechModule, fetches all sources (parallel asyncio.gather)
     │            keyword filters, deduplicates, story continuity check
     │    writes: state["raw_items"] = [24 RawItem objects]
     │    yields: event {"collect": {"raw_items": [...]}}
     │         → Telegram: "📡 Fetching news sources..."
     │
     ├─ Nodes: analyst_node + scout_node  (PARALLEL)
     │    analyst reads:  state["raw_items"]
     │    analyst does:   scores each item 0–100
     │    analyst writes: state["scored_items"] = [top 14], state["top_items"] = [top 7]
     │
     │    scout reads:  state["raw_items"]
     │    scout does:   counts topic keywords, builds heatmap
     │    scout writes: state["trend_heatmap"] = "AI Agents 🔥 | LLM 📈"
     │
     │    yields: event {"analyst": {...}} → Telegram: "📊 Scoring stories..."
     │    yields: event {"scout": {...}}  → Telegram: "🔍 Scanning trends..."
     │
     ├─ Node: join (dummy fan-in)
     │    waits for analyst AND scout to both finish
     │    does: nothing (return {})
     │    yields: event {"join": {}} → Telegram: "🔗 Analysing..."
     │
     ├─ router.after_parallel(state) → "write"  (mode == "full")
     │
     ├─ Node: writer_node
     │    reads:  state["top_items"] (from analyst)
     │            state["trend_heatmap"] (from scout)
     │            state["content_format"] = "report"
     │    does:   builds enriched payload, calls LLMProvider.complete(prompt)
     │    writes: state["report_text"] = "🤖 KYVRA TECH REPORT – ..."
     │    yields: event {"writer": {...}} → Telegram: "✍️ Writing report..."
     │
     ├─ Node: publisher_node
     │    reads:  state["top_items"], state["module_name"]
     │    does:   marks top_items URLs as seen in SQLite
     │            pushes stories to TrendPost webhook (if configured)
     │    writes: state["published"] = True
     │    yields: event {"publisher": {...}} → Telegram: "📬 Saving results..."
     │
     └─ Reaches END
          yields: ("__end__", final_state)
               │
               ▼
         cmd_report receives final_state
         builds inline tweet keyboard
         splits report into 4096-char chunks
         sends to Telegram
```

---

## 11. Mental Models & Common Mistakes

### Mental model 1: Nodes are pure functions with side effects separated

A node should:
- **Read** from state
- **Do** its work
- **Write** its results back

Nodes that cause side effects (network calls, database writes) are fine — but
keep side-effect nodes separate from computation nodes. In Kyvra, `publisher`
handles all side effects, and `analyst`/`scout` are pure computation.

### Mental model 2: State is a whiteboard, not a pipeline

The old `PipelineContext` was threaded through each agent sequentially, with
each one mutating it. That's a pipeline.

LangGraph state is more like a **shared whiteboard**: every node can read any
key, and each node writes to its own section. Multiple nodes can be reading
and writing simultaneously.

### Mental model 3: Edges are contracts

When you write `g.add_edge("collect", "analyst")`, you are making a contract:
> "analyst_node will only ever start after collect_node has finished"

When you write two edges from the same source:
```python
g.add_edge("collect", "analyst")
g.add_edge("collect", "scout")
```
You are saying:
> "Both analyst and scout can start as soon as collect finishes — neither waits for the other"

### Common mistake 1: Returning the full state from a node

```python
# WRONG — do not do this
async def my_node(state: KyvraState) -> KyvraState:
    state["new_key"] = "value"
    return state             # ← returns entire state, overwrites everything

# CORRECT
async def my_node(state: KyvraState) -> dict:
    return {"new_key": "value"}   # ← returns only the changed keys
```

### Common mistake 2: Mutating the input state

```python
# WRONG — state is read-only inside a node
async def my_node(state: KyvraState) -> dict:
    state["raw_items"].append(new_item)   # ← mutates the input!
    return {}

# CORRECT — create new values, return them
async def my_node(state: KyvraState) -> dict:
    items = list(state.get("raw_items") or [])
    items.append(new_item)
    return {"raw_items": items}
```

### Common mistake 3: Putting heavy state in the state dict

```python
# WRONG — live objects can't be serialised by the checkpointer
class KyvraState(TypedDict):
    module: BaseModule        # ← a live Python object

# CORRECT — store only serialisable primitives
class KyvraState(TypedDict):
    module_name: str          # ← a string; load the object inside each node
```

### Common mistake 4: Forgetting the fan-in node

```python
# WRONG — two conditional edges from two different sources
# Which one fires? Both? First one? This is undefined.
g.add_edge("analyst", END)
g.add_edge("scout", END)

# CORRECT — fan-in to a single join node first
g.add_edge("analyst", "join")
g.add_edge("scout", "join")
g.add_edge("join", END)
```

---

## 12. What to Learn Next

You now understand the full LangGraph stack as implemented in Kyvra.
Here is the natural learning progression from here:

### Next: Checkpointing (Phase 7)

Add a `SqliteSaver` checkpointer so graph state survives bot restarts:

```python
from langgraph.checkpoint.sqlite import SqliteSaver

checkpointer = SqliteSaver.from_conn_string("kyvra.db")
kyvra_graph = build_graph(checkpointer=checkpointer)

# Each run needs a thread_id so the checkpointer knows which run to resume
result = await kyvra_graph.ainvoke(
    initial_state,
    config={"configurable": {"thread_id": f"user_{user_id}"}}
)
```

**What this enables:**
- Chat history survives bot restarts (currently lost)
- Human-in-the-loop: pause the graph mid-run, resume after user approval

```python
# Compile with interrupt BEFORE the writer node
kyvra_graph = build_graph(
    checkpointer=checkpointer,
    interrupt_before=["writer"]    # pause here
)

# Run until the interrupt point
state = await kyvra_graph.ainvoke(initial_state, config={"thread_id": "abc"})
# Bot sends: "Here are today's top stories. Type /approve to write the report."

# Later, when user sends /approve:
result = await kyvra_graph.ainvoke(
    None,    # None = "resume from where we stopped"
    config={"thread_id": "abc"}
)
```

### Next: Subgraphs (Multi-Agent)

For the `/newsletter` command, you could build a 3-agent subgraph where
agents collaborate: one researches context, one drafts, one edits.

```python
# Content generation subgraph
content_graph = StateGraph(ContentState)
content_graph.add_node("researcher", research_node)
content_graph.add_node("drafter",    draft_node)
content_graph.add_node("editor",     edit_node)
content_graph.add_edge("researcher", "drafter")
content_graph.add_edge("drafter", "editor")
content_subgraph = content_graph.compile()

# Use it as a single node in the main graph
main_graph.add_node("generate_content", content_subgraph)
```

**This is what "multi-agent" means in LangGraph:** agents are subgraphs
embedded inside larger graphs. Each subgraph has its own state and its own
internal flow, but from the outside it looks like a single node.

### Key LangGraph docs to read

1. **Concepts overview** — `langchain-ai.github.io/langgraph/concepts/`
2. **How-to: streaming** — shows all streaming modes (`values`, `updates`, `events`)
3. **How-to: human-in-the-loop** — interrupt + resume patterns
4. **How-to: subgraphs** — nesting graphs inside graphs

### Key Python concepts that support this architecture

1. **`TypedDict`** — typed dictionaries (Python 3.8+, `typing_extensions`)
2. **`ABC` and `abstractmethod`** — how `LLMProvider` enforces the interface contract
3. **`async/await` and `asyncio.gather`** — Python's async model
4. **`AsyncIterator` and `yield`** — how `stream_events` works as a generator
5. **`from __future__ import annotations`** — deferred annotation evaluation (Python 3.7+)
