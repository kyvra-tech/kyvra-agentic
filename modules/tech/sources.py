from modules.base import BaseModule, DataSource
from modules.tech.config import (
    KEYWORDS, SOURCE_AUTHORITY,
    X_AI_LAB_ACCOUNTS, X_AI_LEADER_ACCOUNTS,
    X_SOFTWARE_ENG_ACCOUNTS, X_INDIE_BUILDER_ACCOUNTS,
    X_AI_RESEARCH_ACCOUNTS,
)
from modules.tech import prompts

_X_LABS_QUERY = (
    " OR ".join(f"from:{a}" for a in X_AI_LAB_ACCOUNTS)
    + " -is:retweet lang:en"
)
_X_LEADERS_QUERY = (
    " OR ".join(f"from:{a}" for a in X_AI_LEADER_ACCOUNTS)
    + " -is:retweet lang:en"
)
_X_SWE_QUERY = (
    " OR ".join(f"from:{a}" for a in X_SOFTWARE_ENG_ACCOUNTS)
    + " -is:retweet lang:en"
)
_X_INDIE_QUERY = (
    " OR ".join(f"from:{a}" for a in X_INDIE_BUILDER_ACCOUNTS)
    + " -is:retweet lang:en"
)
_X_RESEARCH_QUERY = (
    " OR ".join(f"from:{a}" for a in X_AI_RESEARCH_ACCOUNTS)
    + " -is:retweet lang:en"
)


class TechModule(BaseModule):
    name = "tech"

    def get_sources(self) -> list[DataSource]:
        return [
            # ── X: account-based, primary signal ──────────────────────────
            DataSource(
                name="X - AI Labs",
                url="https://api.twitter.com/2/tweets/search/recent",
                source_type="x",
                params={"query": _X_LABS_QUERY, "max_results": 10},
                authority_score=SOURCE_AUTHORITY["X - AI Labs"],
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="X - AI Leaders",
                url="https://api.twitter.com/2/tweets/search/recent",
                source_type="x",
                params={"query": _X_LEADERS_QUERY, "max_results": 10},
                authority_score=SOURCE_AUTHORITY["X - AI Leaders"],
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="X - Software Eng",
                url="https://api.twitter.com/2/tweets/search/recent",
                source_type="x",
                params={"query": _X_SWE_QUERY, "max_results": 10},
                authority_score=SOURCE_AUTHORITY["X - Software Eng"],
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="X - Indie Builders",
                url="https://api.twitter.com/2/tweets/search/recent",
                source_type="x",
                params={"query": _X_INDIE_QUERY, "max_results": 10},
                authority_score=SOURCE_AUTHORITY["X - Indie Builders"],
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="X - AI Research",
                url="https://api.twitter.com/2/tweets/search/recent",
                source_type="x",
                params={"query": _X_RESEARCH_QUERY, "max_results": 10},
                authority_score=SOURCE_AUTHORITY["X - AI Research"],
                bypass_keyword_filter=True,
            ),
            # ── X: keyword-based signal discovery ─────────────────────────
            DataSource(
                name="X - AI Trending",
                url="https://api.twitter.com/2/tweets/search/recent",
                source_type="x",
                params={
                    "query": "(AI agent OR LLM OR Claude OR Gemini OR GPT OR MCP) -is:retweet lang:en",
                    "max_results": 10,
                },
                authority_score=SOURCE_AUTHORITY["X - AI Trending"],
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="X - AI Tools",
                url="https://api.twitter.com/2/tweets/search/recent",
                source_type="x",
                params={
                    "query": "(cursor AI OR copilot OR replit OR \"v0.dev\" OR lovable OR windsurf) -is:retweet lang:en",
                    "max_results": 10,
                },
                authority_score=SOURCE_AUTHORITY["X - AI Tools"],
                bypass_keyword_filter=True,
            ),
            DataSource(
                name="X - OSS",
                url="https://api.twitter.com/2/tweets/search/recent",
                source_type="x",
                params={
                    "query": "(\"open source\" OR \"just open sourced\" OR \"MIT license\" OR \"github stars\") (AI OR LLM OR model) -is:retweet lang:en",
                    "max_results": 10,
                },
                authority_score=SOURCE_AUTHORITY["X - OSS"],
                bypass_keyword_filter=True,
            ),
            # ── GitHub Trending: native dev signal ────────────────────────
            DataSource(
                name="GitHub Trending",
                url="https://github.com/trending",
                source_type="scrape",
                params={"language": "", "since": "daily"},
                authority_score=SOURCE_AUTHORITY["GitHub Trending"],
            ),
        ]

    def get_report_prompt(self, items: list[dict]) -> str:
        return prompts.build_report_prompt(items)

    def get_thread_prompt(self, item: dict) -> str:
        return prompts.build_thread_prompt(item)

    def get_chat_system_prompt(self) -> str:
        return prompts.CHAT_SYSTEM_PROMPT

    def get_keywords(self) -> list[str]:
        return KEYWORDS
