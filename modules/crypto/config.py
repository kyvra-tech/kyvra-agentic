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
]

# Source authority scores (0-20 extra points in confidence scoring)
SOURCE_AUTHORITY = {
    "CoinDesk": 20,
    "Cointelegraph": 18,
    "The Block": 17,
    "Bitcoin Magazine": 16,
    "Decrypt": 15,
    "X - Crypto Leaders": 18,
    "X - DeFi": 14,
    "X - Web3 / NFT": 12,
    "X - Crypto Macro": 13,
}

# X/Twitter: tweet is viral if likes > this
# Lower than tech (300 vs 500) — CT moves faster, high-signal tweets get likes quickly
X_SPIKE_THRESHOLD = 300

# Key X accounts to monitor — highest signal-to-noise on Crypto Twitter
X_CRYPTO_LEADER_ACCOUNTS = [
    # Protocol founders
    "VitalikButerin", "solana", "aeyakovenko",
    # Macro / Bitcoin maximalists
    "saylor", "documentingbtc", "PeterSchiff",
    # Exchange / institutional
    "cz_binance", "brian_armstrong", "coinbase",
    # Researchers / analysts
    "nic__carter", "aantonop", "MessariCrypto",
    # DeFi builders
    "haydenzadams", "StaniKulechov", "RuneKek",
    # Media
    "CoinDesk", "Cointelegraph", "TheBlock__",
]

# X accounts focused on crypto macro / regulatory news
X_CRYPTO_MACRO_ACCOUNTS = [
    "SECGov", "GaryGensler", "SenLummis", "RepMcHenry",
    "Blockworks_", "WuBlockchain", "ZachXBT",
]
