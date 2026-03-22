import hashlib
import hmac
import json
import logging
import random
import string
from datetime import datetime, timedelta, timezone

import httpx
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from agents.supervisor import SupervisorAgent, load_module
from agents.content_writer import chat_with_llm
from interfaces.telegram.formatter import split_long_message, format_update, format_breaking
from config import ACTIVE_MODULE, TRENDPOST_API_URL, TRENDPOST_WEBHOOK_SECRET
import services.memory as memory

logger = logging.getLogger(__name__)

# Runtime module state — starts from .env, changed by /module command without restart
_active_module: str = ACTIVE_MODULE
AVAILABLE_MODULES = ["tech", "crypto", "vietnam", "indie"]

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
            f"🧩 Active module: {_active_module}\n\nAvailable: {options}\n\nUsage: /module crypto",
        )
        return

    if requested not in AVAILABLE_MODULES:
        options = " | ".join(f"`{m}`" for m in AVAILABLE_MODULES)
        await update.message.reply_text(
            f"❌ Unknown module: {requested}\n\nAvailable: {options}",
        )
        return

    if requested == _active_module:
        await update.message.reply_text(
            f"✅ Already on {_active_module} module.",
        )
        return

    _active_module = requested
    logger.info(f"[Module] Switched to '{_active_module}' by user {update.effective_user.id}")

    # Clear all chat histories — old context is invalid for the new module
    _chat_histories.clear()

    await update.message.reply_text(
        f"✅ Switched to {_active_module} module.\nChat history cleared. Run /report for today's briefing.",
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
        "/brief – 3-bullet summary, ready to share\n"
        "/thread – 7-tweet thread from today's top story\n"
        "/newsletter – Newsletter section from today's top story\n"
        "/script – TikTok/Reels voiceover script\n"
        "/status – Source health & item count check\n"
        "/chat [msg] – Chat about today's news\n"
        "/setvoice [description] – Set your writing style/voice\n"
        "/module [tech|crypto|vietnam|indie] – Switch focus module\n"
        "/link – Link this Telegram to your TrendPost account (enables auto-post)\n\n"
        "Try `/update` for a quick check! ⚡"
    )
    await update.message.reply_text(text)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        f"*Kyvra – AI Content Agent* (module: *{_active_module}*)\n\n"
        "⚡ */update* – Fast scan, top scored items, no AI writing (~10 sec)\n"
        "🚨 */breaking* – Spike items only (viral X tweets, trending signals)\n"
        "🔍 */topic [keyword]* – AI report scoped to one topic\n"
        "   e.g. `/topic openai` `/topic bitcoin` `/topic defi`\n"
        "📋 */report* – Full daily report with content angles (30-60 sec)\n"
        "⚡ */brief* – 3-bullet summary, screenshot-ready\n"
        "🧵 */thread* – 7-tweet X thread from today's top story\n"
        "📰 */newsletter* – Newsletter section from today's top story\n"
        "🎬 */script* – TikTok/Reels voiceover script from today's top story\n"
        "📊 */status* – Source health check: items fetched, top score, spikes\n"
        "💬 */chat [question]* – Chat about today's news\n"
        "   e.g. `/chat What's new with OpenAI today?`\n"
        "🎙 */setvoice [description]* – Set your writing voice for all content\n"
        "   e.g. `/setvoice Casual, punchy, uses data and metaphors`\n"
        "🧩 */module [tech|crypto|vietnam|indie]* – Switch active module\n"
        "🔗 */link* – Link this Telegram to TrendPost (enables auto-post + STOP command)\n\n"
        "📅 Auto-report every day at *8:00 AM* and *8:00 PM* (GMT+7)"
    )
    await update.message.reply_text(text)


async def cmd_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"[Analytics] user={update.effective_user.id} command=report module={_active_module}")
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
        await update.message.reply_text(chunk)


async def cmd_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/update — fast scan, no LLM, shows top scored items immediately."""
    logger.info(f"[Analytics] user={update.effective_user.id} command=update module={_active_module}")
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
    logger.info(f"[Analytics] user={update.effective_user.id} command=breaking module={_active_module}")
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
            "Usage: /topic [keyword]\nExamples:\n/topic openai\n/topic bitcoin\n/topic defi",
        )
        return

    logger.info(f"[Analytics] user={update.effective_user.id} command=topic module={_active_module} topic={topic!r}")
    msg = await update.message.reply_text(f"🔍 Finding news about {topic}...")
    try:
        supervisor = SupervisorAgent(_get_module())
        report = await supervisor.generate_report_for_topic(topic)
    except Exception as e:
        logger.error(f"Topic report failed for '{topic}': {e}")
        await msg.edit_text("❌ Could not generate report. Please try again.")
        return

    await msg.delete()
    for chunk in split_long_message(report):
        await update.message.reply_text(chunk)


async def cmd_brief(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/brief — 3-bullet shareable summary of today's top stories."""
    user_id = update.effective_user.id
    logger.info(f"[Analytics] user={user_id} command=brief module={_active_module}")
    msg = await update.message.reply_text("⚡ Writing today's brief...")
    try:
        supervisor = SupervisorAgent(_get_module())
        brief = await supervisor.generate_brief(user_id=user_id)
    except Exception as e:
        logger.error(f"Brief generation failed: {e}")
        await msg.edit_text("❌ Could not generate brief. Please try again later.")
        return

    await msg.delete()
    for chunk in split_long_message(brief):
        await update.message.reply_text(chunk)


async def cmd_thread(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/thread — generate a 7-tweet Twitter thread from today's top story."""
    user_id = update.effective_user.id
    logger.info(f"[Analytics] user={user_id} command=thread module={_active_module}")
    msg = await update.message.reply_text("🧵 Writing thread from today's top story... (30-60 sec)")
    try:
        supervisor = SupervisorAgent(_get_module())
        thread = await supervisor.generate_thread(user_id=user_id)
    except Exception as e:
        logger.error(f"Thread generation failed: {e}")
        await msg.edit_text("❌ Could not generate thread. Please try again later.")
        return

    await msg.delete()
    for chunk in split_long_message(thread):
        await update.message.reply_text(chunk)


async def cmd_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_message = " ".join(context.args)[:500].replace("\n", " ").strip() if context.args else ""

    if not user_message:
        await update.message.reply_text(
            "What do you want to ask? Example:\n/chat What's new with OpenAI today?",
        )
        return

    logger.info(f"[Analytics] user={user_id} command=chat module={_active_module}")
    history = _chat_histories.get(user_id, [])
    typing_msg = await update.message.reply_text("💭 Thinking...")

    try:
        reply = await chat_with_llm(user_message, _get_module().get_chat_system_prompt(), history)
    except Exception as e:
        logger.error(f"Chat LLM call failed for user {user_id}: {e}")
        await typing_msg.edit_text("❌ Could not get a response. Please try again.")
        return

    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": reply})
    _chat_histories[user_id] = history[-(MAX_HISTORY * 2):]

    await typing_msg.delete()
    for chunk in split_long_message(reply):
        await update.message.reply_text(chunk)


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/status — source health & last run summary (cached within 2h, else live scan)."""
    logger.info(f"[Analytics] user={update.effective_user.id} command=status module={_active_module}")
    from agents.supervisor import _STATUS_CACHE
    import time as _time
    cached = _STATUS_CACHE.get(_active_module)
    if cached:
        msg = await update.message.reply_text("📊 Loading status from last run...")
    else:
        msg = await update.message.reply_text("📊 Running status check... (~10 sec)")
    try:
        supervisor = SupervisorAgent(_get_module())
        status = await supervisor.get_status()
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        await msg.edit_text("❌ Status check failed.")
        return

    cache_entry = _STATUS_CACHE.get(_active_module)
    age_min = int((_time.time() - cache_entry["timestamp"]) / 60) if cache_entry else 0
    freshness = f"cached {age_min}m ago" if (cache_entry and age_min > 0) else "live"

    lines = [
        f"📊 *Kyvra Status* — module: *{status['module']}* ({freshness})",
        f"Items fetched: {status['total_fetched']}",
        f"Top score: {status['top_score']}/100",
        f"Spikes: {status['spikes']}",
        "",
        "*Sources:*",
    ]
    for source, count in sorted(status['sources'].items()):
        lines.append(f"  • {source}: {count}")
    await msg.delete()
    await update.message.reply_text("\n".join(lines))


async def cmd_newsletter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/newsletter — generate a newsletter section from today's top story."""
    user_id = update.effective_user.id
    logger.info(f"[Analytics] user={user_id} command=newsletter module={_active_module}")
    msg = await update.message.reply_text("📰 Writing newsletter section from today's top story...")
    try:
        supervisor = SupervisorAgent(_get_module())
        newsletter = await supervisor.generate_newsletter(user_id=user_id)
    except Exception as e:
        logger.error(f"Newsletter generation failed: {e}")
        await msg.edit_text("❌ Could not generate newsletter section. Please try again later.")
        return
    await msg.delete()
    for chunk in split_long_message(newsletter):
        await update.message.reply_text(chunk)


async def cmd_script(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/script — generate a TikTok/Reels voiceover script from today's top story."""
    user_id = update.effective_user.id
    logger.info(f"[Analytics] user={user_id} command=script module={_active_module}")
    msg = await update.message.reply_text("🎬 Writing voiceover script from today's top story...")
    try:
        supervisor = SupervisorAgent(_get_module())
        script = await supervisor.generate_script(user_id=user_id)
    except Exception as e:
        logger.error(f"Script generation failed: {e}")
        await msg.edit_text("❌ Could not generate script. Please try again later.")
        return
    await msg.delete()
    for chunk in split_long_message(script):
        await update.message.reply_text(chunk)


async def cmd_setvoice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/setvoice [description] — save a personal writing voice/style profile."""
    user_id = update.effective_user.id
    voice = " ".join(context.args)[:500].replace("\n", " ").strip() if context.args else ""

    if not voice:
        current = memory.get_voice_profile(user_id)
        if current:
            await update.message.reply_text(
                f"🎙 *Your current voice profile:*\n_{current}_\n\n"
                "To update it: `/setvoice Casual, punchy, uses data and metaphors`\n"
                "To clear it: `/setvoice clear`",
            )
        else:
            await update.message.reply_text(
                "🎙 No voice profile set yet.\n\n"
                "Usage: `/setvoice [your writing style description]`\n"
                "Example: `/setvoice Casual, punchy, uses data and metaphors, builder tone`",
            )
        return

    if voice.lower() == "clear":
        memory.save_voice_profile(user_id, "")
        logger.info(f"[Analytics] user={user_id} command=setvoice action=clear")
        await update.message.reply_text("🗑 Voice profile cleared.")
        return

    memory.save_voice_profile(user_id, voice)
    logger.info(f"[Analytics] user={user_id} command=setvoice action=set")
    await update.message.reply_text(
        f"✅ Voice profile saved!\n\n_{voice}_\n\n"
        "All content formats (/thread, /brief, /newsletter, /script) will now use your voice.",
    )


async def cmd_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/link — generate a one-time 6-digit code to link this Telegram account to TrendPost web app."""
    if not TRENDPOST_API_URL or not TRENDPOST_WEBHOOK_SECRET:
        await update.message.reply_text(
            "⚠️ TrendPost integration is not configured. Contact support."
        )
        return

    chat_id = str(update.effective_chat.id)
    code = "".join(random.choices(string.digits, k=6))
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()

    # Store the code in TrendPost so the web UI can verify it
    payload = {"telegram_chat_id": chat_id, "code": code, "expires_at": expires_at}
    body = json.dumps(payload, separators=(",", ":"))
    sig = "sha256=" + hmac.new(
        TRENDPOST_WEBHOOK_SECRET.encode(),
        body.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{TRENDPOST_API_URL}/api/webhooks/kyvra-link",
                content=body,
                headers={"Content-Type": "application/json", "x-kyvra-signature": sig},
            )
        if resp.status_code not in (200, 201):
            logger.error(f"cmd_link: TrendPost returned {resp.status_code}: {resp.text}")
            await update.message.reply_text(
                "❌ Could not generate link code. Please try again in a moment."
            )
            return
    except Exception as e:
        logger.error(f"cmd_link: request failed: {e}")
        await update.message.reply_text(
            "❌ Could not reach TrendPost. Please try again in a moment."
        )
        return

    await update.message.reply_text(
        f"🔗 *Link your TrendPost account*\n\n"
        f"Enter this code in TrendPost → Settings → Telegram:\n\n"
        f"```\n{code}\n```\n\n"
        f"Code expires in *5 minutes*. Run /link again if it expires.",
        parse_mode="Markdown",
    )
    logger.info(f"cmd_link: code generated for chat_id={chat_id}")


async def handle_stop_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Plain-text message handler for 'STOP' (case-insensitive).
    Cancels the most recent pending_approval auto-post for this Telegram chat.
    """
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip().upper()
    if text != "STOP":
        return

    if not TRENDPOST_API_URL or not TRENDPOST_WEBHOOK_SECRET:
        return

    chat_id = str(update.effective_chat.id)
    logger.info(f"handle_stop_message: STOP received from chat_id={chat_id}")

    payload = {"telegram_chat_id": chat_id}
    body = json.dumps(payload, separators=(",", ":"))
    sig = "sha256=" + hmac.new(
        TRENDPOST_WEBHOOK_SECRET.encode(),
        body.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{TRENDPOST_API_URL}/api/webhooks/kyvra-stop",
                content=body,
                headers={"Content-Type": "application/json", "x-kyvra-signature": sig},
            )

        if resp.status_code == 200:
            await update.message.reply_text(
                "✅ Got it — today's auto-post has been cancelled."
            )
        elif resp.status_code == 404:
            await update.message.reply_text(
                "ℹ️ No pending auto-post found to cancel."
            )
        elif resp.status_code == 409:
            await update.message.reply_text(
                "ℹ️ The post has already been sent or was already cancelled."
            )
        else:
            logger.warning(f"handle_stop_message: unexpected status {resp.status_code}: {resp.text}")
            await update.message.reply_text(
                "⚠️ Could not cancel the post. Please check TrendPost directly."
            )
    except Exception as e:
        logger.error(f"handle_stop_message: request failed: {e}")
        await update.message.reply_text(
            "⚠️ Could not reach TrendPost to cancel. Please check the app directly."
        )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Telegram error: {context.error}", exc_info=context.error)
