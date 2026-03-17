KEYWORDS = [
    # Assets
    "bitcoin", "btc", "ethereum", "eth", "solana", "sol", "bnb", "xrp",
    "avalanche", "avax", "polygon", "matic", "arbitrum", "optimism", "base",
    # DeFi
    "defi", "tvl", "yield", "liquidity", "amm", "dex", "cex", "swap",
    "uniswap", "aave", "compound", "curve", "maker", "lido", "eigenlayer",
    # NFT / Web3
    "nft", "web3", "on-chain", "smart contract", "dao", "token", "airdrop",
    # Layer 2 / scaling
    "layer 2", "l2", "rollup", "zk proof", "zkp", "zkevm", "validium",
    # Stablecoins / macro
    "stablecoin", "usdt", "usdc", "cbdc", "tether",
    # Infrastructure
    "wallet", "bridge", "oracle", "chainlink", "infra",
    # Narrative / market
    "altcoin", "meme coin", "bull run", "bear market", "halving", "etf",
    "spot etf", "blackrock bitcoin", "sec crypto", "regulation",
    # Key people / orgs
    "vitalik", "saylor", "coinbase", "binance", "kraken", "grayscale",
    "microstrategy", "bitfinex", "cointelegraph", "coindesk",
    # Vietnam crypto
    "vndc", "sipher", "kyber", "axie", "sky mavis", "coin98", "tomochain",
    "viction", "ancient8", "trava", "kyberswap",
]

# Source authority scores (0-20 extra points in confidence scoring)
# X is the primary — and only — source for crypto. News breaks on CT first.
SOURCE_AUTHORITY = {
    "X - Crypto Global Leaders":  20,
    "X - Bitcoin & Macro":        19,
    "X - Ethereum & DeFi":        18,
    "X - Solana & Alt-L1":        17,
    "X - Vietnam Crypto":         17,
    "X - Crypto Macro":           16,
    "X - DeFi":                   15,
    "X - Web3 / L2":              14,
}

# X/Twitter: tweet is viral if likes > this
# Lower than tech (300 vs 500) — CT moves faster
X_SPIKE_THRESHOLD = 300

# ── Global crypto leaders ────────────────────────────────────────────────────
# Protocol founders & core devs
X_CRYPTO_GLOBAL_LEADERS = [
    "VitalikButerin",   # Ethereum founder
    "aeyakovenko",      # Solana co-founder
    "CZbinance",        # Binance founder
    "brian_armstrong",  # Coinbase CEO
    "tyler",            # Winklevoss / Gemini
    "cameron",          # Winklevoss / Gemini
]

# Bitcoin & macro
X_BITCOIN_MACRO = [
    "saylor",           # MicroStrategy
    "documentingbtc",   # BTC data/charts
    "PrestonPysh",      # Bitcoin Standard podcast
    "WClementeIII",     # on-chain analyst
    "caprioleio",       # Bitcoin macro research
    "100trillionUSD",   # Stock-to-flow model
    "PeterSchiff",      # gold/BTC debate (contrarian signal)
    "maxkeiser",        # BTC maximalist
]

# Ethereum & DeFi
X_ETHEREUM_DEFI = [
    "sassal0x",         # Ethereum educator
    "haydenzadams",     # Uniswap founder
    "StaniKulechov",    # Aave founder
    "RuneKek",          # MakerDAO founder
    "AntonioMJuliano",  # dYdX founder
    "MonetSupply",      # DeFi researcher
    "evan_van_ness",    # Week in Ethereum
]

# Solana & alt-L1 ecosystem
X_SOLANA_ALT_L1 = [
    "rajgokal",         # Solana co-founder
    "armaniferrante",   # Solana ecosystem
    "cronos_shadow",    # Solana DeFi signal
    "0xMert_",          # Helius / Solana dev
    "weremeow",         # Jupiter / Solana DeFi
]

# On-chain analysts & researchers (global)
X_CRYPTO_MACRO_ACCOUNTS = [
    "WuBlockchain",     # China crypto news
    "ZachXBT",          # on-chain detective
    "nic__carter",      # Bitcoin researcher
    "aantonop",         # Bitcoin advocate
    "MessariCrypto",    # research platform
    "Blockworks_",      # institutional crypto
    "SECGov",           # regulatory signal
    "GaryGensler",      # SEC chair
    "SenLummis",        # pro-crypto senator
]

# ── Vietnam crypto leaders ───────────────────────────────────────────────────
# Founders, builders, KOLs of the Vietnamese crypto community
X_VIETNAM_CRYPTO = [
    # Protocol / product founders
    "loi_luu",          # Kyber Network founder
    "trungnguyen_eth",  # Coin98 Finance founder
    "trinhkien",        # Ancient8 / crypto gaming
    "jeffkuang",        # Axie / Sky Mavis
    "longhash_vn",      # Vietnam blockchain research
    # Top Vietnam crypto KOLs / educators
    "btc_vn",           # BTC Vietnam community
    "coin98analytics",  # Coin98 analytics
    "defivn_",          # DeFi Vietnam community
]
