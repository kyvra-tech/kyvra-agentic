from modules.base import BaseModule, DataSource
from modules.vietnam.config import KEYWORDS, SOURCE_AUTHORITY
from modules.vietnam import prompts


class VietnamModule(BaseModule):
    name = "vietnam"

    def get_sources(self) -> list[DataSource]:
        return [
            DataSource(
                name="VnExpress Tech",
                url="https://vnexpress.net/rss/khoa-hoc-cong-nghe.rss",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["VnExpress Tech"],
            ),
            DataSource(
                name="CafeF Tech",
                url="https://cafef.vn/cong-nghe.rss",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["CafeF Tech"],
            ),
            DataSource(
                name="ICTNews",
                url="https://ictnews.vn/rss/home.rss",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["ICTNews"],
            ),
            DataSource(
                name="TechInAsia VN",
                url="https://www.techinasia.com/feed",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["TechInAsia VN"],
            ),
        ]

    def get_report_prompt(self, items: list[dict]) -> str:
        return prompts.build_report_prompt(items)

    def get_thread_prompt(self, item: dict) -> str:
        return prompts.build_thread_prompt(item)

    def get_brief_prompt(self, items: list[dict]) -> str:
        return prompts.build_brief_prompt(items)

    def get_newsletter_prompt(self, item: dict) -> str:
        return prompts.build_newsletter_prompt(item)

    def get_script_prompt(self, item: dict) -> str:
        return prompts.build_script_prompt(item)

    def get_chat_system_prompt(self) -> str:
        return prompts.CHAT_SYSTEM_PROMPT

    def get_keywords(self) -> list[str]:
        return KEYWORDS
