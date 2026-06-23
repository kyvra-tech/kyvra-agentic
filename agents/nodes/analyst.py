"""
analyst_node — LangGraph node: score items 0-100, flag spikes.

Reads:  state["raw_items"], state["module_name"]
Writes: state["scored_items"], state["top_items"]

Pure Python — no LLM call. Runs in parallel with scout_node.
Scoring functions are unchanged from agents/analyst.py so existing unit
tests in tests/test_analyst.py continue to pass without modification.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from email.utils import parsedate_to_datetime

from agents.base import ScoredItem
from agents.state import KyvraState
from agents.registry import load_module
from modules.base import RawItem
from config import MAX_REPORT_ITEMS
import services.memory as memory

logger = logging.getLogger(__name__)

_AUTHORITY_SOURCES = {"X - AI Leaders"}
_AUTHORITY_ENGAGEMENT_FLOOR = 15


# ---------------------------------------------------------------------------
# Scoring helpers (unchanged — keep importable so test_analyst.py still works)
# ---------------------------------------------------------------------------

def _parse_timestamp(published_at: str) -> float | None:
    if not published_at:
        return None
    if published_at.isdigit():
        return float(published_at)
    try:
        return parsedate_to_datetime(published_at).timestamp()
    except Exception:
        pass
    try:
        return datetime.fromisoformat(published_at.replace("Z", "+00:00")).timestamp()
    except Exception:
        pass
    return None


def _recency_score(published_at: str) -> int:
    ts = _parse_timestamp(published_at)
    if ts is None:
        return 5
    age_hours = (time.time() - ts) / 3600
    if age_hours < 6:
        return 20
    elif age_hours < 24:
        return 13
    elif age_hours < 48:
        return 6
    return 0


def _engagement_score(item: RawItem) -> int:
    if item.source == "GitHub Trending":
        return min(40, int(item.score / 3))
    elif item.source.startswith("X -"):
        raw = min(35, int(item.score / 15)) + min(5, int(item.comments / 5))
        if item.source in _AUTHORITY_SOURCES:
            return max(_AUTHORITY_ENGAGEMENT_FLOOR, raw)
        return raw
    else:
        return 15


def _relevance_score(item: RawItem, keywords: list[str]) -> int:
    text = (item.title + " " + item.summary).lower()
    hits = sum(1 for kw in keywords if kw in text)
    return min(20, 10 + max(0, hits - 1) * 2)


def _cross_source_boost(item: RawItem) -> int:
    return 10 if item.cross_source_count >= 2 else 0


def _velocity_score(item: RawItem) -> int:
    if not item.source.startswith("X -"):
        return 0
    ts = _parse_timestamp(item.published_at)
    if ts is None:
        return 0
    age_hours = max((time.time() - ts) / 3600, 0.5)
    lph = item.score / age_hours
    if lph >= 300:
        return 10
    if lph >= 100:
        return 7
    if lph >= 50:
        return 4
    return 0


def _is_spike(item: RawItem, github_threshold: int, x_threshold: int) -> bool:
    return (
        (item.source == "GitHub Trending" and item.score >= github_threshold)
        or (item.source.startswith("X -") and item.score >= x_threshold)
    )


def _performance_score(item: RawItem, source_perf: dict[str, float]) -> int:
    """Score based on historical performance signals for this source.

    Reads avg_delta from the performance_signals table (via get_source_performance).
    Maps the average delta [-5, +5] to a score of [-5, +10].
    Sources with no history get 0 (neutral).
    """
    avg_delta = source_perf.get(item.source)
    if avg_delta is None:
        return 0
    # Map [-5, +5] delta → [-5, +10] score
    #   avg_delta = +5  →  +10 (best performing source)
    #   avg_delta =  0  →    0 (neutral)
    #   avg_delta = -5  →   -5 (worst performing source)
    return max(-5, min(10, round(avg_delta * 2)))


def score_item(
    item: RawItem,
    keywords: list[str],
    github_threshold: int = 100,
    x_threshold: int = 500,
    source_perf: dict[str, float] | None = None,
) -> ScoredItem:
    engagement  = _engagement_score(item)
    authority   = item.authority_score
    recency     = _recency_score(item.published_at)
    relevance   = _relevance_score(item, keywords)
    cross_boost = _cross_source_boost(item)
    velocity    = _velocity_score(item)
    perf        = _performance_score(item, source_perf or {})

    confidence = min(100, max(0, engagement + authority + recency + relevance + cross_boost + velocity + perf))

    return ScoredItem(
        title=item.title,
        url=item.url,
        source=item.source,
        published_at=item.published_at,
        summary=item.summary,
        confidence_score=confidence,
        is_spike=_is_spike(item, github_threshold, x_threshold),
        raw_score=item.score,
        cross_source_count=item.cross_source_count,
        media_url=item.media_url,
        media_type=item.media_type,
    )


# ---------------------------------------------------------------------------
# LangGraph node
# ---------------------------------------------------------------------------

async def run(state: KyvraState) -> dict:
    raw_items = state.get("raw_items") or []
    module_name = state["module_name"]
    module = load_module(module_name)

    logger.info("[analyst] Scoring %d items...", len(raw_items))
    keywords = [kw.lower() for kw in module.get_keywords()]
    github_threshold, x_threshold = module.get_spike_thresholds()

    # Load historical performance data for the feedback loop
    source_perf = memory.get_source_performance(days=30)
    if source_perf:
        logger.info("[analyst] Feedback loop active — %d sources have performance history", len(source_perf))

    scored = sorted(
        [score_item(item, keywords, github_threshold, x_threshold, source_perf) for item in raw_items],
        key=lambda x: (x.is_spike, x.confidence_score),
        reverse=True,
    )

    scored_items = scored[: MAX_REPORT_ITEMS * 2]
    top_items = scored[:MAX_REPORT_ITEMS]

    if scored:
        top = scored[0]
        spikes = sum(1 for s in scored if s.is_spike)
        cross = sum(1 for s in scored if s.cross_source_count >= 2)
        logger.info(
            "[analyst] Top: '%s' score=%d spike=%s | total=%d spikes=%d cross=%d",
            top.title[:55], top.confidence_score, top.is_spike,
            len(scored), spikes, cross,
        )

    return {"scored_items": scored_items, "top_items": top_items}
