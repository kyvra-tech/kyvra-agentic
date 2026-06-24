from __future__ import annotations

from modules.base import BaseModule, DataSource
from modules.wisdom.config import KEYWORDS, SOURCE_AUTHORITY
from modules.wisdom import prompts


class WisdomModule(BaseModule):
    name = "wisdom"

    def get_sources(self) -> list[DataSource]:
        return [
            # ── Tier 1: Core motivation & habit building blogs ─────────────
            DataSource(
                name="James Clear",
                url="https://jamesclear.com/feed",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("James Clear", 18),
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="Daily Stoic",
                url="https://dailystoic.com/feed/",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("Daily Stoic", 18),
                bypass_keyword_filter=True,
            ),
            # ── Tier 2: Simplicity, mindfulness & chilling ──────────────────
            DataSource(
                name="Zen Habits",
                url="https://zenhabits.net/index.xml",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("Zen Habits", 18),
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="Tiny Buddha",
                url="https://tinybuddha.com/feed/",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("Tiny Buddha", 17),
            ),
            DataSource(
                name="Farnam Street",
                url="https://fs.blog/feed/",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("Farnam Street", 16),
            ),
            # ── Tier 3: Scoped search for general motivation & resilience ─────
            DataSource(
                name="NewsAPI - Motivation",
                url="https://newsapi.org/v2/everything",
                source_type="newsapi",
                params={
                    "endpoint": "everything",
                    "q": "motivation OR resilience OR mindfulness OR \"peace of mind\"",
                    "sort_by": "publishedAt",
                    "page_size": 15,
                },
                authority_score=SOURCE_AUTHORITY.get("NewsAPI - Motivation", 12),
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
