from datetime import datetime, timezone, timedelta
from agents.base import ScoredItem

_VN_TZ = timezone(timedelta(hours=7))


def _signal_label(item: ScoredItem) -> str:
    """Return a human-readable signal tier label with reason."""
    if item.is_spike and item.cross_source_count >= 2:
        return f"🔥 VIRAL — spike, {item.cross_source_count} sources"
    if item.is_spike:
        return f"🚨 SPIKE — {item.raw_score:,} engagements"
    if item.confidence_score >= 80 and item.cross_source_count >= 2:
        return f"📈 RISING — {item.cross_source_count} sources"
    if item.confidence_score >= 80:
        return f"📈 RISING — {item.source}"
    if item.confidence_score >= 60:
        return f"🟡 STEADY — {item.source}"
    return "⬜ SIGNAL"


def format_update(items: list[ScoredItem], total_fetched: int) -> str:
    now = datetime.now(_VN_TZ).strftime("%H:%M GMT+7")
    lines = [f"⚡ Quick Update — {now}", f"{total_fetched} items scanned across all sources\n"]
    for item in items[:7]:
        label = _signal_label(item)
        title = item.title[:80] + ("…" if len(item.title) > 80 else "")
        lines.append(f"[{item.source}] {title}")
        lines.append(f"└ {label} | {item.url}\n")
    lines.append("Use /report for full AI-written analysis")
    return "\n".join(lines)


def format_breaking(spikes: list[ScoredItem]) -> str:
    now = datetime.now(_VN_TZ).strftime("%H:%M GMT+7")
    if not spikes:
        return f"🟢 No breaking spikes right now — {now}"
    lines = [f"🚨 Breaking / Spike Items — {now}\n"]
    for item in spikes:
        label = _signal_label(item)
        title = item.title[:90] + ("…" if len(item.title) > 90 else "")
        lines.append(f"[{item.source}] {title}")
        lines.append(f"└ {label} | {item.url}\n")
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
