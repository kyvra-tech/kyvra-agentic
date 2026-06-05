"""
writer_node — LangGraph node: call LLM to produce the report / thread / brief / etc.

Reads:  state["top_items"], state["trend_heatmap"], state["module_name"],
        state["content_format"], state["content_rank"]
Writes: state["report_text"]

The actual LLM call is delegated to services/llm_provider.py (Phase 4).
Until the provider abstraction is in place we fall back to services/llm
directly — the switch is transparent to this node.
"""

import logging

from agents.state import KyvraState
from agents.registry import load_module
import services.memory as memory

logger = logging.getLogger(__name__)

# Max tokens per content format
_MAX_TOKENS: dict[str, int] = {
    "report":     2000,
    "thread":     1200,
    "brief":       400,
    "newsletter":  800,
    "script":      600,
    "tweet_hook":  160,
}


def _item_dict(item) -> dict:
    return {
        "title":            item.title,
        "url":              item.url,
        "source":           item.source,
        "published_at":     item.published_at,
        "summary":          item.summary,
        "confidence_score": item.confidence_score,
        "is_spike":         item.is_spike,
        "raw_score":        item.raw_score,
    }


async def run(state: KyvraState) -> dict:
    top_items = state.get("top_items") or []
    trend_heatmap = state.get("trend_heatmap") or ""
    module_name = state["module_name"]
    fmt = state.get("content_format") or "report"
    rank = max(1, state.get("content_rank") or 1)
    errors = list(state.get("errors") or [])

    if not top_items:
        return {"report_text": "No scored items today. Try again later! 🤷", "errors": errors}

    module = load_module(module_name)
    max_tokens = _MAX_TOKENS.get(fmt, 2000)

    # Build enriched payload for the prompt
    enriched = [
        {**_item_dict(item), "trend_heatmap": trend_heatmap}
        for item in top_items
    ]

    # Pick the right prompt builder
    clamped_rank = max(1, min(rank, len(top_items)))
    selected = _item_dict(top_items[clamped_rank - 1])

    try:
        if fmt == "report":
            prompt = module.get_report_prompt(enriched)
        elif fmt == "thread":
            prompt = module.get_thread_prompt(selected)
        elif fmt == "brief":
            payload = [_item_dict(i) for i in top_items[:3]]
            prompt = module.get_brief_prompt(payload)
        elif fmt == "newsletter":
            prompt = module.get_newsletter_prompt(selected)
        elif fmt == "script":
            prompt = module.get_script_prompt(selected)
        else:
            prompt = module.get_report_prompt(enriched)
    except Exception as e:
        msg = f"writer: prompt build failed: {e}"
        errors.append(msg)
        logger.error("[writer] %s", msg)
        return {"report_text": "Could not generate content right now. Try again later! 🤷", "errors": errors}

    logger.info("[writer] Calling LLM (format=%s, items=%d, max_tokens=%d)...", fmt, len(top_items), max_tokens)

    try:
        from services.llm_provider import get_content_provider
        text = await get_content_provider().complete(prompt, max_tokens=max_tokens)
        logger.info("[writer] LLM call succeeded.")
    except Exception as e:
        msg = f"writer: LLM call failed: {e}"
        errors.append(msg)
        logger.error("[writer] %s", msg)
        text = "Could not generate report right now. Try again later! 🤷"

    return {"report_text": text, "errors": errors}
