import logging
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from modules.base import RawItem
from modules.tech.config import HN_SPIKE_THRESHOLD, GITHUB_STARS_SPIKE

logger = logging.getLogger(__name__)


def _parse_timestamp(published_at: str) -> float | None:
    """Try to parse various timestamp formats → unix timestamp."""
    if not published_at:
        return None
    # Unix timestamp (HackerNews)
    if published_at.isdigit():
        return float(published_at)
    # RFC 2822 (RSS)
    try:
        return parsedate_to_datetime(published_at).timestamp()
    except Exception:
        pass
    # ISO 8601
    try:
        return datetime.fromisoformat(published_at.replace("Z", "+00:00")).timestamp()
    except Exception:
        pass
    return None


def _recency_score(published_at: str) -> int:
    """0-20 points based on how recent the item is."""
    ts = _parse_timestamp(published_at)
    if ts is None:
        return 5  # unknown age → small score
    age_hours = (time.time() - ts) / 3600
    if age_hours < 6:
        return 20
    elif age_hours < 24:
        return 13
    elif age_hours < 48:
        return 6
    return 0


def _engagement_score(item: RawItem) -> int:
    """0-40 points from engagement signals."""
    if item.source == "HackerNews":
        # HN points 0-30, comments 0-10
        pts = min(30, int(item.score / 10))
        cmts = min(10, int(item.comments / 20))
        return pts + cmts
    elif item.source == "GitHub Trending":
        # stars today 0-40
        return min(40, int(item.score / 3))
    else:
        # RSS sources: no engagement data → fixed mid value
        return 15


def calculate_confidence(item: RawItem) -> tuple[int, bool]:
    """Return (confidence_score 0-100, is_spike bool)."""
    engagement = _engagement_score(item)        # 0-40
    authority = item.authority_score             # 0-20
    recency = _recency_score(item.published_at)  # 0-20
    relevance = 10                               # base: passed keyword filter
    total = min(100, engagement + authority + recency + relevance)

    is_spike = (
        (item.source == "HackerNews" and item.score >= HN_SPIKE_THRESHOLD)
        or (item.source == "GitHub Trending" and item.score >= GITHUB_STARS_SPIKE)
    )
    return total, is_spike


class AnalystAgent:
    """Scores each item with a Confidence Score (0-100) and flags spikes."""

    async def run(self, context: dict) -> dict:
        raw_items: list[RawItem] = context.get("raw_items", [])
        logger.info(f"[Analyst] Scoring {len(raw_items)} items...")

        scored = []
        for item in raw_items:
            score, is_spike = calculate_confidence(item)
            scored.append({
                "title": item.title,
                "url": item.url,
                "source": item.source,
                "published_at": item.published_at,
                "summary": item.summary,
                "confidence_score": score,
                "is_spike": is_spike,
                "raw_score": item.score,
            })

        # Sort by confidence score descending
        scored.sort(key=lambda x: (x["is_spike"], x["confidence_score"]), reverse=True)

        from config import MAX_REPORT_ITEMS
        context["scored_items"] = scored[:MAX_REPORT_ITEMS * 2]  # keep buffer for narrative
        context["top_items"] = scored[:MAX_REPORT_ITEMS]
        logger.info(f"[Analyst] Top item: {scored[0]['title'][:60] if scored else 'none'} | Score: {scored[0]['confidence_score'] if scored else 0}")
        return context
