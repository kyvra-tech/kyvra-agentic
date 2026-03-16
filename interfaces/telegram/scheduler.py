import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram import Bot
from agents.supervisor import SupervisorAgent, load_module
from interfaces.telegram.formatter import split_long_message
from config import ACTIVE_MODULE, REPORT_TIME, REPORT_CHAT_IDS, TIMEZONE

logger = logging.getLogger(__name__)


async def _send_daily_report(bot: Bot) -> None:
    if not REPORT_CHAT_IDS:
        logger.warning("[Scheduler] No REPORT_CHAT_IDS configured – skipping daily report.")
        return

    logger.info("[Scheduler] Generating daily report...")
    try:
        module = load_module(ACTIVE_MODULE)
        supervisor = SupervisorAgent(module)
        report = await supervisor.generate_report()
    except Exception as e:
        logger.error(f"[Scheduler] Report generation failed: {e}")
        return

    for chat_id in REPORT_CHAT_IDS:
        try:
            for chunk in split_long_message(report):
                await bot.send_message(chat_id=chat_id, text=chunk, parse_mode="Markdown")
            logger.info(f"[Scheduler] Report sent to {chat_id}")
        except Exception as e:
            logger.error(f"[Scheduler] Failed to send to {chat_id}: {e}")


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    hour, minute = REPORT_TIME.split(":")
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    scheduler.add_job(
        _send_daily_report,
        trigger=CronTrigger(hour=int(hour), minute=int(minute), timezone=TIMEZONE),
        args=[bot],
        id="daily_report",
        replace_existing=True,
    )
    logger.info(f"[Scheduler] Daily report scheduled at {REPORT_TIME} ({TIMEZONE})")
    return scheduler
