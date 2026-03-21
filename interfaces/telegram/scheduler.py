import hashlib
import hmac
import json
import logging
import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram import Bot
from agents.supervisor import generate_report_for_module_with_ctx
from interfaces.telegram.formatter import split_long_message, _signal_label_key
from config import REPORT_TIME, REPORT_CHAT_IDS, TIMEZONE, TRENDPOST_WEBHOOK_URL, TRENDPOST_WEBHOOK_SECRET

logger = logging.getLogger(__name__)

# All active modules get a report on every scheduled run, sent serially.
_ALL_MODULES = ["tech", "crypto", "vietnam", "indie"]


async def _push_to_trendpost(module_name: str, supervisor_ctx) -> None:
    """
    Push top stories for a module to TrendPost via HMAC-signed webhook.
    Called from _send_all_module_reports after each module report is generated.

    Only runs when TRENDPOST_WEBHOOK_URL and TRENDPOST_WEBHOOK_SECRET are configured.
    Failures are logged but never raise — Telegram delivery must not be blocked.
    """
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


async def _send_all_module_reports(bot: Bot) -> None:
    """Generate and send reports for all modules to all configured chats, serially."""
    if not REPORT_CHAT_IDS:
        logger.warning("[Scheduler] No REPORT_CHAT_IDS configured — skipping.")
        return

    for module_name in _ALL_MODULES:
        logger.info("[Scheduler] Generating report for module: %s", module_name)
        ctx = None
        try:
            report, ctx = await generate_report_for_module_with_ctx(module_name)
        except Exception as e:
            logger.error("[Scheduler] Report failed for module '%s': %s", module_name, e)
            continue  # other modules still run

        for chat_id in REPORT_CHAT_IDS:
            try:
                for chunk in split_long_message(report):
                    await bot.send_message(chat_id=chat_id, text=chunk, parse_mode="Markdown")
                logger.info("[Scheduler] %s report sent to %s", module_name, chat_id)
            except Exception as e:
                logger.error("[Scheduler] Failed to send %s report to %s: %s", module_name, chat_id, e)

        # Push top stories to TrendPost (non-blocking — failures are logged only)
        await _push_to_trendpost(module_name, ctx)


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    hour, minute = REPORT_TIME.split(":")
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    scheduler.add_job(
        _send_all_module_reports,
        trigger=CronTrigger(hour=int(hour), minute=int(minute), timezone=TIMEZONE),
        args=[bot],
        id="morning_digest",
        replace_existing=True,
    )
    logger.info("[Scheduler] Morning digest scheduled at %s (%s)", REPORT_TIME, TIMEZONE)
    scheduler.add_job(
        _send_all_module_reports,
        trigger=CronTrigger(hour=20, minute=0, timezone=TIMEZONE),
        args=[bot],
        id="evening_digest",
        replace_existing=True,
    )
    logger.info("[Scheduler] Evening digest scheduled at 20:00 (%s)", TIMEZONE)
    return scheduler
