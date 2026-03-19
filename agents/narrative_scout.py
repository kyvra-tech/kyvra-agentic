from collections import Counter
from agents.base import BaseAgent, PipelineContext

_TECH_TOPICS: dict[str, list[str]] = {
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

_CRYPTO_TOPICS: dict[str, list[str]] = {
    "Bitcoin":       ["bitcoin", "btc", "satoshi", "lightning", "ordinals"],
    "Ethereum":      ["ethereum", "eth", "eip", "vitalik", "pectra"],
    "DeFi":          ["defi", "tvl", "yield", "liquidity", "amm", "dex", "lending"],
    "Layer 2":       ["l2", "rollup", "optimism", "arbitrum", "zksync", "base", "starknet"],
    "Regulation":    ["sec", "cftc", "regulation", "compliance", "etf", "legal", "law"],
    "Stablecoins":   ["usdc", "usdt", "stablecoin", "depeg", "tether", "dai"],
    "NFT / Gaming":  ["nft", "gaming", "axie", "web3 game", "metaverse"],
    "Funding / VC":  ["raises", "funding", "series", "valuation", "vc", "backed"],
}

_VIETNAM_TOPICS: dict[str, list[str]] = {
    "Vietnam Startup": ["vietnam", "viet", "hanoi", "hcmc", "saigon", "vng", "momo", "tiki"],
    "SEA Tech":        ["southeast asia", "sea", "singapore", "indonesia", "grab", "gojek"],
    "Vietnam Crypto":  ["coin98", "kyber", "axie", "sky mavis", "vndc", "viction"],
    "Fintech VN":      ["vnpay", "zalopay", "momo", "fintech", "ngan hang"],
    "AI / LLM":        ["llm", "ai", "gpt", "claude", "gemini", "vinai"],
    "Funding":         ["raises", "funding", "series", "dau tu", "goi von"],
}

_INDIE_TOPICS: dict[str, list[str]] = {
    "Launches":        ["launch", "launched", "product hunt", "show hn", "shipped"],
    "MRR / Revenue":   ["mrr", "arr", "revenue", "paying", "customers", "churn"],
    "AI Tools":        ["ai tool", "ai app", "cursor", "replit", "vibe cod", "llm"],
    "Built in Public": ["built in public", "building in public", "bip", "open startup"],
    "Funding":         ["raises", "funding", "backed", "acquired", "valuation"],
    "Distribution":    ["viral", "hacker news", "reddit", "twitter", "seo", "growth"],
}

_MODULE_TOPICS: dict[str, dict[str, list[str]]] = {
    "tech":    _TECH_TOPICS,
    "crypto":  _CRYPTO_TOPICS,
    "vietnam": _VIETNAM_TOPICS,
    "indie":   _INDIE_TOPICS,
}
_MODULE_FALLBACKS: dict[str, str] = {
    "tech":    "Tech 📊",
    "crypto":  "Crypto 📊",
    "vietnam": "Vietnam Tech 🇻🇳",
    "indie":   "Indie 🚀",
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

        topics = _MODULE_TOPICS.get(ctx.module.name, _TECH_TOPICS)
        fallback = _MODULE_FALLBACKS.get(ctx.module.name, "Tech 📊")

        counts: Counter = Counter()
        for item in ctx.raw_items:
            text = (item.title + " " + item.summary).lower()
            for topic, keywords in topics.items():
                if any(kw in text for kw in keywords):
                    counts[topic] += 1

        top = counts.most_common(4)
        ctx.trend_heatmap = " | ".join(
            f"{topic} {_heat(n)}" for topic, n in top if n > 0
        ) or fallback

        self._log(f"Heatmap: {ctx.trend_heatmap}")
        return ctx
