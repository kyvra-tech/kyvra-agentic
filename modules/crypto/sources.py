from modules.base import BaseModule, DataSource
from modules.crypto.config import (
    KEYWORDS, SOURCE_AUTHORITY,
    X_CRYPTO_LEADER_ACCOUNTS, X_CRYPTO_MACRO_ACCOUNTS,
)
from modules.crypto import prompts

_X_LEADER_QUERY = (
    " OR ".join(f"from:{a}" for a in X_CRYPTO_LEADER_ACCOUNTS)
    + " -is:retweet lang:en"
)
_X_MACRO_QUERY = (
    " OR ".join(f"from:{a}" for a in X_CRYPTO_MACRO_ACCOUNTS)
    + " -is:retweet lang:en"
)


class CryptoModule(BaseModule):
    name = "crypto"

    def get_sources(self) -> list[DataSource]:
        return [
            # --- X: account-based (pre-curated, bypass keyword filter) ---
            DataSource(
                name="X - Crypto Leaders",
                url="https://api.twitter.com/2/tweets/search/recent",
                source_type="x",
                params={"query": _X_LEADER_QUERY, "max_results": 10},
                authority_score=SOURCE_AUTHORITY["X - Crypto Leaders"],
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
            # --- X: keyword-based (signal discovery) ---
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
                name="X - Web3 / NFT",
                url="https://api.twitter.com/2/tweets/search/recent",
                source_type="x",
                params={
                    "query": "(L2 OR rollup OR \"zk proof\" OR \"smart contract\" OR web3) -is:retweet lang:en",
                    "max_results": 10,
                },
                authority_score=SOURCE_AUTHORITY["X - Web3 / NFT"],
                bypass_keyword_filter=True,
            ),
            # --- RSS: authoritative crypto media ---
            DataSource(
                name="CoinDesk",
                url="https://www.coindesk.com/arc/outboundfeeds/rss/",
                source_type="rss",
                authority_score=SOURCE_AUTHORITY["CoinDesk"],
            ),
            DataSource(
                name="Cointelegraph",
                url="https://cointelegraph.com/rss",
                source_type="rss",
                authority_score=SOURCE_AUTHORITY["Cointelegraph"],
            ),
            DataSource(
                name="The Block",
                url="https://www.theblock.co/rss.xml",
                source_type="rss",
                authority_score=SOURCE_AUTHORITY["The Block"],
            ),
            DataSource(
                name="Bitcoin Magazine",
                url="https://bitcoinmagazine.com/.rss/full/",
                source_type="rss",
                authority_score=SOURCE_AUTHORITY["Bitcoin Magazine"],
            ),
            DataSource(
                name="Decrypt",
                url="https://decrypt.co/feed",
                source_type="rss",
                authority_score=SOURCE_AUTHORITY["Decrypt"],
            ),
        ]

    def get_report_prompt(self, items: list[dict]) -> str:
        return prompts.build_report_prompt(items)

    def get_chat_system_prompt(self) -> str:
        return prompts.CHAT_SYSTEM_PROMPT

    def get_keywords(self) -> list[str]:
        return KEYWORDS
