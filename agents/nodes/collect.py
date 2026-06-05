"""
collect_node — LangGraph node: fetch, filter, dedup, story-continuity.

Reads:  state["module_name"], state["mode"], state["topic_filter"]
Writes: state["raw_items"], state["errors"]

This is a direct port of DataCollectorAgent.run() adapted to the LangGraph
node contract: returns a dict of only the keys it updates rather than
mutating a PipelineContext object.
"""

import asyncio
import logging
import time
from collections import Counter, defaultdict

from agents.state import KyvraState
from agents.registry import load_module
from modules.base import RawItem
from utils.api_client import fetch_source
import services.memory as memory

logger = logging.getLogger(__name__)

_MIN_ITEMS_AFTER_SEEN_FILTER = 3


def _dedup_with_cross_source(items: list[RawItem]) -> list[RawItem]:
    """Group items covering the same story; pick the best representative."""
    url_groups: dict[str, list[RawItem]] = defaultdict(list)
    for item in items:
        url_groups[item.url.lower().rstrip("/")].append(item)

    title_groups: dict[str, list[RawItem]] = defaultdict(list)
    for group in url_groups.values():
        for item in group:
            title_groups[item.title.lower()[:60]].append(item)

    deduped: list[RawItem] = []
    for group in title_groups.values():
        best = max(group, key=lambda x: x.authority_score)
        best.cross_source_count = len({i.source for i in group})
        deduped.append(best)
    return deduped


async def run(state: KyvraState) -> dict:
    module_name = state["module_name"]
    module = load_module(module_name)
    errors: list[str] = list(state.get("errors") or [])

    sources = module.get_sources()
    keywords = [kw.lower() for kw in module.get_keywords()]
    logger.info("[collect] Fetching %d sources for module '%s'...", len(sources), module_name)

    results = await asyncio.gather(
        *[fetch_source(src) for src in sources],
        return_exceptions=True,
    )

    all_items: list[RawItem] = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            msg = f"collect: '{sources[i].name}' failed: {result}"
            logger.warning("[collect] %s", msg)
            errors.append(msg)
            continue
        all_items.extend(result)

    # Keyword relevance filter
    source_bypass = {src.name for src in sources if src.bypass_keyword_filter}
    topic_filter = state.get("topic_filter")
    extra_kw = [topic_filter.lower()] if topic_filter else []

    filtered: list[RawItem] = []
    for item in all_items:
        if item.source in source_bypass:
            filtered.append(item)
        else:
            text = (item.title + " " + item.summary).lower()
            if any(kw in text for kw in keywords + extra_kw):
                filtered.append(item)

    deduped = _dedup_with_cross_source(filtered)

    # Story continuity
    from agents.nodes.analyst import _parse_timestamp
    _, x_spike_threshold = module.get_spike_thresholds()
    spike_lph = x_spike_threshold / 24
    seen_urls = memory.get_seen_urls(module_name, days=7)
    if seen_urls:
        fresh: list[RawItem] = []
        for item in deduped:
            if item.url.lower().rstrip("/") not in seen_urls:
                fresh.append(item)
            elif item.source.startswith("X -"):
                ts = _parse_timestamp(item.published_at)
                age_hours = max((time.time() - ts) / 3600, 0.5) if ts else 24.0
                if (item.score / age_hours) >= spike_lph:
                    fresh.append(item)
        if len(fresh) >= _MIN_ITEMS_AFTER_SEEN_FILTER:
            deduped = fresh
            logger.info("[collect] Story continuity: %d fresh items", len(deduped))
        else:
            logger.warning(
                "[collect] Story continuity floor: only %d fresh — keeping all %d",
                len(fresh), len(deduped),
            )

    breakdown = Counter(item.source for item in deduped)
    multi_source = sum(1 for item in deduped if item.cross_source_count > 1)
    logger.info(
        "[collect] %d fetched → %d relevant → %d after dedup (%d cross-source) | %s",
        len(all_items), len(filtered), len(deduped), multi_source, dict(breakdown),
    )

    return {"raw_items": deduped, "errors": errors}
