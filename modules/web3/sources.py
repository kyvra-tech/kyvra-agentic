from __future__ import annotations

from modules.base import BaseModule, DataSource
from modules.web3.config import KEYWORDS, SOURCE_AUTHORITY
from modules.web3 import prompts


class Web3Module(BaseModule):
    name = "web3"

    def get_sources(self) -> list[DataSource]:
        return [
            # ── Tier 1: developer & research-native blogs/newsletters ─────
            DataSource(
                name="Ethereum Foundation",
                url="https://blog.ethereum.org/feed.xml",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("Ethereum Foundation", 20),
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="a16z Crypto",
                url="https://a16zcrypto.substack.com/feed",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("a16z Crypto", 18),
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="Web3 Foundation",
                url="https://medium.com/feed/web3foundation",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("Web3 Foundation", 17),
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="Chainlink Blog",
                url="https://blog.chain.link/feed/",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("Chainlink Blog", 17),
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="Bankless",
                url="https://www.bankless.com/rss/feed",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("Bankless", 16),
            ),
            # ── Tier 2: general crypto/web3 media publications ────────────
            DataSource(
                name="CoinDesk",
                url="https://www.coindesk.com/arc/outboundfeeds/rss",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("CoinDesk", 15),
            ),
            DataSource(
                name="The Block",
                url="https://www.theblock.co/rss.xml",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("The Block", 15),
            ),
            DataSource(
                name="Blockworks",
                url="https://blockworks.co/feed",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("Blockworks", 14),
            ),
            DataSource(
                name="Decrypt",
                url="https://decrypt.co/feed",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("Decrypt", 14),
            ),
            DataSource(
                name="CoinTelegraph",
                url="https://cointelegraph.com/rss",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("CoinTelegraph", 14),
            ),
            # ── Tier 3: NewsAPI keyword search ────────────────────────────
            DataSource(
                name="NewsAPI - Web3",
                url="https://newsapi.org/v2/everything",
                source_type="newsapi",
                params={
                    "endpoint": "everything",
                    "q": "web3 OR blockchain OR \"smart contract\" OR \"zero knowledge proof\" OR EVM",
                    "sort_by": "publishedAt",
                    "page_size": 15,
                },
                authority_score=SOURCE_AUTHORITY.get("NewsAPI - Web3", 12),
                bypass_keyword_filter=True,
            ),
        ]

    def get_report_prompt(self, items: list[dict]) -> str:
        return prompts.build_report_prompt(items)

    def get_thread_prompt(self, item: dict, voice: str | None = None) -> str:
        return prompts.build_thread_prompt(item, voice=voice)

    def get_brief_prompt(self, items: list[dict], voice: str | None = None) -> str:
        return prompts.build_brief_prompt(items, voice=voice)

    def get_newsletter_prompt(self, item: dict, voice: str | None = None) -> str:
        return prompts.build_newsletter_prompt(item, voice=voice)

    def get_script_prompt(self, item: dict, voice: str | None = None) -> str:
        return prompts.build_script_prompt(item, voice=voice)

    def get_tweet_hook_prompt(self, item: dict, lang: str = "en") -> str:
        return prompts.build_tweet_hook_prompt(item, lang=lang)

    def get_chat_system_prompt(self) -> str:
        return prompts.CHAT_SYSTEM_PROMPT

    def get_keywords(self) -> list[str]:
        return KEYWORDS
