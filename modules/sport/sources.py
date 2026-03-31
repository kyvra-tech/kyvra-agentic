from modules.base import BaseModule, DataSource
from modules.sport.config import KEYWORDS, SOURCE_AUTHORITY
from modules.sport import prompts


class SportModule(BaseModule):
    name = "sport"

    def get_sources(self) -> list[DataSource]:
        return [
            DataSource(
                name="ESPN",
                url="https://www.espn.com/espn/rss/news",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["ESPN"],
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="BBC Sport",
                url="https://feeds.bbci.co.uk/sport/rss.xml",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["BBC Sport"],
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="Sky Sports",
                url="https://www.skysports.com/rss/12040",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["Sky Sports"],
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="Goal.com",
                url="https://www.goal.com/feeds/en/news",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["Goal.com"],
            ),
            DataSource(
                name="Reddit - Soccer",
                url="https://www.reddit.com/r/soccer/new/.rss",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["Reddit - Soccer"],
            ),
            DataSource(
                name="Reddit - NBA",
                url="https://www.reddit.com/r/nba/new/.rss",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["Reddit - NBA"],
            ),
            DataSource(
                name="Reddit - NFL",
                url="https://www.reddit.com/r/nfl/new/.rss",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["Reddit - NFL"],
            ),
            DataSource(
                name="Reddit - UFC",
                url="https://www.reddit.com/r/ufc/new/.rss",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["Reddit - UFC"],
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
        return (50, 300)  # lower thresholds — sports content spikes faster
