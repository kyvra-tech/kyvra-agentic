from modules.base import BaseModule, DataSource
from modules.markets.config import KEYWORDS, SOURCE_AUTHORITY
from modules.markets import prompts


class MarketsModule(BaseModule):
    name = "markets"

    def get_sources(self) -> list[DataSource]:
        return [
            # ── Tier 1: financial wire & publications ──────────────────────
            DataSource(
                name="Reuters Business",
                url="https://feeds.reuters.com/reuters/businessNews",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("Reuters Business", 20),
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="MarketWatch",
                url="https://feeds.marketwatch.com/marketwatch/topstories/",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("MarketWatch", 17),
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="Financial Times",
                url="https://www.ft.com/rss/home",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("Financial Times", 19),
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="Seeking Alpha",
                url="https://seekingalpha.com/feed.xml",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("Seeking Alpha", 15),
            ),
            DataSource(
                name="Investopedia",
                url="https://www.investopedia.com/feedbuilder/feed/getfeed/?feedName=rss_headline",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("Investopedia", 15),
            ),
            # ── Tier 2: NewsAPI business + markets ────────────────────────
            DataSource(
                name="NewsAPI - Business",
                url="https://newsapi.org/v2/top-headlines",
                source_type="newsapi",
                params={"endpoint": "top-headlines", "category": "business", "page_size": 20},
                authority_score=SOURCE_AUTHORITY.get("NewsAPI - Business", 16),
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="NewsAPI - Markets",
                url="https://newsapi.org/v2/everything",
                source_type="newsapi",
                params={
                    "endpoint": "everything",
                    "q": "stock market OR S&P 500 OR Federal Reserve OR interest rates OR Wall Street",
                    "sort_by": "publishedAt",
                    "page_size": 15,
                },
                authority_score=SOURCE_AUTHORITY.get("NewsAPI - Markets", 15),
                bypass_keyword_filter=True,
            ),
            # ── Tier 3: Google News markets ────────────────────────────────
            DataSource(
                name="Google News - Markets",
                url="https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("Google News - Markets", 13),
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
