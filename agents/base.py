from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from modules.base import BaseModule, RawItem

logger = logging.getLogger(__name__)


@dataclass
class ScoredItem:
    title: str
    url: str
    source: str
    published_at: str
    summary: str
    confidence_score: int
    is_spike: bool
    raw_score: int
    cross_source_count: int = 1  # inherited from RawItem


@dataclass
class PipelineContext:
    """Typed state passed between agents in the pipeline."""
    module: BaseModule
    raw_items: list[RawItem] = field(default_factory=list)
    scored_items: list[ScoredItem] = field(default_factory=list)
    top_items: list[ScoredItem] = field(default_factory=list)
    trend_heatmap: str = ""
    report_text: str = ""
    errors: list[str] = field(default_factory=list)


class BaseAgent(ABC):
    """Uniform interface for all pipeline agents: run(ctx) -> ctx."""

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @abstractmethod
    async def run(self, ctx: PipelineContext) -> PipelineContext:
        ...

    def _log(self, msg: str) -> None:
        logger.info(f"[{self.name}] {msg}")

    def _warn(self, msg: str) -> None:
        logger.warning(f"[{self.name}] {msg}")

    def _record_error(self, ctx: PipelineContext, msg: str) -> None:
        logger.error(f"[{self.name}] {msg}")
        ctx.errors.append(f"{self.name}: {msg}")
