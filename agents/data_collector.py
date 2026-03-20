import asyncio
import time
from collections import Counter, defaultdict
from agents.base import BaseAgent, PipelineContext
from modules.base import RawItem
from utils.api_client import fetch_source
import services.memory as memory
from agents.analyst import _parse_timestamp

_MIN_ITEMS_AFTER_SEEN_FILTER = 3  # floor: bypass filter if fewer items survive


def _dedup_with_cross_source(items: list[RawItem]) -> list[RawItem]:
    """Group items covering the same story, pick the best one, record source count.

    Grouping key priority:
      1. Exact URL match (same link shared across sources)
      2. Title prefix match (first 60 chars, same story different wording)
    """
    # Group by URL first
    url_groups: dict[str, list[RawItem]] = defaultdict(list)
    for item in items:
        url_key = item.url.lower().rstrip("/")
        url_groups[url_key].append(item)

    # Within each URL group, further group by title prefix
    title_groups: dict[str, list[RawItem]] = defaultdict(list)
    for group in url_groups.values():
        for item in group:
            title_key = item.title.lower()[:60]
            title_groups[title_key].append(item)

    deduped: list[RawItem] = []
    for group in title_groups.values():
        # Pick the item with the highest authority score as the representative
        best = max(group, key=lambda x: x.authority_score)
        # Record how many distinct sources covered this story
        best.cross_source_count = len({i.source for i in group})
        deduped.append(best)

    return deduped


class DataCollectorAgent(BaseAgent):
    """Fetches from all sources in parallel, filters, deduplicates, and tracks cross-source signals."""

    async def run(self, ctx: PipelineContext) -> PipelineContext:
        sources = ctx.module.get_sources()
        keywords = [kw.lower() for kw in ctx.module.get_keywords()]
        self._log(f"Fetching {len(sources)} sources in parallel...")

        results = await asyncio.gather(
            *[fetch_source(src) for src in sources],
            return_exceptions=True,
        )

        all_items: list[RawItem] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self._warn(f"'{sources[i].name}' failed: {result}")
                continue
            all_items.extend(result)

        # Keyword relevance filter — bypassed for pre-curated sources (bypass_keyword_filter=True)
        source_bypass = {src.name for src in sources if src.bypass_keyword_filter}
        filtered: list[RawItem] = []
        for item in all_items:
            if item.source in source_bypass:
                filtered.append(item)
            else:
                text = (item.title + " " + item.summary).lower()
                if any(kw in text for kw in keywords):
                    filtered.append(item)

        # Dedup and detect cross-source coverage
        deduped = _dedup_with_cross_source(filtered)

        # Story continuity: suppress items already reported in the last 7 days,
        # unless they are spiking hard (high likes/hour = genuinely trending again).
        _, x_spike_threshold = ctx.module.get_spike_thresholds()
        spike_lph = x_spike_threshold / 24  # daily spike threshold → per-hour rate
        seen_urls = memory.get_seen_urls(ctx.module.name, days=7)
        if seen_urls:
            fresh: list[RawItem] = []
            for item in deduped:
                if item.url.lower().rstrip("/") not in seen_urls:
                    fresh.append(item)
                elif item.source.startswith("X -"):
                    # Spike override: re-surface if trending hard right now
                    ts = _parse_timestamp(item.published_at)
                    age_hours = max((time.time() - ts) / 3600, 0.5) if ts else 24.0
                    if (item.score / age_hours) >= spike_lph:
                        fresh.append(item)
            if len(fresh) >= _MIN_ITEMS_AFTER_SEEN_FILTER:
                deduped = fresh
                self._log(f"Story continuity: {len(deduped)} fresh items (suppressed {len(seen_urls)} seen)")
            else:
                self._warn(
                    f"Story continuity floor: only {len(fresh)} items after seen filter — "
                    f"bypassing to keep all {len(deduped)} items"
                )

        # Log source breakdown for observability
        breakdown = Counter(item.source for item in deduped)
        multi_source = sum(1 for item in deduped if item.cross_source_count > 1)
        self._log(
            f"{len(all_items)} fetched → {len(filtered)} relevant → {len(deduped)} after dedup "
            f"({multi_source} cross-source) | {dict(breakdown)}"
        )

        ctx.raw_items = deduped
        return ctx
