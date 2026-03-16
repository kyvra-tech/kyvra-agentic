from collections import Counter
from agents.base import BaseAgent, PipelineContext

TREND_TOPICS: dict[str, list[str]] = {
    "AI Agents":         ["agent", "agentic", "autonomous", "tool use", "mcp"],
    "LLM / Models":      ["llm", "model", "gpt", "claude", "gemini", "llama", "mistral", "grok"],
    "OpenAI":            ["openai", "gpt", "chatgpt", "o1", "o3", "o4"],
    "Anthropic":         ["anthropic", "claude"],
    "Google AI":         ["deepmind", "gemini", "google ai"],
    "Indie Dev / SaaS":  ["indie", "saas", "launch", "product hunt", "show hn", "built"],
    "Open Source":       ["open source", "github", "open-source", "hugging face"],
    "AI Tools":          ["cursor", "copilot", "replit", "vercel", "supabase"],
    "Funding":           ["raises", "funding", "acqui", "series", "valuation"],
}

_HEAT: dict[int, str] = {5: "🔥", 4: "📈", 3: "🟡", 2: "👀", 1: "📉"}


def _heat(count: int) -> str:
    for threshold in sorted(_HEAT, reverse=True):
        if count >= threshold:
            return _HEAT[threshold]
    return ""


class NarrativeScoutAgent(BaseAgent):
    """Builds a trend heatmap from raw item text — runs in parallel with Analyst."""

    async def run(self, ctx: PipelineContext) -> PipelineContext:
        self._log(f"Scanning {len(ctx.raw_items)} items for trending topics...")

        counts: Counter = Counter()
        for item in ctx.raw_items:
            text = (item.title + " " + item.summary).lower()
            for topic, keywords in TREND_TOPICS.items():
                if any(kw in text for kw in keywords):
                    counts[topic] += 1

        top = counts.most_common(4)
        ctx.trend_heatmap = " | ".join(
            f"{topic} {_heat(n)}" for topic, n in top if n > 0
        ) or "Tech 📊"

        self._log(f"Heatmap: {ctx.trend_heatmap}")
        return ctx
