import asyncio
from collections import Counter, defaultdict
from agents.base import BaseAgent, PipelineContext
from modules.base import RawItem
from utils.api_client import fetch_source

# X sources are pre-filtered by their API query (account curation or min_faves).
# Applying keyword filter on top would drop conversational tweets that are genuinely relevant.
_KEYWORD_FILTER_BYPASS = {"X - AI Leaders", "X - AI Trending", "X - Indie Dev"}


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

        # Keyword relevance filter — bypassed for pre-curated X sources
        filtered: list[RawItem] = []
        for item in all_items:
            if item.source in _KEYWORD_FILTER_BYPASS:
                filtered.append(item)
            else:
                text = (item.title + " " + item.summary).lower()
                if any(kw in text for kw in keywords):
                    filtered.append(item)

        # Dedup and detect cross-source coverage
        deduped = _dedup_with_cross_source(filtered)

        # Log source breakdown for observability
        breakdown = Counter(item.source for item in deduped)
        multi_source = sum(1 for item in deduped if item.cross_source_count > 1)
        self._log(
            f"{len(all_items)} fetched → {len(filtered)} relevant → {len(deduped)} after dedup "
            f"({multi_source} cross-source) | {dict(breakdown)}"
        )

        ctx.raw_items = deduped
        return ctx
