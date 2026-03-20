import sys
import logging
import asyncio
from telegram.ext import Application, CommandHandler
from config import TELEGRAM_BOT_TOKEN, XAI_API_KEY, ACTIVE_MODULE
from agents.supervisor import load_module
from interfaces.telegram.handlers import (
    cmd_start, cmd_help, cmd_report, cmd_chat, error_handler,
    cmd_update, cmd_breaking, cmd_topic, cmd_module, cmd_thread, cmd_brief,
    cmd_status, cmd_newsletter, cmd_script, cmd_setvoice,
)
from interfaces.telegram.scheduler import setup_scheduler

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def validate_config() -> None:
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set in .env")
    if not XAI_API_KEY:
        raise RuntimeError("XAI_API_KEY is not set in .env")


def main() -> None:
    validate_config()

    if "--once" in sys.argv:
        async def run_once():
            from agents.supervisor import SupervisorAgent, load_module
            supervisor = SupervisorAgent(load_module(ACTIVE_MODULE))
            report = await supervisor.generate_report()
            print(report)
        asyncio.run(run_once())
        return

    logger.info("Starting Kyvra bot...")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register command handlers
    app.add_handler(CommandHandler("start",      cmd_start))
    app.add_handler(CommandHandler("help",       cmd_help))
    app.add_handler(CommandHandler("report",     cmd_report))
    app.add_handler(CommandHandler("update",     cmd_update))
    app.add_handler(CommandHandler("breaking",   cmd_breaking))
    app.add_handler(CommandHandler("topic",      cmd_topic))
    app.add_handler(CommandHandler("brief",      cmd_brief))
    app.add_handler(CommandHandler("thread",     cmd_thread))
    app.add_handler(CommandHandler("newsletter", cmd_newsletter))
    app.add_handler(CommandHandler("script",     cmd_script))
    app.add_handler(CommandHandler("status",     cmd_status))
    app.add_handler(CommandHandler("chat",       cmd_chat))
    app.add_handler(CommandHandler("setvoice",   cmd_setvoice))
    app.add_handler(CommandHandler("module",     cmd_module))
    app.add_error_handler(error_handler)

    # Setup daily report scheduler
    scheduler = setup_scheduler(app.bot)
    scheduler.start()
    logger.info(f"[Startup] Active module: {ACTIVE_MODULE}, sources: {len(load_module(ACTIVE_MODULE).get_sources())}")

    logger.info("Bot is running. Press Ctrl+C to stop.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
