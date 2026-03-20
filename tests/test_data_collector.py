"""Unit tests for DataCollectorAgent dedup and seen-item filter logic."""

import time
import pytest
from unittest.mock import patch
from modules.base import RawItem
from agents.data_collector import _dedup_with_cross_source, _MIN_ITEMS_AFTER_SEEN_FILTER


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_item(
    title="Test story",
    url="https://example.com/story",
    source="X - AI Leaders",
    authority_score=15,
    score=100,
    published_at="2026-01-01T00:00:00Z",
) -> RawItem:
    return RawItem(
        title=title,
        url=url,
        source=source,
        published_at=published_at,
        summary="test summary",
        score=score,
        authority_score=authority_score,
    )


def _fresh_ts(age_hours: float = 1.0) -> str:
    """Return a Unix timestamp string for an item published `age_hours` ago."""
    return str(int(time.time() - age_hours * 3600))


# ── Dedup tests ───────────────────────────────────────────────────────────────

class TestDedupWithCrossSource:
    def test_empty_input(self):
        assert _dedup_with_cross_source([]) == []

    def test_single_item_passthrough(self):
        items = [make_item()]
        result = _dedup_with_cross_source(items)
        assert len(result) == 1
        assert result[0].cross_source_count == 1

    def test_same_url_deduped(self):
        items = [
            make_item(source="X - AI Leaders", url="https://example.com/story"),
            make_item(source="HN RSS", url="https://example.com/story"),
        ]
        result = _dedup_with_cross_source(items)
        assert len(result) == 1
        assert result[0].cross_source_count == 2

    def test_same_url_trailing_slash_normalized(self):
        items = [
            make_item(url="https://example.com/story/"),
            make_item(url="https://example.com/story"),
        ]
        result = _dedup_with_cross_source(items)
        assert len(result) == 1

    def test_different_stories_not_deduped(self):
        items = [
            make_item(title="OpenAI releases GPT-5", url="https://x.com/1"),
            make_item(title="Anthropic releases Claude 4", url="https://x.com/2"),
        ]
        result = _dedup_with_cross_source(items)
        assert len(result) == 2

    def test_best_authority_chosen(self):
        items = [
            make_item(source="Low Authority Source", url="https://example.com/story", authority_score=5),
            make_item(source="High Authority Source", url="https://example.com/story", authority_score=18),
        ]
        result = _dedup_with_cross_source(items)
        assert len(result) == 1
        assert result[0].source == "High Authority Source"

    def test_cross_source_count_reflects_distinct_sources(self):
        # Same URL from 3 different sources
        items = [
            make_item(source="Source A", url="https://example.com/story"),
            make_item(source="Source B", url="https://example.com/story"),
            make_item(source="Source C", url="https://example.com/story"),
        ]
        result = _dedup_with_cross_source(items)
        assert result[0].cross_source_count == 3

    def test_cross_source_count_same_source_not_doubled(self):
        # Same URL from the same source twice → count = 1
        items = [
            make_item(source="X - AI Leaders", url="https://example.com/story"),
            make_item(source="X - AI Leaders", url="https://example.com/story"),
        ]
        result = _dedup_with_cross_source(items)
        assert result[0].cross_source_count == 1

    def test_url_case_insensitive(self):
        items = [
            make_item(url="https://Example.COM/Story"),
            make_item(url="https://example.com/Story"),
        ]
        result = _dedup_with_cross_source(items)
        assert len(result) == 1

    def test_title_prefix_uses_60_chars(self):
        # Titles that differ only after char 60 should be grouped
        prefix = "A" * 60
        items = [
            make_item(title=prefix + "different ending one", url="https://x.com/1"),
            make_item(title=prefix + "different ending two", url="https://x.com/2"),
        ]
        result = _dedup_with_cross_source(items)
        assert len(result) == 1

    def test_mixed_dedup_and_unique(self):
        items = [
            make_item(title="Story A", url="https://x.com/a", source="Source 1"),
            make_item(title="Story A", url="https://hn.com/a", source="Source 2"),
            make_item(title="Story B", url="https://x.com/b", source="Source 1"),
        ]
        result = _dedup_with_cross_source(items)
        assert len(result) == 2
        cross_sourced = [r for r in result if r.cross_source_count >= 2]
        assert len(cross_sourced) == 1


# ── Seen-item filter (story continuity) ──────────────────────────────────────
#
# The filter lives in DataCollectorAgent.run() and calls memory.get_seen_urls().
# We test the filter logic by patching memory.get_seen_urls and inspecting
# ctx.raw_items on the output.
#
# Note: DataCollectorAgent.run() also calls fetch_source (network). We isolate
# the filter logic via a helper that mirrors the filter block from run().

def _apply_seen_filter(
    deduped: list[RawItem],
    seen_urls: set[str],
    module_name: str = "tech",
    x_spike_threshold: int = 500,
) -> list[RawItem]:
    """Mirror of the seen-filter block in DataCollectorAgent.run() for isolated testing."""
    from agents.analyst import _parse_timestamp
    import time as _time

    spike_lph = x_spike_threshold / 24
    if not seen_urls:
        return deduped

    fresh = []
    for item in deduped:
        if item.url.lower().rstrip("/") not in seen_urls:
            fresh.append(item)
        elif item.source.startswith("X -"):
            ts = _parse_timestamp(item.published_at)
            age_hours = max((_time.time() - ts) / 3600, 0.5) if ts else 24.0
            if (item.score / age_hours) >= spike_lph:
                fresh.append(item)

    if len(fresh) >= _MIN_ITEMS_AFTER_SEEN_FILTER:
        return fresh
    return deduped  # floor bypass


class TestSeenItemFilter:
    def test_unseen_items_pass_through(self):
        items = [make_item(url="https://x.com/new")]
        result = _apply_seen_filter(items, seen_urls=set())
        assert len(result) == 1

    def test_seen_item_suppressed(self):
        # 4 items total: 1 seen + 3 fresh → 3 survive (meets floor), seen item dropped
        items = [
            make_item(url="https://x.com/old",   score=10, published_at=_fresh_ts(2)),
            make_item(url="https://x.com/new1",  score=10, published_at=_fresh_ts(1)),
            make_item(url="https://x.com/new2",  score=10, published_at=_fresh_ts(1)),
            make_item(url="https://x.com/new3",  score=10, published_at=_fresh_ts(1)),
        ]
        result = _apply_seen_filter(items, seen_urls={"https://x.com/old"})
        urls = [i.url for i in result]
        assert "https://x.com/old" not in urls
        assert "https://x.com/new1" in urls

    def test_seen_x_item_kept_if_spiking(self):
        # 1200 likes in 1 hour = 1200/hr, spike_lph = 500/24 ≈ 20.8 → well above threshold
        item = make_item(
            url="https://x.com/hot",
            source="X - AI Trending",
            score=1200,
            published_at=_fresh_ts(1.0),
        )
        result = _apply_seen_filter([item], seen_urls={"https://x.com/hot"}, x_spike_threshold=500)
        assert len(result) == 1  # spike override kept it

    def test_seen_x_item_suppressed_if_not_spiking(self):
        # 1 seen (low engagement) + 3 fresh → seen item dropped, 3 fresh survive (meets floor)
        slow = make_item(url="https://x.com/slow", source="X - AI Trending", score=10, published_at=_fresh_ts(2.0))
        fresh_items = [make_item(url=f"https://x.com/f{i}", score=10, published_at=_fresh_ts(1)) for i in range(3)]
        result = _apply_seen_filter([slow] + fresh_items, seen_urls={"https://x.com/slow"}, x_spike_threshold=500)
        urls = [i.url for i in result]
        assert "https://x.com/slow" not in urls  # suppressed — not spiking
        assert len(result) == 3

    def test_floor_bypass_when_too_few_fresh(self):
        # Only 1 fresh item survives — floor kicks in and returns full list
        items = [
            make_item(url="https://x.com/seen1", score=5, published_at=_fresh_ts(2)),
            make_item(url="https://x.com/seen2", score=5, published_at=_fresh_ts(2)),
            make_item(url="https://x.com/new",   score=5, published_at=_fresh_ts(1)),
        ]
        seen = {"https://x.com/seen1", "https://x.com/seen2"}
        result = _apply_seen_filter(items, seen_urls=seen)
        # Only 1 survives filter (< _MIN_ITEMS_AFTER_SEEN_FILTER=3) → floor returns all 3
        assert len(result) == 3

    def test_exactly_min_items_no_bypass(self):
        # Exactly _MIN_ITEMS_AFTER_SEEN_FILTER fresh items → no bypass needed
        items = [make_item(url=f"https://x.com/{i}", score=5, published_at=_fresh_ts(1)) for i in range(5)]
        seen = {items[0].url, items[1].url}  # suppress 2, leave 3 fresh
        result = _apply_seen_filter(items, seen_urls=seen)
        assert len(result) == 3  # exactly 3 survived, no bypass
