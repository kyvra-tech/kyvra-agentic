from modules.base import BaseModule, DataSource
from modules.crypto.config import (
    KEYWORDS, SOURCE_AUTHORITY,
    X_CRYPTO_GLOBAL_LEADERS, X_BITCOIN_MACRO,
    X_ETHEREUM_DEFI, X_SOLANA_ALT_L1,
    X_CRYPTO_MACRO_ACCOUNTS, X_VIETNAM_CRYPTO,
)
from modules.crypto import prompts

# Build from: account queries — English global feeds
_X_GLOBAL_LEADERS_QUERY = (
    " OR ".join(f"from:{a}" for a in X_CRYPTO_GLOBAL_LEADERS)
    + " -is:retweet lang:en"
)
_X_BTC_MACRO_QUERY = (
    " OR ".join(f"from:{a}" for a in X_BITCOIN_MACRO)
    + " -is:retweet lang:en"
)
_X_ETH_DEFI_QUERY = (
    " OR ".join(f"from:{a}" for a in X_ETHEREUM_DEFI)
    + " -is:retweet lang:en"
)
_X_SOL_L1_QUERY = (
    " OR ".join(f"from:{a}" for a in X_SOLANA_ALT_L1)
    + " -is:retweet lang:en"
)
_X_MACRO_QUERY = (
    " OR ".join(f"from:{a}" for a in X_CRYPTO_MACRO_ACCOUNTS)
    + " -is:retweet lang:en"
)

# Vietnam: include both English and Vietnamese tweets from known accounts
_X_VIETNAM_QUERY = (
    " OR ".join(f"from:{a}" for a in X_VIETNAM_CRYPTO)
    + " -is:retweet"
)


class CryptoModule(BaseModule):
    name = "crypto"

    def get_sources(self) -> list[DataSource]:
        return [
            # ── X: account-based, primary signal ──────────────────────────
            # These are pre-curated trusted accounts — bypass keyword filter
            DataSource(
                name="X - Crypto Global Leaders",
                url="https://api.twitter.com/2/tweets/search/recent",
                source_type="x",
                params={"query": _X_GLOBAL_LEADERS_QUERY, "max_results": 10},
                authority_score=SOURCE_AUTHORITY["X - Crypto Global Leaders"],
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="X - Bitcoin & Macro",
                url="https://api.twitter.com/2/tweets/search/recent",
                source_type="x",
                params={"query": _X_BTC_MACRO_QUERY, "max_results": 10},
                authority_score=SOURCE_AUTHORITY["X - Bitcoin & Macro"],
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="X - Ethereum & DeFi",
                url="https://api.twitter.com/2/tweets/search/recent",
                source_type="x",
                params={"query": _X_ETH_DEFI_QUERY, "max_results": 10},
                authority_score=SOURCE_AUTHORITY["X - Ethereum & DeFi"],
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="X - Solana & Alt-L1",
                url="https://api.twitter.com/2/tweets/search/recent",
                source_type="x",
                params={"query": _X_SOL_L1_QUERY, "max_results": 10},
                authority_score=SOURCE_AUTHORITY["X - Solana & Alt-L1"],
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="X - Crypto Macro",
                url="https://api.twitter.com/2/tweets/search/recent",
                source_type="x",
                params={"query": _X_MACRO_QUERY, "max_results": 10},
                authority_score=SOURCE_AUTHORITY["X - Crypto Macro"],
                bypass_keyword_filter=True,
            ),
            # ── X: Vietnam crypto community ────────────────────────────────
            DataSource(
                name="X - Vietnam Crypto",
                url="https://api.twitter.com/2/tweets/search/recent",
                source_type="x",
                params={"query": _X_VIETNAM_QUERY, "max_results": 10},
                authority_score=SOURCE_AUTHORITY["X - Vietnam Crypto"],
                bypass_keyword_filter=True,
            ),
            # ── X: keyword-based signal discovery ─────────────────────────
            DataSource(
                name="X - DeFi",
                url="https://api.twitter.com/2/tweets/search/recent",
                source_type="x",
                params={
                    "query": "(DeFi OR TVL OR liquidity OR yield farming OR airdrop) -is:retweet lang:en",
                    "max_results": 10,
                },
                authority_score=SOURCE_AUTHORITY["X - DeFi"],
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="X - Web3 / L2",
                url="https://api.twitter.com/2/tweets/search/recent",
                source_type="x",
                params={
                    "query": "(L2 OR rollup OR \"zk proof\" OR \"smart contract\" OR web3) -is:retweet lang:en",
                    "max_results": 10,
                },
                authority_score=SOURCE_AUTHORITY["X - Web3 / L2"],
                bypass_keyword_filter=True,
            ),
        ]

    def get_report_prompt(self, items: list[dict]) -> str:
        return prompts.build_report_prompt(items)

    def get_thread_prompt(self, item: dict) -> str:
        return prompts.build_thread_prompt(item)

    def get_brief_prompt(self, items: list[dict]) -> str:
        return prompts.build_brief_prompt(items)

    def get_chat_system_prompt(self) -> str:
        return prompts.CHAT_SYSTEM_PROMPT

    def get_keywords(self) -> list[str]:
        return KEYWORDS
