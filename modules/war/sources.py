from modules.base import BaseModule, DataSource
from modules.war.config import KEYWORDS, SOURCE_AUTHORITY
from modules.war import prompts


class WarModule(BaseModule):
    name = "war"

    def get_sources(self) -> list[DataSource]:
        return [
            DataSource(
                name="Kyiv Independent",
                url="https://kyivindependent.com/feed/",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["Kyiv Independent"],
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="Al Jazeera",
                url="https://www.aljazeera.com/xml/rss/all.xml",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["Al Jazeera"],
            ),
            DataSource(
                name="Reuters",
                url="https://feeds.reuters.com/reuters/worldNews",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["Reuters"],
            ),
            DataSource(
                name="BBC News",
                url="https://feeds.bbci.co.uk/news/world/rss.xml",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["BBC News"],
            ),
            DataSource(
                name="AP News",
                url="https://rsshub.app/apnews/topics/war-and-conflicts",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["AP News"],
            ),
            DataSource(
                name="The Guardian",
                url="https://www.theguardian.com/world/rss",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["The Guardian"],
            ),
            DataSource(
                name="Reddit - Ukraine",
                url="https://www.reddit.com/r/ukraine/new/.rss",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["Reddit - Ukraine"],
            ),
            DataSource(
                name="Reddit - WorldNews",
                url="https://www.reddit.com/r/worldnews/new/.rss",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["Reddit - WorldNews"],
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
        return (30, 200)  # lower thresholds — war news spikes fast
