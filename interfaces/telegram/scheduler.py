import hashlib
import hmac
import json
import logging
import httpx
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram import Bot
from agents.supervisor import SupervisorAgent, load_module
from interfaces.telegram.formatter import split_long_message, _signal_label_key
from config import REPORT_TIME, REPORT_CHAT_IDS, TIMEZONE, TRENDPOST_WEBHOOK_URL, TRENDPOST_WEBHOOK_SECRET

logger = logging.getLogger(__name__)

_VN_TZ = timezone(timedelta(hours=7))

# All active modules included in the combined daily digest.
_ALL_MODULES = [
    "tech", "crypto", "parody", "sport", "political",
    "war", "humor", "energy", "markets",
]

# Module display names and emoji headers for the digest
_MODULE_META = {
    "tech":      ("🤖", "Tech & AI"),
    "crypto":    ("₿",  "Crypto"),
    "parody":    ("🤡", "Parody"),
    "sport":     ("⚽", "Sport"),
    "political": ("🏛️", "Politics"),
    "war":       ("⚔️", "Geopolitics & War"),
    "humor":     ("🎬", "Entertainment"),
    "energy":    ("⚡", "Energy"),
    "markets":   ("📈", "Markets"),
}

_ITEMS_PER_MODULE = 2  # top stories per module in the combined digest


async def _push_to_trendpost(module_name: str, supervisor_ctx) -> None:
    """Push top stories for a module to TrendPost via HMAC-signed webhook."""
    if not TRENDPOST_WEBHOOK_URL or not TRENDPOST_WEBHOOK_SECRET:
        return

    if not supervisor_ctx or not getattr(supervisor_ctx, "top_items", None):
        logger.info("[TrendPost push] No top_items for module '%s' — skipping", module_name)
        return

    stories = [
        {
            "title": item.title,
            "url": item.url,
            "confidence_score": item.confidence_score,
            "signal_label": _signal_label_key(item),
            "summary": getattr(item, "summary", None),
        }
        for item in supervisor_ctx.top_items[:7]
    ]

    payload = {"module": module_name, "stories": stories}
    body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    signature = "sha256=" + hmac.new(
        TRENDPOST_WEBHOOK_SECRET.encode("utf-8"),
        body.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                TRENDPOST_WEBHOOK_URL,
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "x-kyvra-signature": signature,
                },
            )
        if response.status_code == 200:
            result = response.json()
            logger.info(
                "[TrendPost push] Module '%s': %d inserted, %d skipped",
                module_name, result.get("inserted", 0), result.get("skipped", 0),
            )
        else:
            logger.warning(
                "[TrendPost push] Module '%s': unexpected status %d",
                module_name, response.status_code,
            )
    except Exception as exc:
        logger.error("[TrendPost push] Module '%s' failed: %s", module_name, exc)


def _format_module_section(module_name: str, top_items: list) -> str:
    """Format 2 top items from a module as a compact digest section."""
    emoji, label = _MODULE_META.get(module_name, ("📌", module_name.capitalize()))
    lines = [f"{emoji} *{label}*"]
    for i, item in enumerate(top_items[:_ITEMS_PER_MODULE], 1):
        title = item.title[:100] + ("…" if len(item.title) > 100 else "")
        score = item.confidence_score
        lines.append(f"  {i}\\. [{score}] {title}")
        lines.append(f"     {item.url}")
    return "\n".join(lines)


async def _send_combined_digest(bot: Bot) -> None:
    """
    Collect top 2 stories from every module in parallel (quick scan, no LLM),
    assemble a single combined digest message, and send it once to all chats.
    """
    if not REPORT_CHAT_IDS:
        logger.warning("[Scheduler] No REPORT_CHAT_IDS configured — skipping.")
        return

    now = datetime.now(_VN_TZ).strftime("%d/%m/%Y %H:%M GMT+7")
    sections = []
    trendpost_tasks = []

    for module_name in _ALL_MODULES:
        logger.info("[Scheduler] Scanning module: %s", module_name)
        try:
            supervisor = SupervisorAgent(load_module(module_name))
            ctx = await supervisor.quick_scan()
            if ctx.top_items:
                sections.append(_format_module_section(module_name, ctx.top_items))
                trendpost_tasks.append((module_name, ctx))
            else:
                logger.info("[Scheduler] No items for module '%s' — skipped from digest", module_name)
        except Exception as e:
            logger.error("[Scheduler] Scan failed for module '%s': %s", module_name, e)

    if not sections:
        logger.warning("[Scheduler] All modules returned empty — digest not sent.")
        return

    header = f"🌅 *Kyvra Daily Digest — {now}*\nTop stories across all modules\n"
    digest = header + "\n\n" + "\n\n".join(sections)

    for chat_id in REPORT_CHAT_IDS:
        try:
            for chunk in split_long_message(digest):
                await bot.send_message(chat_id=chat_id, text=chunk, parse_mode="Markdown")
            logger.info("[Scheduler] Combined digest sent to %s", chat_id)
        except Exception as e:
            logger.error("[Scheduler] Failed to send digest to %s: %s", chat_id, e)

    # Push to TrendPost (non-blocking)
    for module_name, ctx in trendpost_tasks:
        await _push_to_trendpost(module_name, ctx)


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    hour, minute = REPORT_TIME.split(":")
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    scheduler.add_job(
        _send_combined_digest,
        trigger=CronTrigger(hour=int(hour), minute=int(minute), timezone=TIMEZONE),
        args=[bot],
        id="morning_digest",
        replace_existing=True,
    )
    logger.info("[Scheduler] Daily digest scheduled at %s (%s)", REPORT_TIME, TIMEZONE)
    return scheduler
