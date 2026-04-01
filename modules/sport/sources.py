from modules.base import BaseModule, DataSource
from modules.sport.config import KEYWORDS, SOURCE_AUTHORITY
from modules.sport import prompts


class SportModule(BaseModule):
    name = "sport"

    def get_sources(self) -> list[DataSource]:
        return [
            # ── Tier 1: major sports broadcasters ─────────────────────────
            DataSource(
                name="ESPN",
                url="https://www.espn.com/espn/rss/news",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("ESPN", 19),
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="BBC Sport",
                url="https://feeds.bbci.co.uk/sport/rss.xml",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("BBC Sport", 18),
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="Sky Sports",
                url="https://www.skysports.com/rss/12040",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("Sky Sports", 17),
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="Goal.com",
                url="https://www.goal.com/feeds/en/news",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("Goal.com", 16),
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="The Athletic",
                url="https://theathletic.com/feed/",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("The Athletic", 17),
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="Bleacher Report",
                url="https://bleacherreport.com/articles/feed",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("Bleacher Report", 15),
                bypass_keyword_filter=True,
            ),
            # ── Tier 2: NewsAPI sports ─────────────────────────────────────
            DataSource(
                name="NewsAPI - Sports",
                url="https://newsapi.org/v2/top-headlines",
                source_type="newsapi",
                params={"endpoint": "top-headlines", "category": "sports", "page_size": 20},
                authority_score=SOURCE_AUTHORITY.get("NewsAPI - Sports", 15),
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
        return (50, 300)
