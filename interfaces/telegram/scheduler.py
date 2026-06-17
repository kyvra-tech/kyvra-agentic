import logging
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram import Bot
from agents.graph_runner import GraphRunner
from interfaces.telegram.formatter import split_long_message, _signal_label_key
from config import REPORT_TIME, REPORT_CHAT_IDS, TIMEZONE

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

    for module_name in _ALL_MODULES:
        logger.info("[Scheduler] Scanning module: %s", module_name)
        try:
            runner = GraphRunner(module_name)
            state = await runner.quick_scan()
            top_items = state.get("top_items") or []
            if top_items:
                sections.append(_format_module_section(module_name, top_items))
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
