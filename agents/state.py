"""
LangGraph state for the Kyvra pipeline.

KyvraState is a TypedDict — LangGraph reads from it and each node returns
a dict of only the keys it updates. LangGraph merges the returned dict into
the running state automatically.

Replaces the PipelineContext dataclass in agents/base.py.

Key fields
----------
module_name : str
    Active module slug ("tech", "crypto", "vietnam", …). The graph loads
    the concrete BaseModule instance from this at the start of each node
    that needs it.
mode : "full" | "quick" | "topic" | "breaking"
    Controls which nodes run via conditional routing:
    - "full"     → collect → analyst+scout → writer → publisher
    - "quick"    → collect → analyst+scout → END (no LLM)
    - "topic"    → same as "full" but keyword-filtered collect
    - "breaking" → collect → analyst+scout → END (spikes only)
topic_filter : str | None
    Keyword passed to collect_node when mode == "topic".
content_format : "report" | "thread" | "brief" | "newsletter" | "script"
    Tells writer_node which prompt template to use.
content_rank : int
    Story rank (1-based) to use for thread/brief/newsletter/script.
    Ignored for "report" format.
"""

from __future__ import annotations

from typing import Any, Optional
from typing_extensions import TypedDict


class KyvraState(TypedDict, total=False):
    # --- Input (set by callers before ainvoke) ---
    module_name: str
    mode: str                           # "full" | "quick" | "topic" | "breaking"
    topic_filter: Optional[str]         # keyword for mode=="topic"
    content_format: str                 # "report" | "thread" | "brief" | "newsletter" | "script"
    content_rank: int                   # 1-based story rank for content formats

    # --- Collect node output ---
    raw_items: list[Any]                # list[RawItem] — typed as Any to avoid circular import

    # --- Analyst node output ---
    scored_items: list[Any]             # list[ScoredItem] top-14
    top_items: list[Any]                # list[ScoredItem] top-7 for LLM

    # --- Scout node output ---
    trend_heatmap: str                  # e.g. "AI Agents 🔥 | LLM 📈"

    # --- Writer node output ---
    report_text: str                    # final AI-generated prose

    # --- Publisher node output ---
    published: bool                     # True after mark_seen + webhook push

    # --- Shared error log ---
    errors: list[str]


def empty_state(
    module_name: str,
    mode: str = "full",
    topic_filter: Optional[str] = None,
    content_format: str = "report",
    content_rank: int = 1,
) -> KyvraState:
    """Return a fully-initialised empty KyvraState ready for ainvoke()."""
    return KyvraState(
        module_name=module_name,
        mode=mode,
        topic_filter=topic_filter,
        content_format=content_format,
        content_rank=content_rank,
        raw_items=[],
        scored_items=[],
        top_items=[],
        trend_heatmap="",
        report_text="",
        published=False,
        errors=[],
    )
