KEYWORDS = [
    # AI companies
    "openai", "anthropic", "google deepmind", "deepmind", "mistral", "cohere",
    "meta ai", "llama", "grok", "xai", "perplexity", "claude", "gpt", "gemini",
    # AI topics
    "llm", "large language model", "ai agent", "agentic", "rag", "fine-tuning",
    "multimodal", "diffusion", "generative ai", "foundation model", "transformer",
    "mcp", "model context protocol", "reasoning model", "alignment", "rlhf",
    # Indie dev / maker
    "indie hacker", "indie dev", "saas", "product hunt", "show hn", "built with",
    "launched", "open source", "github", "self-hosted",
    # Tech platforms
    "cursor", "replit", "vercel", "supabase", "cloudflare", "hugging face",
    "langchain", "llamaindex", "ollama", "vllm",
    # Research
    "arxiv", "paper", "benchmark", "sota", "research",
]

# Source authority scores (0-20 extra points in confidence scoring)
SOURCE_AUTHORITY = {
    "Anthropic Blog": 20,
    "OpenAI Blog": 20,
    "Google DeepMind Blog": 18,
    "X - AI Leaders": 18,
    "X - AI Research": 16,
    "X - AI Trending": 14,
    "X - AI Tools": 13,
    "X - OSS": 12,
    "X - Indie Dev": 12,
    "GitHub Trending": 10,
    "Product Hunt": 8,
    "NewsAPI Tech": 6,
}

# GitHub: trending repo is notable if stars_today > this
GITHUB_STARS_SPIKE = 100

# X/Twitter: tweet is viral if likes > this
X_SPIKE_THRESHOLD = 500

# Key X accounts to monitor (used in AI Leaders query)
# Broad set: lab accounts + prominent researchers + top builders
X_AI_LEADER_ACCOUNTS = [
    # AI labs (official)
    "AnthropicAI", "OpenAI", "GoogleDeepMind", "xai",
    # Lab founders / researchers
    "sama", "karpathy", "ylecun", "ilyasut", "DrJimFan",
    "jeffdean", "demishassabis", "GaryMarcus", "fchollet",
    # AI safety / alignment
    "ESYudkowsky", "paulfchristiano",
    # Top builders / indie makers in AI
    "levelsio", "marc_louvion", "danielgross", "benedictevans",
    # AI tools & platforms
    "amanrsanger", "ggerganov", "simonw",
]

# X accounts focused on AI research (used in AI Research query)
X_AI_RESEARCH_ACCOUNTS = [
    "arxiv_cscl", "paperswithcode", "huggingface",
    "weights_biases", "LangChainAI", "llama_index",
]
