KEYWORDS = [
    # Core Infrastructure & Protocol
    "blockchain", "smart contract", "solidity", "rust", "wasm", "evm", "zkevm", "svm", "move language",
    "consensus", "proof of stake", "pos", "validator", "node", "mem-pool", "mempool",
    
    # Layer 2 & Scaling
    "layer 2", "l2", "rollup", "optimistic rollup", "zk rollup", "zkp", "zero-knowledge",
    "validium", "sidechain", "arbitrum", "optimism", "base chain", "polygon", "starknet", "zksync",
    "l2beat", "blobspace", "proto-danksharding", "eip-4844",
    
    # Cryptography
    "cryptography", "zero-knowledge proof", "zk-proof", "snark", "stark", "fully homomorphic encryption",
    "fhe", "multi-party computation", "mpc", "signatures",
    
    # Smart Contract Ecosystem & Standards
    "dapp", "decentralized app", "erc-20", "erc-721", "erc-1155", "erc-4337", "account abstraction",
    "smart wallet", "safe multisig", "walletconnect",
    
    # DeFi & Tokenomics
    "defi", "amm", "dex", "liquidity pool", "yield farming", "oracles", "chainlink", "pyth",
    "liquid restaking", "eigenlayer", "lrt", "lst", "tokenomics", "airdrop",
    
    # Governance & Web3 Narratives
    "dao", "decentralized governance", "rwa", "real world assets", "tokenization", "did",
    "decentralized identity", "decentralized storage", "ipfs", "arweave", "filecoin", "ens",
    
    # Key Organizations & Projects
    "ethereum foundation", "web3 foundation", "a16z crypto", "vitalik", "uniswap", "aave",
    "eigenlayer", "lido", "makerdao", "coindesk", "cointelegraph", "decrypt", "the block", "blockworks"
]

# Source authority scores (0-20 extra points in confidence scoring)
SOURCE_AUTHORITY = {
    # High authority developer & official resources
    "Ethereum Foundation":       20,
    "Week in Ethereum News":     19,
    "a16z Crypto":               18,
    "Web3 Foundation":           17,
    "Chainlink Blog":            17,
    "Bankless":                  16,
    
    # Media Outlets
    "CoinDesk":                  15,
    "CoinTelegraph":             14,
    "Decrypt":                   14,
    "The Block":                 15,
    "Blockworks":                14,
    
    # Search APIs
    "NewsAPI - Web3":            12,
    "Google News - Web3":        11,
}

# Default spike thresholds
X_SPIKE_THRESHOLD = 300
