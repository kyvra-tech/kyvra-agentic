from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class DataSource:
    name: str
    url: str
    source_type: str  # "rss" | "rest" | "scrape"
    params: dict = field(default_factory=dict)
    authority_score: int = 10  # 0-20, added to confidence scoring


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
    def get_keywords(self) -> list[str]:
        """Return keywords used for relevance filtering."""
        ...
