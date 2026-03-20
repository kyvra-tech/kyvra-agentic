import time
from email.utils import parsedate_to_datetime
from datetime import datetime

from agents.base import BaseAgent, PipelineContext, ScoredItem
from modules.base import RawItem
from config import MAX_REPORT_ITEMS

# X authority accounts get a minimum engagement floor.
# A @AnthropicAI tweet with 20 likes announcing a new model is more valuable
# than its raw like count suggests — same floor as RSS sources.
_AUTHORITY_SOURCES = {"X - AI Leaders"}
_AUTHORITY_ENGAGEMENT_FLOOR = 15


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
    """0–20 pts. Fresher = higher."""
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
    """0–40 pts from source-specific engagement signals."""
    if item.source == "GitHub Trending":
        # stars_today 0–40
        return min(40, int(item.score / 3))

    elif item.source.startswith("X -"):
        # likes 0–35, replies 0–5
        raw = min(35, int(item.score / 15)) + min(5, int(item.comments / 5))
        # Authority account floor: a low-likes announcement from a trusted account
        # should not be penalised below the RSS baseline
        if item.source in _AUTHORITY_SOURCES:
            return max(_AUTHORITY_ENGAGEMENT_FLOOR, raw)
        return raw

    else:
        # RSS: no engagement data → baseline
        return 15


def _relevance_score(item: RawItem, keywords: list[str]) -> int:
    """10 base + 2 per additional keyword match, capped at 20.

    Rationale: an item matching 'openai', 'gpt', AND 'agent' is more on-topic
    than one that just scraped past a single keyword.
    """
    text = (item.title + " " + item.summary).lower()
    hits = sum(1 for kw in keywords if kw in text)
    return min(20, 10 + max(0, hits - 1) * 2)


def _cross_source_boost(item: RawItem) -> int:
    """0 or 10 pts. A story covered by 2+ sources is independently validated as trending."""
    return 10 if item.cross_source_count >= 2 else 0


def _velocity_score(item: RawItem) -> int:
    """0–10 pts. Rewards X items with high likes/hour (momentum, not just raw count).

    A 2h-old tweet with 300 likes (150/hr) outranks a 6h-old tweet with 500 likes (83/hr).
    Tiers: >300/hr → 10pts, >100/hr → 7pts, >50/hr → 4pts, else 0.
    """
    if not item.source.startswith("X -"):
        return 0
    ts = _parse_timestamp(item.published_at)
    if ts is None:
        return 0
    age_hours = max((time.time() - ts) / 3600, 0.5)  # floor at 0.5h to avoid div/0
    likes_per_hour = item.score / age_hours
    if likes_per_hour >= 300:
        return 10
    if likes_per_hour >= 100:
        return 7
    if likes_per_hour >= 50:
        return 4
    return 0


def _is_spike(item: RawItem, github_threshold: int, x_threshold: int) -> bool:
    return (
        (item.source == "GitHub Trending" and item.score >= github_threshold)
        or (item.source.startswith("X -") and item.score >= x_threshold)
    )


def score_item(item: RawItem, keywords: list[str], github_threshold: int = 100, x_threshold: int = 500) -> ScoredItem:
    engagement   = _engagement_score(item)          # 0–40
    authority    = item.authority_score              # 0–20
    recency      = _recency_score(item.published_at) # 0–20
    relevance    = _relevance_score(item, keywords)  # 10–20  (was fixed at 10)
    cross_boost  = _cross_source_boost(item)         # 0 or 10
    velocity     = _velocity_score(item)             # 0–10 (X only: fast engagement)

    confidence = min(100, engagement + authority + recency + relevance + cross_boost + velocity)

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
    )


class AnalystAgent(BaseAgent):
    """Scores each item 0–100 and flags spikes. Higher score = more trending/hot."""

    async def run(self, ctx: PipelineContext) -> PipelineContext:
        self._log(f"Scoring {len(ctx.raw_items)} items...")
        keywords = [kw.lower() for kw in ctx.module.get_keywords()]
        github_threshold, x_threshold = ctx.module.get_spike_thresholds()

        scored = sorted(
            [score_item(item, keywords, github_threshold, x_threshold) for item in ctx.raw_items],
            key=lambda x: (x.is_spike, x.confidence_score),
            reverse=True,
        )

        ctx.scored_items = scored[: MAX_REPORT_ITEMS * 2]
        ctx.top_items = scored[:MAX_REPORT_ITEMS]

        if scored:
            top = scored[0]
            spikes = sum(1 for s in scored if s.is_spike)
            cross = sum(1 for s in scored if s.cross_source_count >= 2)
            self._log(
                f"Top: '{top.title[:55]}' score={top.confidence_score} spike={top.is_spike} | "
                f"total={len(scored)} spikes={spikes} cross-source={cross}"
            )
        return ctx
