from __future__ import annotations

from modules.base import BaseModule, DataSource
from modules.humor.config import KEYWORDS, SOURCE_AUTHORITY
from modules.humor import prompts


class HumorModule(BaseModule):
    name = "humor"

    def get_sources(self) -> list[DataSource]:
        return [
            # ── Tier 1: NewsAPI entertainment category ────────────────────
            DataSource(
                name="NewsAPI - Entertainment",
                url="https://newsapi.org/v2/top-headlines",
                source_type="newsapi",
                params={"endpoint": "top-headlines", "category": "entertainment", "page_size": 20},
                authority_score=SOURCE_AUTHORITY.get("NewsAPI - Entertainment", 16),
                bypass_keyword_filter=True,
            ),
            # ── Tier 2: trade publications ─────────────────────────────────
            DataSource(
                name="Variety",
                url="https://variety.com/feed/",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("Variety", 17),
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="Hollywood Reporter",
                url="https://www.hollywoodreporter.com/feed/",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("Hollywood Reporter", 17),
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="Entertainment Weekly",
                url="https://ew.com/feed/",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("Entertainment Weekly", 16),
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="Deadline",
                url="https://deadline.com/feed/",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("Deadline", 16),
                bypass_keyword_filter=True,
            ),
            # ── Tier 3: Google News entertainment ─────────────────────────
            DataSource(
                name="Google News - Entertainment",
                url="https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNREpxYW5RU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("Google News - Entertainment", 13),
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

    def get_spike_thresholds(self) -> tuple[int, int]:
        return (50, 200)
