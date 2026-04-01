from modules.base import BaseModule, DataSource
from modules.parody.config import KEYWORDS, SOURCE_AUTHORITY
from modules.parody import prompts


class ParodyModule(BaseModule):
    name = "parody"

    def get_sources(self) -> list[DataSource]:
        return [
            # ── Tier 1: satire publications ────────────────────────────────
            DataSource(
                name="The Onion",
                url="https://www.theonion.com/rss",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("The Onion", 20),
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="ClickHole",
                url="https://clickhole.com/feed/",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("ClickHole", 18),
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="The Babylon Bee",
                url="https://babylonbee.com/feed",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("The Babylon Bee", 16),
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="The Beaverton",
                url="https://www.thebeaverton.com/feed/",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("The Beaverton", 15),
                bypass_keyword_filter=True,
            ),
            # ── Tier 2: real news that sounds fake (Google News RSS) ───────
            DataSource(
                name="Google News - Weird",
                url="https://news.google.com/rss/search?q=unbelievable+bizarre+absurd&hl=en-US&gl=US&ceid=US:en",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("Google News - Weird", 12),
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

    def get_tweet_hook_prompt(self, item: dict) -> str:
        return prompts.build_tweet_hook_prompt(item)

    def get_chat_system_prompt(self) -> str:
        return prompts.CHAT_SYSTEM_PROMPT

    def get_keywords(self) -> list[str]:
        return KEYWORDS
