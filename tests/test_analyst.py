"""Unit tests for AnalystAgent scoring functions.

All functions under test are pure Python with no I/O — no mocking needed.
"""

import time
import pytest
from modules.base import RawItem
from agents.analyst import (
    _engagement_score,
    _relevance_score,
    _cross_source_boost,
    _is_spike,
    _recency_score,
    _velocity_score,
    score_item,
)
from modules.tech.config import X_SPIKE_THRESHOLD, GITHUB_STARS_SPIKE


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_item(
    source="X - AI Leaders",
    score=100,
    comments=10,
    title="OpenAI releases new model",
    summary="gpt update from openai",
    published_at="",
    authority_score=15,
    cross_source_count=1,
) -> RawItem:
    return RawItem(
        title=title,
        url="https://x.com/test",
        source=source,
        published_at=published_at,
        summary=summary,
        score=score,
        comments=comments,
        authority_score=authority_score,
        cross_source_count=cross_source_count,
    )


KEYWORDS = ["openai", "gpt", "claude", "llm", "agent", "anthropic"]


# ── _engagement_score ─────────────────────────────────────────────────────────

class TestEngagementScore:
    def test_github_caps_at_40(self):
        item = make_item(source="GitHub Trending", score=9999)
        assert _engagement_score(item) == 40

    def test_github_zero_score(self):
        item = make_item(source="GitHub Trending", score=0)
        assert _engagement_score(item) == 0

    def test_github_proportional(self):
        item = make_item(source="GitHub Trending", score=30)
        assert _engagement_score(item) == 10  # int(30/3)

    def test_x_caps_likes_at_35(self):
        item = make_item(source="X - AI Trending", score=99999, comments=0)
        assert _engagement_score(item) == 35

    def test_x_comments_add_up_to_5(self):
        item = make_item(source="X - AI Trending", score=0, comments=999)
        assert _engagement_score(item) == 5

    def test_x_combined_cap(self):
        item = make_item(source="X - AI Trending", score=99999, comments=999)
        assert _engagement_score(item) == 40

    def test_x_authority_floor_applied(self):
        # AI Leaders with 0 likes should hit the authority floor (15), not 0
        item = make_item(source="X - AI Leaders", score=0, comments=0)
        score = _engagement_score(item)
        assert score == 15  # _AUTHORITY_ENGAGEMENT_FLOOR

    def test_x_non_authority_no_floor(self):
        item = make_item(source="X - AI Trending", score=0, comments=0)
        assert _engagement_score(item) == 0

    def test_rss_baseline(self):
        item = make_item(source="TechCrunch RSS", score=0, comments=0)
        assert _engagement_score(item) == 15


# ── _relevance_score ──────────────────────────────────────────────────────────

class TestRelevanceScore:
    def test_zero_keyword_hits_returns_10(self):
        item = make_item(title="Unrelated topic", summary="nothing here")
        assert _relevance_score(item, KEYWORDS) == 10

    def test_one_hit_returns_10(self):
        item = make_item(title="openai news", summary="nothing else")
        assert _relevance_score(item, KEYWORDS) == 10

    def test_two_hits_returns_12(self):
        item = make_item(title="openai releases gpt", summary="nothing else")
        assert _relevance_score(item, KEYWORDS) == 12

    def test_three_hits_returns_14(self):
        item = make_item(title="openai gpt claude", summary="nothing")
        assert _relevance_score(item, KEYWORDS) == 14

    def test_caps_at_20(self):
        item = make_item(title="openai gpt claude llm agent", summary="anthropic")
        assert _relevance_score(item, KEYWORDS) == 20

    def test_case_insensitive(self):
        item = make_item(title="OpenAI GPT News", summary="")
        assert _relevance_score(item, KEYWORDS) == 12

    def test_empty_keywords(self):
        item = make_item(title="openai gpt", summary="")
        assert _relevance_score(item, []) == 10


# ── _cross_source_boost ───────────────────────────────────────────────────────

class TestCrossSourceBoost:
    def test_single_source_no_boost(self):
        item = make_item(cross_source_count=1)
        assert _cross_source_boost(item) == 0

    def test_two_sources_gives_boost(self):
        item = make_item(cross_source_count=2)
        assert _cross_source_boost(item) == 10

    def test_many_sources_same_boost(self):
        item = make_item(cross_source_count=10)
        assert _cross_source_boost(item) == 10


# ── _is_spike ─────────────────────────────────────────────────────────────────

class TestIsSpike:
    def test_x_spike_above_threshold(self):
        item = make_item(source="X - AI Leaders", score=X_SPIKE_THRESHOLD)
        assert _is_spike(item, GITHUB_STARS_SPIKE, X_SPIKE_THRESHOLD) is True

    def test_x_no_spike_below_threshold(self):
        item = make_item(source="X - AI Leaders", score=X_SPIKE_THRESHOLD - 1)
        assert _is_spike(item, GITHUB_STARS_SPIKE, X_SPIKE_THRESHOLD) is False

    def test_github_spike_above_threshold(self):
        item = make_item(source="GitHub Trending", score=GITHUB_STARS_SPIKE)
        assert _is_spike(item, GITHUB_STARS_SPIKE, X_SPIKE_THRESHOLD) is True

    def test_github_no_spike_below_threshold(self):
        item = make_item(source="GitHub Trending", score=GITHUB_STARS_SPIKE - 1)
        assert _is_spike(item, GITHUB_STARS_SPIKE, X_SPIKE_THRESHOLD) is False

    def test_rss_never_spikes(self):
        item = make_item(source="TechCrunch RSS", score=999999)
        assert _is_spike(item, GITHUB_STARS_SPIKE, X_SPIKE_THRESHOLD) is False


# ── _recency_score ────────────────────────────────────────────────────────────

class TestRecencyScore:
    def test_fresh_item_max_score(self):
        ts = str(int(time.time() - 3600))  # 1 hour ago
        item = make_item(published_at=ts)
        assert _recency_score(item.published_at) == 20

    def test_day_old_item_mid_score(self):
        ts = str(int(time.time() - 12 * 3600))  # 12 hours ago
        item = make_item(published_at=ts)
        assert _recency_score(item.published_at) == 13

    def test_old_item_zero_score(self):
        ts = str(int(time.time() - 72 * 3600))  # 3 days ago
        item = make_item(published_at=ts)
        assert _recency_score(item.published_at) == 0

    def test_missing_timestamp_default(self):
        assert _recency_score("") == 5

    def test_iso_timestamp_parsed(self):
        ts = "2020-01-01T00:00:00Z"  # very old → 0
        assert _recency_score(ts) == 0


# ── score_item (integration of components) ────────────────────────────────────

class TestScoreItem:
    def test_score_capped_at_100(self):
        # Max everything: high authority, high engagement, fresh, multi-keyword, cross-source
        item = make_item(
            source="X - AI Leaders",
            score=99999,
            comments=999,
            title="openai gpt claude llm agent",
            summary="anthropic model",
            published_at=str(int(time.time())),
            authority_score=20,
            cross_source_count=3,
        )
        result = score_item(item, KEYWORDS)
        assert result.confidence_score <= 100

    def test_score_non_negative(self):
        item = make_item(
            source="Unknown RSS",
            score=0,
            comments=0,
            title="Unrelated news",
            summary="nothing",
            published_at="",
            authority_score=0,
            cross_source_count=1,
        )
        result = score_item(item, KEYWORDS)
        assert result.confidence_score >= 0

    def test_cross_source_raises_score(self):
        base = make_item(cross_source_count=1)
        boosted = make_item(cross_source_count=2)
        assert score_item(boosted, KEYWORDS).confidence_score == (
            score_item(base, KEYWORDS).confidence_score + 10
        )

    def test_spike_flag_propagated(self):
        item = make_item(source="X - AI Leaders", score=X_SPIKE_THRESHOLD)
        result = score_item(item, KEYWORDS)
        assert result.is_spike is True

    def test_fields_mapped_correctly(self):
        item = make_item(source="GitHub Trending", score=50, cross_source_count=2)
        result = score_item(item, KEYWORDS)
        assert result.title == item.title
        assert result.url == item.url
        assert result.source == item.source
        assert result.raw_score == 50
        assert result.cross_source_count == 2


# ── _velocity_score (likes/hour normalization) ────────────────────────────────

class TestVelocityScore:
    """velocity_score uses likes/hour, not time brackets.
    Tiers: >=300/hr → 10, >=100/hr → 7, >=50/hr → 4, else 0.
    """

    def _x_item(self, score: int, age_hours: float) -> RawItem:
        """Make an X item with a synthetic timestamp `age_hours` ago."""
        ts = int(time.time() - age_hours * 3600)
        return make_item(source="X - AI Trending", score=score, published_at=str(ts))

    def test_non_x_source_returns_zero(self):
        item = make_item(source="GitHub Trending", score=9999, published_at=str(int(time.time())))
        assert _velocity_score(item) == 0

    def test_no_timestamp_returns_zero(self):
        item = make_item(source="X - AI Trending", score=9999, published_at="")
        assert _velocity_score(item) == 0

    def test_tier_high_300_lph(self):
        # 1200 likes in 2 hours ≈ 600/hr (well above 300 threshold) → 10pts
        item = self._x_item(score=1200, age_hours=2.0)
        assert _velocity_score(item) == 10

    def test_tier_mid_100_lph(self):
        # 500 likes in 2 hours ≈ 250/hr (above 100, below 300 threshold) → 7pts
        item = self._x_item(score=500, age_hours=2.0)
        assert _velocity_score(item) == 7

    def test_tier_low_50_lph(self):
        # 200 likes in 2 hours ≈ 100/hr edge → use 300 likes in 2h ≈ 150/hr, still 7pts
        # Use unambiguous value: 200 likes / 2h ≈ 100/hr → should be 7pts (>= 100)
        # Actually test the 50-99/hr range: 150 likes / 2h = 75/hr → 4pts
        item = self._x_item(score=150, age_hours=2.0)
        assert _velocity_score(item) == 4

    def test_tier_below_threshold(self):
        # 40 likes in 2 hours = 20/hr → 0pts
        item = self._x_item(score=40, age_hours=2.0)
        assert _velocity_score(item) == 0

    def test_age_zero_no_division_error(self):
        # Just-posted tweet: age_hours effectively 0 → floor at 0.5h, no ZeroDivisionError
        ts = str(int(time.time()))
        item = make_item(source="X - AI Trending", score=1000, published_at=ts)
        result = _velocity_score(item)
        assert isinstance(result, int)
        assert result >= 0

    def test_momentum_beats_raw_count(self):
        # 300 likes in 1h (300/hr) should score more than 500 likes in 6h (83/hr)
        fast = self._x_item(score=300, age_hours=1.0)
        slow = self._x_item(score=500, age_hours=6.0)
        assert _velocity_score(fast) > _velocity_score(slow)
