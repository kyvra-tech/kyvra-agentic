from __future__ import annotations

from modules.base import BaseModule, DataSource
from modules.vietnam.config import KEYWORDS, SOURCE_AUTHORITY
from modules.vietnam import prompts


class VietnamModule(BaseModule):
    name = "vietnam"

    def get_sources(self) -> list[DataSource]:
        return [
            DataSource(
                name="Kenh14 Star",
                url="https://kenh14.vn/star.rss",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["Kenh14 Star"],
            ),
            DataSource(
                name="Kenh14 Doi Song",
                url="https://kenh14.vn/doi-song.rss",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["Kenh14 Doi Song"],
            ),
            DataSource(
                name="Ngoisao Hau Truong",
                url="https://ngoisao.vnexpress.net/rss/hau-truong.rss",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["Ngoisao Hau Truong"],
            ),
            DataSource(
                name="Ngoisao Lam Dep",
                url="https://ngoisao.vnexpress.net/rss/lam-dep.rss",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["Ngoisao Lam Dep"],
            ),
            DataSource(
                name="Google News - Bar San",
                url="https://news.google.com/rss/search?q=bar+lounge+club+qu%E1%BB%95y+nightlife&hl=vi&gl=VN&ceid=VN:vi",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["Google News - Bar San"],
            ),
            DataSource(
                name="Google News - Gai Xinh",
                url="https://news.google.com/rss/search?q=g%C3%A1i+xinh+hot+girl+l%C3%A0m+%C4%91%E1%BBA1p+th%E1%BB%9Di+trang&hl=vi&gl=VN&ceid=VN:vi",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["Google News - Gai Xinh"],
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

    def get_chat_system_prompt(self) -> str:
        return prompts.CHAT_SYSTEM_PROMPT

    def get_keywords(self) -> list[str]:
        return KEYWORDS
