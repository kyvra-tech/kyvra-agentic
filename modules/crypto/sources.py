from __future__ import annotations

from modules.base import BaseModule, DataSource
from modules.crypto.config import KEYWORDS, SOURCE_AUTHORITY
from modules.crypto import prompts


class CryptoModule(BaseModule):
    name = "crypto"

    def get_sources(self) -> list[DataSource]:
        return [
            # ── Tier 1: crypto-native publications ────────────────────────
            DataSource(
                name="CoinDesk",
                url="https://www.coindesk.com/arc/outboundfeeds/rss/",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("CoinDesk", 18),
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="CoinTelegraph",
                url="https://cointelegraph.com/rss",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("CoinTelegraph", 17),
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="Decrypt",
                url="https://decrypt.co/feed",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("Decrypt", 16),
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="The Block",
                url="https://www.theblock.co/rss.xml",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("The Block", 17),
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="Blockworks",
                url="https://blockworks.co/feed",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("Blockworks", 16),
                bypass_keyword_filter=True,
            ),
            # ── Tier 2: broader finance with crypto coverage ───────────────
            DataSource(
                name="Reuters Crypto",
                url="https://feeds.reuters.com/reuters/businessNews",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("Reuters Crypto", 18),
            ),
            # ── Tier 3: NewsAPI crypto keyword search ─────────────────────
            DataSource(
                name="NewsAPI - Crypto",
                url="https://newsapi.org/v2/everything",
                source_type="newsapi",
                params={
                    "endpoint": "everything",
                    "q": "bitcoin OR ethereum OR crypto OR DeFi OR blockchain",
                    "sort_by": "publishedAt",
                    "page_size": 15,
                },
                authority_score=SOURCE_AUTHORITY.get("NewsAPI - Crypto", 14),
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

    def get_chat_system_prompt(self) -> str:
        return prompts.CHAT_SYSTEM_PROMPT

    def get_keywords(self) -> list[str]:
        return KEYWORDS
