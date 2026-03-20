from modules.base import BaseModule, DataSource
from modules.indie.config import KEYWORDS, SOURCE_AUTHORITY
from modules.tech.config import X_INDIE_BUILDER_ACCOUNTS
from modules.indie import prompts

# Curated indie hackers / builders on X — primary real-time signal
_X_INDIE_QUERY = (
    " OR ".join(f"from:{a}" for a in X_INDIE_BUILDER_ACCOUNTS)
    + " -is:retweet lang:en"
)


class IndieModule(BaseModule):
    name = "indie"

    def get_sources(self) -> list[DataSource]:
        return [
            # ── X: indie builders — primary real-time signal ───────────────
            DataSource(
                name="X - Indie Builders",
                url="https://api.twitter.com/2/tweets/search/recent",
                source_type="x",
                params={"query": _X_INDIE_QUERY, "max_results": 15},
                authority_score=SOURCE_AUTHORITY["X - Indie Builders"],
                bypass_keyword_filter=True,
            ),
            # ── RSS: community & launch platforms ─────────────────────────
            DataSource(
                name="Hacker News",
                url="https://news.ycombinator.com/rss",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["Hacker News"],
            ),
            DataSource(
                name="IndieHackers",
                url="https://www.indiehackers.com/feed.rss",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["IndieHackers"],
            ),
            DataSource(
                name="Reddit - SideProject",
                url="https://www.reddit.com/r/SideProject/new/.rss",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["Reddit - SideProject"],
            ),
            DataSource(
                name="Product Hunt",
                url="https://www.producthunt.com/feed",
                source_type="rss",
                params={},
                authority_score=SOURCE_AUTHORITY["Product Hunt"],
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

    def get_spike_thresholds(self) -> tuple[int, int]:
        # Indie X: lower bar — 200 likes signals viral for this niche
        # No GitHub Trending source, so github threshold is unused (set high)
        return (9999, 200)
