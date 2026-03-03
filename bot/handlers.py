import logging
from telegram import Update
from telegram.ext import ContextTypes
from agents.supervisor import SupervisorAgent, load_module
from agents.content_writer import chat_with_claude
from bot.formatter import split_long_message
from config import ACTIVE_MODULE

logger = logging.getLogger(__name__)

# Per-user chat history for /chat command (in-memory, resets on restart)
_chat_histories: dict[int, list[dict]] = {}
MAX_HISTORY = 10  # keep last N turns


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "👋 Xin chào! Mình là *Kyvra* – AI content agent cho Tech/AI/Indie Dev.\n\n"
        "Mình theo dõi tin tức từ HackerNews, GitHub, Anthropic, OpenAI, DeepMind và tóm tắt "
        "mọi thứ cho bạn mỗi sáng 8h – kèm gợi ý content angle.\n\n"
        "*Lệnh có sẵn:*\n"
        "/report – Tạo báo cáo ngay bây giờ\n"
        "/chat [tin nhắn] – Chat với AI về tech/AI news\n"
        "/help – Hiển thị hướng dẫn này\n\n"
        "Gõ `/report` để xem thử nhé! 🚀"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "*Kyvra – AI Tech Content Agent*\n\n"
        "*/report* – Tạo Daily Tech Report (top 7 insights + content angles)\n"
        "*/chat [câu hỏi]* – Chat với AI về tech news\n"
        "  Ví dụ: `/chat OpenAI hôm nay có gì mới không?`\n"
        "  Ví dụ: `/chat Viết thread về Claude 4`\n"
        "  Ví dụ: `/chat So sánh Cursor vs Copilot`\n\n"
        "Report tự động gửi lúc *8:00 sáng* mỗi ngày (GMT+7)."
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = await update.message.reply_text("⏳ Đang thu thập tin tức và viết report... (30-60 giây)")

    try:
        module = load_module(ACTIVE_MODULE)
        supervisor = SupervisorAgent(module)
        report = await supervisor.generate_report()
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        await msg.edit_text(f"❌ Lỗi khi tạo report: {e}")
        return

    await msg.delete()
    for chunk in split_long_message(report):
        await update.message.reply_text(chunk, parse_mode="Markdown")


async def cmd_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_message = " ".join(context.args) if context.args else ""

    if not user_message:
        await update.message.reply_text(
            "Bạn muốn hỏi gì? Ví dụ:\n`/chat OpenAI hôm nay có gì mới?`",
            parse_mode="Markdown"
        )
        return

    # Load this user's chat history
    history = _chat_histories.get(user_id, [])

    typing_msg = await update.message.reply_text("💭 Đang suy nghĩ...")

    from modules.tech.prompts import CHAT_SYSTEM_PROMPT
    reply = await chat_with_claude(user_message, CHAT_SYSTEM_PROMPT, history)

    # Update history (trim to last MAX_HISTORY turns)
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": reply})
    _chat_histories[user_id] = history[-(MAX_HISTORY * 2):]

    await typing_msg.delete()
    for chunk in split_long_message(reply):
        await update.message.reply_text(chunk, parse_mode="Markdown")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Telegram error: {context.error}", exc_info=context.error)
