KEYWORDS = [
    # AI companies
    "openai", "anthropic", "google deepmind", "deepmind", "mistral", "cohere",
    "meta ai", "llama", "grok", "xai", "perplexity", "claude", "gpt", "gemini",
    # AI topics
    "llm", "large language model", "ai agent", "agentic", "rag", "fine-tuning",
    "multimodal", "diffusion", "generative ai", "foundation model", "transformer",
    # Indie dev / maker
    "indie hacker", "indie dev", "saas", "product hunt", "show hn", "built with",
    "launched", "open source", "github", "self-hosted",
    # Tech platforms
    "cursor", "replit", "vercel", "supabase", "cloudflare", "hugging face",
]

# Source authority scores (0-20 extra points in confidence scoring)
SOURCE_AUTHORITY = {
    "Anthropic Blog": 20,
    "OpenAI Blog": 20,
    "Google DeepMind Blog": 18,
    "X - AI Leaders": 18,
    "X - AI Trending": 14,
    "X - Indie Dev": 12,
    "HackerNews": 12,
    "GitHub Trending": 10,
    "Product Hunt": 8,
    "NewsAPI Tech": 6,
}

# Spike detection: item is "hot" if HN score > this value
HN_SPIKE_THRESHOLD = 200

# GitHub: trending repo is notable if stars_today > this
GITHUB_STARS_SPIKE = 100

# X/Twitter: tweet is viral if likes > this
X_SPIKE_THRESHOLD = 500

# Key X accounts to monitor (used in AI Leaders query)
X_AI_LEADER_ACCOUNTS = [
    "AnthropicAI", "OpenAI", "GoogleDeepMind",
    "sama", "karpathy", "ylecun", "ilyasut",
    "levelsio", "marc_louvion",
]
