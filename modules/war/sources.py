from modules.base import BaseModule, DataSource
from modules.war.config import KEYWORDS, SOURCE_AUTHORITY
from modules.war import prompts


class WarModule(BaseModule):
    name = "war"

    def get_sources(self) -> list[DataSource]:
        return [
            # ── Tier 1: conflict-specialist outlets ───────────────────────
            DataSource(
                name="Kyiv Independent",
                url="https://kyivindependent.com/feed/",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("Kyiv Independent", 18),
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="Middle East Eye",
                url="https://www.middleeasteye.net/rss",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("Middle East Eye", 16),
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="Defense News",
                url="https://www.defensenews.com/arc/outboundfeeds/rss/",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("Defense News", 16),
                bypass_keyword_filter=True,
            ),
            # ── Tier 2: wire services / international ─────────────────────
            DataSource(
                name="Reuters World",
                url="https://feeds.reuters.com/reuters/worldNews",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("Reuters", 20),
            ),
            DataSource(
                name="BBC World",
                url="https://feeds.bbci.co.uk/news/world/rss.xml",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("BBC News", 19),
            ),
            DataSource(
                name="Al Jazeera",
                url="https://www.aljazeera.com/xml/rss/all.xml",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("Al Jazeera", 17),
            ),
            DataSource(
                name="AP News World",
                url="https://rsshub.app/apnews/topics/war-and-conflicts",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("AP News", 19),
            ),
            # ── Tier 3: NewsAPI conflict keyword search ───────────────────
            DataSource(
                name="NewsAPI - War",
                url="https://newsapi.org/v2/everything",
                source_type="newsapi",
                params={
                    "endpoint": "everything",
                    "q": "war OR conflict OR military OR ceasefire OR missile OR NATO",
                    "sort_by": "publishedAt",
                    "page_size": 15,
                },
                authority_score=SOURCE_AUTHORITY.get("NewsAPI - War", 14),
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

    def get_tweet_hook_prompt(self, item: dict) -> str:
        return prompts.build_tweet_hook_prompt(item)

    def get_chat_system_prompt(self) -> str:
        return prompts.CHAT_SYSTEM_PROMPT

    def get_keywords(self) -> list[str]:
        return KEYWORDS

    def get_spike_thresholds(self) -> tuple[int, int]:
        return (30, 200)
