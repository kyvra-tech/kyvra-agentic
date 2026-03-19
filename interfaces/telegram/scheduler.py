import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram import Bot
from agents.supervisor import generate_report_for_module
from interfaces.telegram.formatter import split_long_message
from config import REPORT_TIME, REPORT_CHAT_IDS, TIMEZONE

logger = logging.getLogger(__name__)

# All active modules get a report on every scheduled run, sent serially.
_ALL_MODULES = ["tech", "crypto", "vietnam", "indie"]


async def _send_all_module_reports(bot: Bot) -> None:
    """Generate and send reports for all modules to all configured chats, serially."""
    if not REPORT_CHAT_IDS:
        logger.warning("[Scheduler] No REPORT_CHAT_IDS configured — skipping.")
        return

    for module_name in _ALL_MODULES:
        logger.info("[Scheduler] Generating report for module: %s", module_name)
        try:
            report = await generate_report_for_module(module_name)
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
