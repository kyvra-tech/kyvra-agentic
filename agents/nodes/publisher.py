"""
publisher_node — LangGraph node: mark stories as seen + push TrendPost webhook.

Reads:  state["top_items"], state["module_name"], state["report_text"]
Writes: state["published"]

Extracted from SupervisorAgent.generate_report_with_ctx() and the TrendPost
push logic in interfaces/telegram/scheduler.py.

This node only runs for mode=="full" and mode=="topic" (skipped by router for
"quick" and "breaking").
"""

import hashlib
import hmac
import json
import logging
import time

import httpx

from agents.state import KyvraState
from config import (
    TRENDPOST_WEBHOOK_URL,
    TRENDPOST_WEBHOOK_SECRET,
)
import services.memory as memory

logger = logging.getLogger(__name__)


def _sign(body: bytes, secret: str) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


async def run(state: KyvraState) -> dict:
    top_items = state.get("top_items") or []
    module_name = state["module_name"]

    # Mark delivered items as seen (story continuity)
    if top_items:
        memory.mark_seen([i.url for i in top_items], module_name)
        logger.info("[publisher] Marked %d items as seen for module '%s'.", len(top_items), module_name)

    # Push TrendPost webhook (optional — silently skipped if not configured)
    if TRENDPOST_WEBHOOK_URL and TRENDPOST_WEBHOOK_SECRET and top_items:
        stories = [
            {
                "title":            item.title,
                "url":              item.url,
                "source":           item.source,
                "summary":          item.summary,
                "confidence_score": item.confidence_score,
                "is_spike":         item.is_spike,
            }
            for item in top_items
        ]
        payload = {
            "stories":     stories,
            "module":      module_name,
            "pushed_date": time.strftime("%Y-%m-%d"),
        }
        body = json.dumps(payload).encode()
        sig = _sign(body, TRENDPOST_WEBHOOK_SECRET)

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    TRENDPOST_WEBHOOK_URL,
                    content=body,
                    headers={
                        "Content-Type":      "application/json",
                        "x-kyvra-signature": sig,
                    },
                )
            logger.info("[publisher] TrendPost webhook → %d", resp.status_code)
        except Exception as e:
            logger.warning("[publisher] TrendPost webhook failed: %s", e)

    return {"published": True}
