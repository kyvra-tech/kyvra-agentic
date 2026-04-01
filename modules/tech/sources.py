from modules.base import BaseModule, DataSource
from modules.tech.config import KEYWORDS, SOURCE_AUTHORITY
from modules.tech import prompts


class TechModule(BaseModule):
    name = "tech"

    def get_sources(self) -> list[DataSource]:
        return [
            # ── Tier 1: curated tech newsletters & aggregators ────────────
            DataSource(
                name="TLDR Tech",
                url="https://tldr.tech/api/rss/tech",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("TLDR Tech", 15),
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="Hacker News",
                url="https://hnrss.org/frontpage",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("Hacker News", 16),
            ),
            # ── Tier 2: AI lab official feeds ─────────────────────────────
            DataSource(
                name="Anthropic Blog",
                url="https://www.anthropic.com/rss.xml",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("Anthropic Blog", 18),
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="OpenAI Blog",
                url="https://openai.com/blog/rss.xml",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("OpenAI Blog", 18),
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="Google DeepMind",
                url="https://deepmind.google/blog/rss.xml",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("Google DeepMind", 17),
                bypass_keyword_filter=True,
            ),
            # ── Tier 3: tech publications ──────────────────────────────────
            DataSource(
                name="TechCrunch",
                url="https://techcrunch.com/feed/",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("TechCrunch", 16),
            ),
            DataSource(
                name="The Verge",
                url="https://www.theverge.com/rss/index.xml",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("The Verge", 15),
            ),
            DataSource(
                name="Ars Technica",
                url="https://feeds.arstechnica.com/arstechnica/index",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("Ars Technica", 15),
            ),
            DataSource(
                name="MIT Tech Review",
                url="https://www.technologyreview.com/feed/",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY.get("MIT Tech Review", 17),
            ),
            # ── Tier 4: GitHub trending ────────────────────────────────────
            DataSource(
                name="GitHub Trending",
                url="https://github.com/trending",
                source_type="scrape",
                params={"language": "", "since": "daily"},
                authority_score=SOURCE_AUTHORITY.get("GitHub Trending", 14),
            ),
            # ── Tier 5: NewsAPI AI/tech keyword search ────────────────────
            DataSource(
                name="NewsAPI - AI",
                url="https://newsapi.org/v2/everything",
                source_type="newsapi",
                params={
                    "endpoint": "everything",
                    "q": "artificial intelligence OR LLM OR ChatGPT OR Claude AI OR Gemini AI",
                    "sort_by": "publishedAt",
                    "page_size": 15,
                },
                authority_score=SOURCE_AUTHORITY.get("NewsAPI - AI", 14),
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
