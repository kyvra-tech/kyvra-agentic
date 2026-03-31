from modules.base import BaseModule, DataSource
from modules.parody.config import KEYWORDS, SOURCE_AUTHORITY
from modules.parody import prompts


class ParodyModule(BaseModule):
    name = "parody"

    def get_sources(self) -> list[DataSource]:
        return [
            DataSource(
                name="The Onion",
                url="https://www.theonion.com/rss",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["The Onion"],
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="ClickHole",
                url="https://clickhole.com/feed/",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["ClickHole"],
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="Reddit - NotTheOnion",
                url="https://www.reddit.com/r/nottheonion/new/.rss",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["Reddit - NotTheOnion"],
            ),
            DataSource(
                name="Reddit - Funny",
                url="https://www.reddit.com/r/funny/new/.rss",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["Reddit - Funny"],
            ),
            DataSource(
                name="Reddit - Unexpected",
                url="https://www.reddit.com/r/Unexpected/new/.rss",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["Reddit - Unexpected"],
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
