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
    "HackerNews": 12,
    "GitHub Trending": 10,
    "Product Hunt": 8,
    "NewsAPI Tech": 6,
}

# Spike detection: item is "hot" if HN score > this value
HN_SPIKE_THRESHOLD = 200

# GitHub: trending repo is notable if stars_today > this
GITHUB_STARS_SPIKE = 100
