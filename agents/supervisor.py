import asyncio
import copy
import logging
from agents.base import PipelineContext
from agents.data_collector import DataCollectorAgent
from agents.analyst import AnalystAgent
from agents.narrative_scout import NarrativeScoutAgent
from agents.content_writer import ContentWriterAgent
from modules.base import BaseModule

logger = logging.getLogger(__name__)


class SupervisorAgent:
    """Orchestrates the pipeline with parallel execution where possible.

    Phase 1 — DataCollector   (sequential: all others depend on raw_items)
    Phase 2 — Analyst + NarrativeScout  (parallel: both only read raw_items)
    Phase 3 — ContentWriter   (sequential: needs scored_items + trend_heatmap)
    """

    def __init__(self, module: BaseModule):
        self.module = module
        self.collector = DataCollectorAgent()
        self.analyst = AnalystAgent()
        self.scout = NarrativeScoutAgent()
        self.writer = ContentWriterAgent()

    async def _collect_and_score(self) -> PipelineContext:
        """Phases 1 + 2: collect → (analyst ∥ scout). No LLM call."""
        ctx = PipelineContext(module=self.module)

        ctx = await self.collector.run(ctx)

        analyst_ctx, scout_ctx = await asyncio.gather(
            self.analyst.run(copy.copy(ctx)),
            self.scout.run(copy.copy(ctx)),
        )
        ctx.scored_items  = analyst_ctx.scored_items
        ctx.top_items     = analyst_ctx.top_items
        ctx.trend_heatmap = scout_ctx.trend_heatmap
        ctx.errors += analyst_ctx.errors + scout_ctx.errors
        return ctx

    async def quick_scan(self) -> PipelineContext:
        """Collect + score only — skips LLM. Fast, cheap, used by /update and /breaking."""
        logger.info("[Supervisor] Quick scan started...")
        ctx = await self._collect_and_score()
        logger.info("[Supervisor] Quick scan complete.")
        return ctx

    async def generate_report(self) -> str:
        """Full pipeline including LLM report generation."""
        logger.info("[Supervisor] Starting full pipeline...")
        ctx = await self._collect_and_score()

        if not ctx.raw_items:
            return "Không có tin tức hôm nay. Thử lại sau!"

        ctx = await self.writer.run(ctx)

        if ctx.errors:
            logger.warning(f"[Supervisor] {len(ctx.errors)} error(s): {ctx.errors}")
            footer = f"\n\n⚠️ _{len(ctx.errors)} source(s) had issues and were skipped._"
            report = ctx.report_text or "Không thể tạo report."
            return report + footer
        logger.info("[Supervisor] Pipeline complete.")
        return ctx.report_text or "Không thể tạo report."

    async def generate_report_for_topic(self, topic: str) -> str:
        """Full pipeline scoped to items matching a topic keyword."""
        logger.info(f"[Supervisor] Topic pipeline: '{topic}'")
        ctx = await self._collect_and_score()

        # Filter scored items to topic
        kw = topic.lower()
        ctx.scored_items = [
            i for i in ctx.scored_items
            if kw in (i.title + " " + i.summary).lower()
        ]
        ctx.top_items = ctx.scored_items[:7]

        if not ctx.top_items:
            return f"Không tìm thấy tin nào về *{topic}* hôm nay."

        ctx = await self.writer.run(ctx)
        return ctx.report_text or "Không thể tạo report."


def load_module(module_name: str) -> BaseModule:
    if module_name == "tech":
        from modules.tech.sources import TechModule
        return TechModule()
    raise ValueError(f"Unknown module: {module_name}")
