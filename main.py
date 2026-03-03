import logging
import asyncio
from telegram.ext import Application, CommandHandler
from config import TELEGRAM_BOT_TOKEN, ANTHROPIC_API_KEY
from bot.handlers import cmd_start, cmd_help, cmd_report, cmd_chat, error_handler
from bot.scheduler import setup_scheduler

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def validate_config() -> None:
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set in .env")
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY is not set in .env")


def main() -> None:
    validate_config()
    logger.info("Starting Kyvra bot...")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register command handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("report", cmd_report))
    app.add_handler(CommandHandler("chat", cmd_chat))
    app.add_error_handler(error_handler)

    # Setup daily report scheduler
    scheduler = setup_scheduler(app.bot)
    scheduler.start()

    logger.info("Bot is running. Press Ctrl+C to stop.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
