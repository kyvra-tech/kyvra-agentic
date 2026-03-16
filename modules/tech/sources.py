from modules.base import BaseModule, DataSource
from modules.tech.config import KEYWORDS, SOURCE_AUTHORITY, X_AI_LEADER_ACCOUNTS
from modules.tech import prompts

_X_LEADER_QUERY = " OR ".join(f"from:{a}" for a in X_AI_LEADER_ACCOUNTS) + " -is:retweet lang:en"


class TechModule(BaseModule):
    name = "tech"

    def get_sources(self) -> list[DataSource]:
        return [
            # --- X (primary real-time sources) ---
            DataSource(
                name="X - AI Leaders",
                url="https://api.twitter.com/2/tweets/search/recent",
                source_type="x",
                params={"query": _X_LEADER_QUERY, "max_results": 10},
                authority_score=SOURCE_AUTHORITY["X - AI Leaders"],
            ),
            DataSource(
                name="X - AI Trending",
                url="https://api.twitter.com/2/tweets/search/recent",
                source_type="x",
                params={
                    "query": "(AI agent OR LLM OR Claude OR Gemini OR GPT) -is:retweet lang:en min_faves:100",
                    "max_results": 10,
                },
                authority_score=SOURCE_AUTHORITY["X - AI Trending"],
            ),
            DataSource(
                name="X - Indie Dev",
                url="https://api.twitter.com/2/tweets/search/recent",
                source_type="x",
                params={
                    "query": "(\"just launched\" OR \"just shipped\" OR \"I built\" OR \"indie hacker\") -is:retweet lang:en min_faves:50",
                    "max_results": 10,
                },
                authority_score=SOURCE_AUTHORITY["X - Indie Dev"],
            ),
            # --- Supplementary sources ---
            DataSource(
                name="HackerNews",
                url="https://hacker-news.firebaseio.com/v0/topstories.json",
                source_type="rest",
                params={"limit": 30},
                authority_score=SOURCE_AUTHORITY["HackerNews"],
            ),
            DataSource(
                name="GitHub Trending",
                url="https://github.com/trending",
                source_type="scrape",
                params={"language": "", "since": "daily"},
                authority_score=SOURCE_AUTHORITY["GitHub Trending"],
            ),
            DataSource(
                name="Anthropic Blog",
                url="https://www.anthropic.com/rss.xml",
                source_type="rss",
                authority_score=SOURCE_AUTHORITY["Anthropic Blog"],
            ),
            DataSource(
                name="OpenAI Blog",
                url="https://openai.com/news/rss.xml",
                source_type="rss",
                authority_score=SOURCE_AUTHORITY["OpenAI Blog"],
            ),
            DataSource(
                name="Google DeepMind Blog",
                url="https://deepmind.google/blog/rss.xml",
                source_type="rss",
                authority_score=SOURCE_AUTHORITY["Google DeepMind Blog"],
            ),
        ]

    def get_report_prompt(self, items: list[dict]) -> str:
        return prompts.build_report_prompt(items)

    def get_chat_system_prompt(self) -> str:
        return prompts.CHAT_SYSTEM_PROMPT

    def get_keywords(self) -> list[str]:
        return KEYWORDS
