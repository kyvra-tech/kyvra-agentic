"""
scout_node — LangGraph node: build trend heatmap from raw item text.

Reads:  state["raw_items"], state["module_name"]
Writes: state["trend_heatmap"]

Pure Python — no LLM call. Runs in parallel with analyst_node.
"""

import logging
from collections import Counter

from agents.state import KyvraState

logger = logging.getLogger(__name__)

_TECH_TOPICS: dict[str, list[str]] = {
    "AI Agents":        ["agent", "agentic", "autonomous", "tool use", "mcp"],
    "LLM / Models":     ["llm", "model", "gpt", "claude", "gemini", "llama", "mistral", "grok"],
    "OpenAI":           ["openai", "gpt", "chatgpt", "o1", "o3", "o4"],
    "Anthropic":        ["anthropic", "claude"],
    "Google AI":        ["deepmind", "gemini", "google ai"],
    "Indie Dev / SaaS": ["indie", "saas", "launch", "product hunt", "show hn", "built"],
    "Open Source":      ["open source", "github", "open-source", "hugging face"],
    "AI Tools":         ["cursor", "copilot", "replit", "vercel", "supabase"],
    "Funding":          ["raises", "funding", "acqui", "series", "valuation"],
}

_CRYPTO_TOPICS: dict[str, list[str]] = {
    "Bitcoin":      ["bitcoin", "btc", "satoshi", "lightning", "ordinals"],
    "Ethereum":     ["ethereum", "eth", "eip", "vitalik", "pectra"],
    "DeFi":         ["defi", "tvl", "yield", "liquidity", "amm", "dex", "lending"],
    "Layer 2":      ["l2", "rollup", "optimism", "arbitrum", "zksync", "base", "starknet"],
    "Regulation":   ["sec", "cftc", "regulation", "compliance", "etf", "legal", "law"],
    "Stablecoins":  ["usdc", "usdt", "stablecoin", "depeg", "tether", "dai"],
    "NFT / Gaming": ["nft", "gaming", "axie", "web3 game", "metaverse"],
    "Funding / VC": ["raises", "funding", "series", "valuation", "vc", "backed"],
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


async def run(state: KyvraState) -> dict:
    raw_items = state.get("raw_items") or []
    module_name = state["module_name"]

    logger.info("[scout] Scanning %d items for trending topics...", len(raw_items))

    topics = _MODULE_TOPICS.get(module_name, _TECH_TOPICS)
    fallback = _MODULE_FALLBACKS.get(module_name, "Tech 📊")

    counts: Counter = Counter()
    for item in raw_items:
        text = (item.title + " " + item.summary).lower()
        for topic, keywords in topics.items():
            if any(kw in text for kw in keywords):
                counts[topic] += 1

    top = counts.most_common(4)
    heatmap = " | ".join(f"{topic} {_heat(n)}" for topic, n in top if n > 0) or fallback

    logger.info("[scout] Heatmap: %s", heatmap)
    return {"trend_heatmap": heatmap}
