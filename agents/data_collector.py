import asyncio
import logging
from modules.base import BaseModule, RawItem
from utils.api_client import fetch_source

logger = logging.getLogger(__name__)


class DataCollectorAgent:
    """Fetches raw data from all sources defined in the active module."""

    async def run(self, context: dict) -> dict:
        module: BaseModule = context["module"]
        sources = module.get_sources()
        keywords = [kw.lower() for kw in module.get_keywords()]

        logger.info(f"[DataCollector] Fetching {len(sources)} sources...")

        tasks = [fetch_source(src) for src in sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_items: list[RawItem] = []
        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"[DataCollector] Source fetch error: {result}")
                continue
            all_items.extend(result)

        # Filter by keyword relevance
        filtered = []
        for item in all_items:
            text = (item.title + " " + item.summary).lower()
            if any(kw in text for kw in keywords):
                filtered.append(item)

        # Deduplicate by title similarity (simple)
        seen_titles: set[str] = set()
        deduped = []
        for item in filtered:
            key = item.title.lower()[:60]
            if key not in seen_titles:
                seen_titles.add(key)
                deduped.append(item)

        logger.info(f"[DataCollector] {len(all_items)} fetched → {len(deduped)} after filter/dedup")
        context["raw_items"] = deduped
        return context
