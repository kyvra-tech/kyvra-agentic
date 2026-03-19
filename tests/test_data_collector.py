"""Unit tests for DataCollectorAgent dedup logic.

_dedup_with_cross_source is pure Python — no I/O, no mocking needed.
"""

import pytest
from modules.base import RawItem
from agents.data_collector import _dedup_with_cross_source


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_item(
    title="Test story",
    url="https://example.com/story",
    source="X - AI Leaders",
    authority_score=15,
) -> RawItem:
    return RawItem(
        title=title,
        url=url,
        source=source,
        published_at="2026-01-01T00:00:00Z",
        summary="test summary",
        authority_score=authority_score,
    )


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
