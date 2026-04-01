from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class DataSource:
    name: str
    url: str
    source_type: str  # "rss" | "rest" | "scrape"
    params: dict = field(default_factory=dict)
    authority_score: int = 10  # 0-20, added to confidence scoring
    bypass_keyword_filter: bool = False  # True for pre-curated sources (e.g. X queries)


@dataclass
class RawItem:
    title: str
    url: str
    source: str
    published_at: str  # ISO 8601
    summary: str = ""
    score: int = 0      # raw engagement score from source
    comments: int = 0
    authority_score: int = 10
    cross_source_count: int = 1  # how many sources covered this story (trending signal)


class BaseModule(ABC):
    name: str = "base"

    @abstractmethod
    def get_sources(self) -> list[DataSource]:
        """Return list of data sources for this module."""
        ...

    @abstractmethod
    def get_report_prompt(self, items: list[dict]) -> str:
        """Return the Claude prompt to generate the daily report."""
        ...

    @abstractmethod
    def get_chat_system_prompt(self) -> str:
        """Return the system prompt for chat mode."""
        ...

    @abstractmethod
    def get_thread_prompt(self, item: dict, voice: str | None = None) -> str:
        """Return the prompt to generate a Twitter thread from a single top item."""
        ...

    @abstractmethod
    def get_brief_prompt(self, items: list[dict], voice: str | None = None) -> str:
        """Return the prompt to generate a 3-bullet shareable brief."""
        ...

    @abstractmethod
    def get_newsletter_prompt(self, item: dict, voice: str | None = None) -> str:
        """Return the prompt to generate a newsletter section from a single top item."""
        ...

    @abstractmethod
    def get_script_prompt(self, item: dict, voice: str | None = None) -> str:
        """Return the prompt to generate a TikTok/Reels voiceover script from a single top item."""
        ...

    @abstractmethod
    def get_keywords(self) -> list[str]:
        """Return keywords used for relevance filtering."""
        ...

    def get_tweet_hook_prompt(self, item: dict, lang: str = "en") -> str:
        """Return the prompt to generate a single viral tweet hook for a story."""
        lang_instruction = (
            "Write the tweet in Japanese (日本語). Use natural, fluent Japanese suitable for Twitter/X."
            if lang == "ja"
            else "Write the tweet in English."
        )
        return (
            f"Write 1 compelling tweet hook (max 280 chars) about this story.\n"
            f"{lang_instruction}\n"
            f"Title: {item['title']}\nURL: {item['url']}\nSummary: {item['summary']}\n"
            f"Output ONLY the tweet text, no explanation."
        )

    def get_spike_thresholds(self) -> tuple[int, int]:
        """Return (github_stars_spike, x_likes_spike) thresholds for this module.

        Override in subclasses to tune spike sensitivity per niche.
        Defaults: GitHub 100 stars/day, X 500 likes.
        """
        return (100, 500)
