import logging
from collections import Counter

logger = logging.getLogger(__name__)

TREND_TOPICS = {
    "AI Agents": ["agent", "agentic", "autonomous", "tool use", "mcp"],
    "LLM / Models": ["llm", "model", "gpt", "claude", "gemini", "llama", "mistral", "grok"],
    "OpenAI": ["openai", "gpt", "chatgpt", "o1", "o3", "o4"],
    "Anthropic": ["anthropic", "claude"],
    "Google AI": ["deepmind", "gemini", "google ai"],
    "Indie Dev / SaaS": ["indie", "saas", "launch", "product hunt", "show hn", "built"],
    "Open Source": ["open source", "github", "open-source", "hugging face"],
    "AI Tools": ["cursor", "copilot", "replit", "vercel", "supabase"],
    "Funding / Acquisition": ["raises", "funding", "acqui", "series", "valuation"],
}

HEAT_EMOJI = {
    5: "🔥",
    4: "📈",
    3: "🟡",
    2: "👀",
    1: "📉",
}


def _heat_emoji(count: int) -> str:
    if count >= 5:
        return HEAT_EMOJI[5]
    elif count >= 3:
        return HEAT_EMOJI[4]
    elif count >= 2:
        return HEAT_EMOJI[3]
    elif count == 1:
        return HEAT_EMOJI[2]
    return ""


class NarrativeScoutAgent:
    """Extracts trending topics from scored items to build the trend heatmap."""

    async def run(self, context: dict) -> dict:
        scored_items: list[dict] = context.get("scored_items", [])
        logger.info(f"[NarrativeScout] Analyzing {len(scored_items)} items for trends...")

        topic_counts: Counter = Counter()
        for item in scored_items:
            text = (item["title"] + " " + item.get("summary", "")).lower()
            for topic, keywords in TREND_TOPICS.items():
                if any(kw in text for kw in keywords):
                    topic_counts[topic] += 1

        # Top 4 trending topics for the heatmap
        top_trends = topic_counts.most_common(4)
        trend_heatmap = " | ".join(
            f"{topic} {_heat_emoji(count)}"
            for topic, count in top_trends
            if count > 0
        )

        context["trend_heatmap"] = trend_heatmap or "Tech 📊"
        logger.info(f"[NarrativeScout] Heatmap: {context['trend_heatmap']}")
        return context
