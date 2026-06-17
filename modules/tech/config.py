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
    # Tech platforms & tools
    "cursor", "replit", "vercel", "supabase", "cloudflare", "hugging face",
    "langchain", "llamaindex", "vllm", "windsurf", "lovable",
    # Research
    "arxiv", "paper", "benchmark", "sota", "research",
]

# Source authority scores (0-20 extra points in confidence scoring)
# X is primary — restructured to match crypto module pattern
SOURCE_AUTHORITY = {
    # X: primary real-time signal
    "X - AI Labs":          20,
    "X - AI Leaders":       19,
    "X - Software Eng":     17,
    "X - Indie Builders":   16,
    "X - AI Research":      16,
    "X - AI Trending":      14,
    "X - AI Tools":         13,
    "X - OSS":              12,
    # GitHub: native signal for dev trends
    "GitHub Trending":      15,
    # Reddit
    "Reddit - ML":          11,
    "Reddit - LocalLLaMA":  10,
    "Reddit - SideProject":  9,
    # TLDR Tech newsletter
    "TLDR Tech":            12,
}

# GitHub: trending repo is notable if stars_today > this
GITHUB_STARS_SPIKE = 100

# X/Twitter: tweet is viral if likes > this
X_SPIKE_THRESHOLD = 500

# ── AI labs — official accounts ───────────────────────────────────────────────
X_AI_LAB_ACCOUNTS = [
    "AnthropicAI",      # Claude / Anthropic
    "OpenAI",           # ChatGPT / GPT-4
    "GoogleDeepMind",   # Gemini / Gemma
    "xai",              # Grok
    "MistralAI",        # Mistral / Mixtral
    "MetaAI",           # LLaMA
    "CohereAI",         # Command R
    "perplexity_ai",    # Perplexity
]

# ── AI founders, researchers, thought leaders ────────────────────────────────
X_AI_LEADER_ACCOUNTS = [
    # Lab heads & founders
    "sama",             # Sam Altman / OpenAI
    "demishassabis",    # Demis Hassabis / DeepMind
    "ylecun",           # Yann LeCun / Meta AI
    "karpathy",         # Andrej Karpathy
    "ilyasut",          # Ilya Sutskever
    "DrJimFan",         # Jim Fan / Nvidia AI
    "jeffdean",         # Jeff Dean / Google
    "fchollet",         # François Chollet / Keras
    # AI safety / alignment
    "ESYudkowsky",      # Eliezer Yudkowsky
    "paulfchristiano",  # Paul Christiano
    # Influential analysts
    "GaryMarcus",       # AI critic / researcher
    "benedictevans",    # tech analyst
    "emollick",         # Ethan Mollick / Wharton AI
]

# ── Software engineers & developer influencers ───────────────────────────────
X_SOFTWARE_ENG_ACCOUNTS = [
    "simonw",           # Simon Willison / Datasette, LLM tools
    "ggerganov",        # Georgi Gerganov / llama.cpp, whisper.cpp
    "dhh",              # DHH / Rails, HEY
    "kentcdodds",       # Kent C. Dodds / React testing
    "dan_abramov",      # Dan Abramov / React core
    "t3dotgg",          # Theo / TypeScript, T3 stack
    "wesbos",           # Wes Bos / web dev educator
    "swyx",             # swyx / AI engineer, Smol AI
    "daisyui",          # Pouya / DaisyUI
    "addyosmani",       # Addy Osmani / Chrome DevRel
]

# ── Indie hackers & product builders ────────────────────────────────────────
X_INDIE_BUILDER_ACCOUNTS = [
    "levelsio",         # Pieter Levels / Nomad List, PhotoAI
    "marc_louvion",     # Marc Lou / ShipFast
    "tdinh_me",         # Tony Dinh / Xnapper, BlackMagic
    "jdnoc",            # Jon Yongfook / Bannerbear
    "shl",              # Sahil Lavingia / Gumroad
    "paulg",            # Paul Graham / YC essays
    "danielgross",      # Daniel Gross / Pioneer
    "arvidkahl",        # Arvid Kahl / bootstrapped SaaS
    "thepatwalls",      # Pat Walls / Starter Story
    "heyeaslo",         # Easlo / Notion templates → SaaS
]

# ── AI research & tooling accounts ──────────────────────────────────────────
X_AI_RESEARCH_ACCOUNTS = [
    "huggingface",      # HuggingFace
    "paperswithcode",   # Papers With Code
    "weights_biases",   # Weights & Biases
    "LangChainAI",      # LangChain
    "llama_index",      # LlamaIndex
    "AnthropicAI",      # Anthropic research thread (also in labs)
]
