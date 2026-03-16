from datetime import datetime, timezone, timedelta
from agents.base import ScoredItem

_VN_TZ = timezone(timedelta(hours=7))
_SPIKE_LABEL = "🔴 SPIKE"
_SCORE_EMOJI = {80: "📈", 60: "🟡", 0: "⬜"}


def _score_emoji(score: int) -> str:
    for threshold in sorted(_SCORE_EMOJI, reverse=True):
        if score >= threshold:
            return _SCORE_EMOJI[threshold]
    return "⬜"


def format_update(items: list[ScoredItem], total_fetched: int) -> str:
    now = datetime.now(_VN_TZ).strftime("%H:%M GMT+7")
    lines = [f"⚡ *Quick Update* — {now}", f"_{total_fetched} items scanned across all sources_\n"]
    for item in items[:7]:
        spike = f" {_SPIKE_LABEL}" if item.is_spike else ""
        emoji = _score_emoji(item.confidence_score)
        source_tag = f"[{item.source}]"
        title = item.title[:80] + ("…" if len(item.title) > 80 else "")
        lines.append(f"{emoji}{spike} *{source_tag}* {title}")
        lines.append(f"└ Score: {item.confidence_score}/100 | {item.url}\n")
    lines.append("_Use /report for full AI\\-written analysis_")
    return "\n".join(lines)


def format_breaking(spikes: list[ScoredItem]) -> str:
    now = datetime.now(_VN_TZ).strftime("%H:%M GMT+7")
    if not spikes:
        return f"🟢 No breaking spikes right now — {now}"
    lines = [f"🚨 *Breaking / Spike Items* — {now}\n"]
    for item in spikes:
        title = item.title[:90] + ("…" if len(item.title) > 90 else "")
        lines.append(f"🔴 *[{item.source}]* {title}")
        lines.append(f"└ Score: {item.confidence_score}/100 | raw: {item.raw_score} | {item.url}\n")
    return "\n".join(lines)


def split_long_message(text: str, max_length: int = 4000) -> list[str]:
    """Split a long message into Telegram-safe chunks (≤4096 chars)."""
    if len(text) <= max_length:
        return [text]

    chunks = []
    while text:
        if len(text) <= max_length:
            chunks.append(text)
            break
        split_at = text.rfind("\n", 0, max_length)
        if split_at == -1:
            split_at = max_length
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")

    return chunks
