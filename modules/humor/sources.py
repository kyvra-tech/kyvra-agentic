from modules.base import BaseModule, DataSource
from modules.humor.config import KEYWORDS, SOURCE_AUTHORITY
from modules.humor import prompts


class HumorModule(BaseModule):
    name = "humor"

    def get_sources(self) -> list[DataSource]:
        return [
            # ── NewsAPI: entertainment category ───────────────────────────
            DataSource(
                name="NewsAPI - Entertainment",
                url="https://newsapi.org/v2/top-headlines",
                source_type="newsapi",
                params={"endpoint": "top-headlines", "category": "entertainment", "page_size": 20},
                authority_score=SOURCE_AUTHORITY["NewsAPI - Entertainment"],
                bypass_keyword_filter=True,
            ),
            # ── RSS: trade publications ────────────────────────────────────
            DataSource(
                name="Variety",
                url="https://variety.com/feed/",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["Variety"],
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="Hollywood Reporter",
                url="https://www.hollywoodreporter.com/feed/",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["Hollywood Reporter"],
                bypass_keyword_filter=True,
            ),
            # ── Reddit RSS: community signal ───────────────────────────────
            DataSource(
                name="Reddit - Movies",
                url="https://www.reddit.com/r/movies/new/.rss",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["Reddit - Movies"],
            ),
            DataSource(
                name="Reddit - Television",
                url="https://www.reddit.com/r/television/new/.rss",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["Reddit - Television"],
            ),
            DataSource(
                name="Reddit - Entertainment",
                url="https://www.reddit.com/r/entertainment/new/.rss",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["Reddit - Entertainment"],
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

    def get_spike_thresholds(self) -> tuple[int, int]:
        # Entertainment moves fast — lower thresholds
        return (50, 200)
