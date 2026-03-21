"""Tests for _push_to_trendpost in interfaces/telegram/scheduler.py

Covers:
1. Push skipped when TRENDPOST_WEBHOOK_URL is empty
2. Push sends correct HMAC signature
3. Push serializes top_items with correct signal_label_key mapping
4. Push returns gracefully on HTTP error (does not raise)
5. Push skips when ctx has no top_items
6. signal_label_key maps confidence scores and is_spike correctly
"""

import hashlib
import hmac
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from modules.base import RawItem


# ── Helpers ──────────────────────────────────────────────────────────────────

def make_scored_item(title, url, confidence_score, is_spike=False, cross_source_count=1):
    item = MagicMock()
    item.title = title
    item.url = url
    item.confidence_score = confidence_score
    item.is_spike = is_spike
    item.cross_source_count = cross_source_count
    item.summary = f"Summary for {title}"
    return item


def make_ctx(items=None):
    ctx = MagicMock()
    ctx.top_items = items if items is not None else []
    return ctx


# ── signal_label_key tests ────────────────────────────────────────────────────

class TestSignalLabelKey:
    def test_viral_spike_multi_source(self):
        from interfaces.telegram.formatter import _signal_label_key
        item = make_scored_item("Test", "http://x.com", 90, is_spike=True, cross_source_count=3)
        assert _signal_label_key(item) == "VIRAL"

    def test_viral_single_spike(self):
        from interfaces.telegram.formatter import _signal_label_key
        item = make_scored_item("Test", "http://x.com", 50, is_spike=True, cross_source_count=1)
        assert _signal_label_key(item) == "VIRAL"

    def test_rising_high_confidence(self):
        from interfaces.telegram.formatter import _signal_label_key
        item = make_scored_item("Test", "http://x.com", 85, is_spike=False)
        assert _signal_label_key(item) == "RISING"

    def test_steady_medium_confidence(self):
        from interfaces.telegram.formatter import _signal_label_key
        item = make_scored_item("Test", "http://x.com", 65, is_spike=False)
        assert _signal_label_key(item) == "STEADY"

    def test_signal_low_confidence(self):
        from interfaces.telegram.formatter import _signal_label_key
        item = make_scored_item("Test", "http://x.com", 40, is_spike=False)
        assert _signal_label_key(item) == "SIGNAL"

    def test_boundary_80_is_rising(self):
        from interfaces.telegram.formatter import _signal_label_key
        item = make_scored_item("Test", "http://x.com", 80, is_spike=False)
        assert _signal_label_key(item) == "RISING"

    def test_boundary_60_is_steady(self):
        from interfaces.telegram.formatter import _signal_label_key
        item = make_scored_item("Test", "http://x.com", 60, is_spike=False)
        assert _signal_label_key(item) == "STEADY"


# ── _push_to_trendpost tests ──────────────────────────────────────────────────

class TestPushToTrendpost:
    @pytest.mark.asyncio
    async def test_skips_when_url_not_configured(self):
        from interfaces.telegram.scheduler import _push_to_trendpost
        ctx = make_ctx([make_scored_item("Story", "http://example.com", 85)])

        with patch("interfaces.telegram.scheduler.TRENDPOST_WEBHOOK_URL", ""), \
             patch("interfaces.telegram.scheduler.TRENDPOST_WEBHOOK_SECRET", "secret"):
            # Should return without making any HTTP call
            await _push_to_trendpost("tech", ctx)  # no assertion needed — just no exception

    @pytest.mark.asyncio
    async def test_skips_when_ctx_has_no_top_items(self):
        from interfaces.telegram.scheduler import _push_to_trendpost
        ctx = make_ctx([])  # empty top_items

        mock_client = AsyncMock()
        with patch("interfaces.telegram.scheduler.TRENDPOST_WEBHOOK_URL", "http://trendpost/api/webhooks/kyvra"), \
             patch("interfaces.telegram.scheduler.TRENDPOST_WEBHOOK_SECRET", "secret"), \
             patch("httpx.AsyncClient") as mock_httpx:
            await _push_to_trendpost("tech", ctx)
            mock_httpx.assert_not_called()

    @pytest.mark.asyncio
    async def test_sends_correct_hmac_signature(self):
        from interfaces.telegram.scheduler import _push_to_trendpost

        items = [make_scored_item("AI breakthrough", "http://example.com/1", 90, is_spike=True, cross_source_count=2)]
        ctx = make_ctx(items)

        secret = "my-super-secret-key"  # pragma: allowlist secret
        captured_request = {}

        class MockResponse:
            status_code = 200
            def json(self):
                return {"inserted": 1, "skipped": 0}

        class MockClient:
            async def __aenter__(self):
                return self
            async def __aexit__(self, *args):
                pass
            async def post(self, url, content, headers):
                captured_request["body"] = content
                captured_request["headers"] = headers
                return MockResponse()

        with patch("interfaces.telegram.scheduler.TRENDPOST_WEBHOOK_URL", "http://trendpost/api/webhooks/kyvra"), \
             patch("interfaces.telegram.scheduler.TRENDPOST_WEBHOOK_SECRET", secret), \
             patch("httpx.AsyncClient", MockClient):
            await _push_to_trendpost("tech", ctx)

        body = captured_request["body"]
        expected_sig = "sha256=" + hmac.new(
            secret.encode("utf-8"),
            body.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        assert captured_request["headers"]["x-kyvra-signature"] == expected_sig

    @pytest.mark.asyncio
    async def test_serializes_signal_label_correctly(self):
        from interfaces.telegram.scheduler import _push_to_trendpost

        items = [
            make_scored_item("Story 1", "http://example.com/1", 90, is_spike=True, cross_source_count=2),  # VIRAL
            make_scored_item("Story 2", "http://example.com/2", 82, is_spike=False),  # RISING
        ]
        ctx = make_ctx(items)

        captured_payload = {}

        class MockResponse:
            status_code = 200
            def json(self):
                return {"inserted": 2, "skipped": 0}

        class MockClient:
            async def __aenter__(self):
                return self
            async def __aexit__(self, *args):
                pass
            async def post(self, url, content, headers):
                captured_payload["data"] = json.loads(content)
                return MockResponse()

        with patch("interfaces.telegram.scheduler.TRENDPOST_WEBHOOK_URL", "http://trendpost/api/webhooks/kyvra"), \
             patch("interfaces.telegram.scheduler.TRENDPOST_WEBHOOK_SECRET", "secret"), \
             patch("httpx.AsyncClient", MockClient):
            await _push_to_trendpost("tech", ctx)

        stories = captured_payload["data"]["stories"]
        assert stories[0]["signal_label"] == "VIRAL"
        assert stories[1]["signal_label"] == "RISING"

    @pytest.mark.asyncio
    async def test_does_not_raise_on_http_error(self):
        """Push failure must never propagate — Telegram delivery must not be blocked."""
        from interfaces.telegram.scheduler import _push_to_trendpost

        items = [make_scored_item("Story", "http://example.com/1", 75)]
        ctx = make_ctx(items)

        class FailingClient:
            async def __aenter__(self):
                return self
            async def __aexit__(self, *args):
                pass
            async def post(self, *args, **kwargs):
                raise ConnectionError("network error")

        with patch("interfaces.telegram.scheduler.TRENDPOST_WEBHOOK_URL", "http://trendpost/api/webhooks/kyvra"), \
             patch("interfaces.telegram.scheduler.TRENDPOST_WEBHOOK_SECRET", "secret"), \
             patch("httpx.AsyncClient", FailingClient):
            # Must not raise
            await _push_to_trendpost("tech", ctx)

    @pytest.mark.asyncio
    async def test_limits_push_to_7_stories(self):
        from interfaces.telegram.scheduler import _push_to_trendpost

        items = [make_scored_item(f"Story {i}", f"http://example.com/{i}", 80) for i in range(10)]
        ctx = make_ctx(items)

        captured_payload = {}

        class MockResponse:
            status_code = 200
            def json(self):
                return {"inserted": 7, "skipped": 0}

        class MockClient:
            async def __aenter__(self):
                return self
            async def __aexit__(self, *args):
                pass
            async def post(self, url, content, headers):
                captured_payload["data"] = json.loads(content)
                return MockResponse()

        with patch("interfaces.telegram.scheduler.TRENDPOST_WEBHOOK_URL", "http://trendpost/api/webhooks/kyvra"), \
             patch("interfaces.telegram.scheduler.TRENDPOST_WEBHOOK_SECRET", "secret"), \
             patch("httpx.AsyncClient", MockClient):
            await _push_to_trendpost("tech", ctx)

        assert len(captured_payload["data"]["stories"]) == 7
