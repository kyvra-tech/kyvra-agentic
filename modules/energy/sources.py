from modules.base import BaseModule, DataSource
from modules.energy.config import KEYWORDS, SOURCE_AUTHORITY
from modules.energy import prompts


class EnergyModule(BaseModule):
    name = "energy"

    def get_sources(self) -> list[DataSource]:
        return [
            # ── NewsAPI: energy keyword search ────────────────────────────
            DataSource(
                name="NewsAPI - Energy",
                url="https://newsapi.org/v2/everything",
                source_type="newsapi",
                params={
                    "endpoint": "everything",
                    "q": "oil OR gas OR OPEC OR renewable energy OR energy crisis",
                    "sort_by": "publishedAt",
                    "page_size": 20,
                },
                authority_score=SOURCE_AUTHORITY["NewsAPI - Energy"],
                bypass_keyword_filter=True,
            ),
            # ── RSS: specialist energy publications ────────────────────────
            DataSource(
                name="Reuters Energy",
                url="https://feeds.reuters.com/reuters/businessNews",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["Reuters Energy"],
            ),
            DataSource(
                name="OilPrice.com",
                url="https://oilprice.com/rss/main",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["OilPrice.com"],
                bypass_keyword_filter=True,
            ),
            # ── Reddit RSS ─────────────────────────────────────────────────
            DataSource(
                name="Reddit - Energy",
                url="https://www.reddit.com/r/energy/new/.rss",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["Reddit - Energy"],
            ),
            DataSource(
                name="Reddit - Renewables",
                url="https://www.reddit.com/r/renewable/new/.rss",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["Reddit - Renewables"],
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
