from modules.base import BaseModule, DataSource
from modules.markets.config import KEYWORDS, SOURCE_AUTHORITY
from modules.markets import prompts


class MarketsModule(BaseModule):
    name = "markets"

    def get_sources(self) -> list[DataSource]:
        return [
            # ── NewsAPI: business category + market keyword search ─────────
            DataSource(
                name="NewsAPI - Business",
                url="https://newsapi.org/v2/top-headlines",
                source_type="newsapi",
                params={"endpoint": "top-headlines", "category": "business", "page_size": 20},
                authority_score=SOURCE_AUTHORITY["NewsAPI - Business"],
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="NewsAPI - Markets",
                url="https://newsapi.org/v2/everything",
                source_type="newsapi",
                params={
                    "endpoint": "everything",
                    "q": "stock market OR S&P 500 OR Federal Reserve OR interest rates OR earnings",
                    "sort_by": "publishedAt",
                    "page_size": 20,
                },
                authority_score=SOURCE_AUTHORITY["NewsAPI - Markets"],
                bypass_keyword_filter=True,
            ),
            # ── RSS: financial publications ────────────────────────────────
            DataSource(
                name="Reuters Business",
                url="https://feeds.reuters.com/reuters/businessNews",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["Reuters Business"],
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="MarketWatch",
                url="https://feeds.marketwatch.com/marketwatch/topstories/",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["MarketWatch"],
                bypass_keyword_filter=True,
            ),
            # ── Reddit RSS: retail investor sentiment ──────────────────────
            DataSource(
                name="Reddit - Investing",
                url="https://www.reddit.com/r/investing/new/.rss",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["Reddit - Investing"],
            ),
            DataSource(
                name="Reddit - StockMarket",
                url="https://www.reddit.com/r/StockMarket/new/.rss",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["Reddit - StockMarket"],
            ),
            DataSource(
                name="Reddit - WallStreetBets",
                url="https://www.reddit.com/r/wallstreetbets/new/.rss",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["Reddit - WallStreetBets"],
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
