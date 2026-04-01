from modules.base import BaseModule, DataSource
from modules.political.config import KEYWORDS, SOURCE_AUTHORITY
from modules.political import prompts


class PoliticalModule(BaseModule):
    name = "political"

    def get_sources(self) -> list[DataSource]:
        return [
            # ── Tier 1: wire services ──────────────────────────────────────
            DataSource(
                name="Reuters Politics",
                url="https://feeds.reuters.com/reuters/politicsNews",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("Reuters", 20),
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="AP News",
                url="https://rsshub.app/apnews/topics/politics",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("AP News", 19),
                bypass_keyword_filter=True,
            ),
            # ── Tier 2: international broadcasters ────────────────────────
            DataSource(
                name="BBC News Politics",
                url="https://feeds.bbci.co.uk/news/politics/rss.xml",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("BBC News", 19),
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="Al Jazeera",
                url="https://www.aljazeera.com/xml/rss/all.xml",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("Al Jazeera", 17),
            ),
            DataSource(
                name="The Guardian Politics",
                url="https://www.theguardian.com/politics/rss",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("The Guardian", 16),
            ),
            DataSource(
                name="Politico",
                url="https://www.politico.com/rss/politicopicks.xml",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("Politico", 17),
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="The Hill",
                url="https://thehill.com/feed/",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("The Hill", 15),
            ),
            # ── Tier 3: NewsAPI politics ───────────────────────────────────
            DataSource(
                name="NewsAPI - Politics",
                url="https://newsapi.org/v2/top-headlines",
                source_type="newsapi",
                params={"endpoint": "top-headlines", "category": "general", "page_size": 15},
                authority_score=SOURCE_AUTHORITY.get("NewsAPI - Politics", 14),
                bypass_keyword_filter=False,
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
