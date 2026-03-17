import logging
from telegram import Update
from telegram.ext import ContextTypes
from agents.supervisor import SupervisorAgent, load_module
from agents.content_writer import chat_with_llm
from interfaces.telegram.formatter import split_long_message, format_update, format_breaking
from config import ACTIVE_MODULE

logger = logging.getLogger(__name__)

# Runtime module state — starts from .env, changed by /module command without restart
_active_module: str = ACTIVE_MODULE
AVAILABLE_MODULES = ["tech", "crypto"]

# Per-user chat history for /chat command (in-memory, resets on restart)
_chat_histories: dict[int, list[dict]] = {}
MAX_HISTORY = 10  # keep last N turns


def _get_module():
    """Return a fresh module instance using the current runtime selection."""
    return load_module(_active_module)


async def cmd_module(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/module [name] — switch active module at runtime, no restart needed."""
    global _active_module

    requested = context.args[0].lower().strip() if context.args else ""

    # No argument → show current status
    if not requested:
        options = " | ".join(f"`{m}`" for m in AVAILABLE_MODULES)
        await update.message.reply_text(
            f"🧩 Active module: *{_active_module}*\n\nAvailable: {options}\n\nUsage: `/module crypto`",
            parse_mode="Markdown",
        )
        return

    if requested not in AVAILABLE_MODULES:
        options = " | ".join(f"`{m}`" for m in AVAILABLE_MODULES)
        await update.message.reply_text(
            f"❌ Unknown module: `{requested}`\n\nAvailable: {options}",
            parse_mode="Markdown",
        )
        return

    if requested == _active_module:
        await update.message.reply_text(
            f"✅ Already on *{_active_module}* module.",
            parse_mode="Markdown",
        )
        return

    _active_module = requested
    logger.info(f"[Module] Switched to '{_active_module}' by user {update.effective_user.id}")

    # Clear all chat histories — old context is invalid for the new module
    _chat_histories.clear()

    await update.message.reply_text(
        f"✅ Switched to *{_active_module}* module.\nChat history cleared. Run `/report` for today's briefing.",
        parse_mode="Markdown",
    )


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "👋 Hey! I'm *Kyvra* – your AI content agent for Tech, AI & Crypto.\n\n"
        "I monitor X/Twitter, GitHub Trending, top blogs and crypto media, "
        "then distill it into a daily briefing with content angles every morning at 8 AM.\n\n"
        "*Commands:*\n"
        "/update – Fast news scan right now (no AI, ~10 sec)\n"
        "/breaking – Spike alerts only\n"
        "/topic [kw] – Report scoped to one topic\n"
        "/report – Full AI-written daily report\n"
        "/chat [msg] – Chat about today's news\n"
        "/module [tech|crypto] – Switch focus module\n\n"
        "Try `/update` for a quick check! ⚡"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        f"*Kyvra – AI Content Agent* (module: *{_active_module}*)\n\n"
        "⚡ */update* – Fast scan, top scored items, no AI writing (~10 sec)\n"
        "🚨 */breaking* – Spike items only (viral X tweets, trending signals)\n"
        "🔍 */topic [keyword]* – AI report scoped to one topic\n"
        "   e.g. `/topic openai` `/topic bitcoin` `/topic defi`\n"
        "📋 */report* – Full daily report with content angles (30-60 sec)\n"
        "💬 */chat [question]* – Chat about today's news\n"
        "   e.g. `/chat What's new with OpenAI today?`\n"
        "🧩 */module [tech|crypto]* – Switch active module\n\n"
        "📅 Auto-report every day at *8:00 AM* (GMT+7)"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = await update.message.reply_text("⏳ Gathering news and writing report... (30-60 sec)")

    try:
        supervisor = SupervisorAgent(_get_module())
        report = await supervisor.generate_report()
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        await msg.edit_text("❌ Could not generate report. Please try again later.")
        return

    await msg.delete()
    for chunk in split_long_message(report):
        await update.message.reply_text(chunk, parse_mode="Markdown")


async def cmd_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/update — fast scan, no LLM, shows top scored items immediately."""
    msg = await update.message.reply_text("⚡ Scanning latest news... (no AI writing, ~10 sec)")
    try:
        supervisor = SupervisorAgent(_get_module())
        ctx = await supervisor.quick_scan()
    except Exception as e:
        logger.error(f"Quick scan failed: {e}")
        await msg.edit_text("❌ Scan failed. Please try again.")
        return

    total = len(ctx.raw_items)
    text = format_update(ctx.top_items, total)
    await msg.delete()
    await update.message.reply_text(text, disable_web_page_preview=True)


async def cmd_breaking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/breaking — only spike items, instant alert, no LLM."""
    msg = await update.message.reply_text("🚨 Checking for spikes...")
    try:
        supervisor = SupervisorAgent(_get_module())
        ctx = await supervisor.quick_scan()
    except Exception as e:
        logger.error(f"Breaking scan failed: {e}")
        await msg.edit_text("❌ Scan failed. Please try again.")
        return

    spikes = [i for i in ctx.scored_items if i.is_spike]
    text = format_breaking(spikes)
    await msg.delete()
    await update.message.reply_text(text, disable_web_page_preview=True)


async def cmd_topic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/topic [keyword] — full AI report scoped to one topic."""
    topic = " ".join(context.args)[:200].replace("\n", " ").strip() if context.args else ""
    if not topic:
        await update.message.reply_text(
            "Usage: `/topic [keyword]`\nExamples:\n`/topic openai`\n`/topic bitcoin`\n`/topic defi`",
            parse_mode="Markdown",
        )
        return

    msg = await update.message.reply_text(f"🔍 Finding news about *{topic}*...", parse_mode="Markdown")
    try:
        supervisor = SupervisorAgent(_get_module())
        report = await supervisor.generate_report_for_topic(topic)
    except Exception as e:
        logger.error(f"Topic report failed for '{topic}': {e}")
        await msg.edit_text("❌ Could not generate report. Please try again.")
        return

    await msg.delete()
    for chunk in split_long_message(report):
        await update.message.reply_text(chunk, parse_mode="Markdown")


async def cmd_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_message = " ".join(context.args)[:500].replace("\n", " ").strip() if context.args else ""

    if not user_message:
        await update.message.reply_text(
            "What do you want to ask? Example:\n`/chat What's new with OpenAI today?`",
            parse_mode="Markdown"
        )
        return

    history = _chat_histories.get(user_id, [])
    typing_msg = await update.message.reply_text("💭 Thinking...")

    reply = await chat_with_llm(user_message, _get_module().get_chat_system_prompt(), history)

    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": reply})
    _chat_histories[user_id] = history[-(MAX_HISTORY * 2):]

    await typing_msg.delete()
    for chunk in split_long_message(reply):
        await update.message.reply_text(chunk, parse_mode="Markdown")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Telegram error: {context.error}", exc_info=context.error)
