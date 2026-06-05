from __future__ import annotations

from modules.base import BaseModule, DataSource
from modules.energy.config import KEYWORDS, SOURCE_AUTHORITY
from modules.energy import prompts


class EnergyModule(BaseModule):
    name = "energy"

    def get_sources(self) -> list[DataSource]:
        return [
            # ── Tier 1: specialist energy outlets ─────────────────────────
            DataSource(
                name="OilPrice.com",
                url="https://oilprice.com/rss/main",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("OilPrice.com", 17),
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="Energy Monitor",
                url="https://www.energymonitor.ai/feed/",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("Energy Monitor", 16),
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="S&P Global Energy",
                url="https://www.spglobal.com/commodityinsights/en/rss-feed/oil",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("S&P Global Energy", 17),
                bypass_keyword_filter=True,
            ),
            # ── Tier 2: wire services ──────────────────────────────────────
            DataSource(
                name="Reuters Energy",
                url="https://feeds.reuters.com/reuters/businessNews",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("Reuters Energy", 20),
            ),
            # ── Tier 3: NewsAPI energy keyword search ─────────────────────
            DataSource(
                name="NewsAPI - Energy",
                url="https://newsapi.org/v2/everything",
                source_type="newsapi",
                params={
                    "endpoint": "everything",
                    "q": "oil price OR OPEC OR natural gas OR renewable energy OR energy crisis",
                    "sort_by": "publishedAt",
                    "page_size": 15,
                },
                authority_score=SOURCE_AUTHORITY.get("NewsAPI - Energy", 14),
                bypass_keyword_filter=True,
            ),
            # ── Tier 4: Google News energy ─────────────────────────────────
            DataSource(
                name="Google News - Energy",
                url="https://news.google.com/rss/search?q=oil+gas+energy+OPEC&hl=en-US&gl=US&ceid=US:en",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("Google News - Energy", 13),
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
