import asyncio
import copy
import logging
import time
from collections import Counter
from agents.base import PipelineContext
from agents.data_collector import DataCollectorAgent
from agents.analyst import AnalystAgent
from agents.narrative_scout import NarrativeScoutAgent
from agents.content_writer import ContentWriterAgent
from modules.base import BaseModule
import services.memory as memory

logger = logging.getLogger(__name__)

# In-memory cache of the last pipeline result per module.
# Keyed by module name → {timestamp: float, status: dict}
_STATUS_CACHE: dict[str, dict] = {}
_STATUS_CACHE_TTL = 7200  # 2 hours


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
            return "No news today. Try again later!"

        ctx = await self.writer.run(ctx)

        # Mark delivered items as seen (story continuity) and refresh status cache.
        if ctx.top_items:
            memory.mark_seen([i.url for i in ctx.top_items], self.module.name)
            _STATUS_CACHE[self.module.name] = {
                "timestamp": time.time(),
                "status": self._build_status_dict(ctx),
            }

        if ctx.errors:
            logger.warning(f"[Supervisor] {len(ctx.errors)} error(s): {ctx.errors}")
            footer = f"\n\n⚠️ _{len(ctx.errors)} source(s) had issues and were skipped._"
            report = ctx.report_text or "Could not generate report."
            return report + footer
        logger.info("[Supervisor] Pipeline complete.")
        return ctx.report_text or "Could not generate report."

    @staticmethod
    def _item_dict(item) -> dict:
        return {
            "title": item.title,
            "url": item.url,
            "source": item.source,
            "published_at": item.published_at,
            "summary": item.summary,
            "confidence_score": item.confidence_score,
            "is_spike": item.is_spike,
        }

    async def _generate_content_format(
        self,
        format_name: str,
        get_prompt,
        max_tokens: int,
        use_top3: bool = False,
        user_id: int | None = None,
        rank: int = 1,
    ) -> str:
        """Shared pipeline for single-item (or top-3) content format generation.

        format_name  — label for log lines (e.g. "brief", "thread")
        get_prompt   — callable: (item_or_items, voice) -> str
        max_tokens   — passed to LLM
        use_top3     — True for brief (top-3 items), False for thread/newsletter/script (top-1)
        user_id      — Telegram user ID; used to load voice profile from memory
        rank         — 1-based index into top_items by confidence_score (default: 1 = highest)
        """
        import services.llm as llm
        logger.info("[Supervisor] %s generation started (rank=%d)...", format_name.capitalize(), rank)
        ctx = await self._collect_and_score()

        if not ctx.top_items:
            return f"No news today to build a {format_name} from. Try again later!"

        voice = memory.get_voice_profile(user_id) if user_id is not None else None

        # Clamp rank to available items (rank is 1-based)
        clamped_rank = max(1, min(rank, len(ctx.top_items)))
        selected_item = ctx.top_items[clamped_rank - 1]

        if use_top3:
            payload = [self._item_dict(i) for i in ctx.top_items[:3]]
        else:
            payload = self._item_dict(selected_item)

        prompt = get_prompt(payload, voice)
        try:
            result = await llm.complete(prompt, max_tokens=max_tokens)
        except Exception as e:
            logger.error("[Supervisor] %s LLM call failed: %s", format_name, e)
            return f"Could not generate {format_name} right now. Try again later!"
        logger.info("[Supervisor] %s generated.", format_name.capitalize())
        return result

    async def generate_brief(self, user_id: int | None = None, rank: int = 1) -> str:
        """Generate a 3-bullet shareable brief from today's top 3 items."""
        return await self._generate_content_format(
            "brief",
            lambda items, voice: self.module.get_brief_prompt(items, voice=voice),
            400,
            use_top3=True,
            user_id=user_id,
            rank=rank,
        )

    async def generate_thread(self, user_id: int | None = None, rank: int = 1) -> str:
        """Generate a Twitter thread from today's top-scored item."""
        return await self._generate_content_format(
            "thread",
            lambda item, voice: self.module.get_thread_prompt(item, voice=voice),
            1200,
            user_id=user_id,
            rank=rank,
        )

    def _build_status_dict(self, ctx: PipelineContext) -> dict:
        return {
            "module": ctx.module.name,
            "total_fetched": len(ctx.raw_items),
            "top_score": ctx.top_items[0].confidence_score if ctx.top_items else 0,
            "spikes": sum(1 for i in ctx.scored_items if i.is_spike),
            "sources": Counter(item.source for item in ctx.raw_items),
        }

    async def get_status(self) -> dict:
        """Return status dict, using the cached result from the last pipeline run if fresh."""
        cached = _STATUS_CACHE.get(self.module.name)
        if cached and (time.time() - cached["timestamp"]) < _STATUS_CACHE_TTL:
            logger.info("[Supervisor] Returning cached status for module '%s'", self.module.name)
            return cached["status"]
        # Cache miss or stale — run a live scan
        ctx = await self._collect_and_score()
        status = self._build_status_dict(ctx)
        _STATUS_CACHE[self.module.name] = {"timestamp": time.time(), "status": status}
        return status

    async def generate_newsletter(self, user_id: int | None = None, rank: int = 1) -> str:
        """Generate a newsletter section from today's top-scored item."""
        return await self._generate_content_format(
            "newsletter",
            lambda item, voice: self.module.get_newsletter_prompt(item, voice=voice),
            800,
            user_id=user_id,
            rank=rank,
        )

    async def generate_script(self, user_id: int | None = None, rank: int = 1) -> str:
        """Generate a TikTok/Reels voiceover script from today's top-scored item."""
        return await self._generate_content_format(
            "script",
            lambda item, voice: self.module.get_script_prompt(item, voice=voice),
            600,
            user_id=user_id,
            rank=rank,
        )

    async def generate_tweet_hook(self, rank: int = 1) -> str:
        """Generate a single viral tweet hook for story #rank using the last cached pipeline result."""
        import services.llm as llm

        # Re-use cached status items if available, else do a quick scan
        cached = _STATUS_CACHE.get(self.module.name)
        if cached and (time.time() - cached["timestamp"]) < _STATUS_CACHE_TTL:
            # We have a recent pipeline run — re-collect to get top_items
            pass  # fall through to quick scan below

        ctx = await self._collect_and_score()
        if not ctx.top_items:
            return "No stories available right now."

        clamped = max(1, min(rank, len(ctx.top_items)))
        item = ctx.top_items[clamped - 1]
        prompt = self.module.get_tweet_hook_prompt(self._item_dict(item))

        try:
            return await llm.complete(prompt, max_tokens=120)
        except Exception as e:
            logger.error("[Supervisor] tweet_hook LLM call failed: %s", e)
            return "Could not generate tweet. Try again later."

    async def generate_report_with_ctx(self) -> tuple[str, "PipelineContext | None"]:
        """Full pipeline — returns (report_text, ctx) so callers can access top_items."""
        logger.info("[Supervisor] Starting full pipeline (with ctx)...")
        ctx = await self._collect_and_score()

        if not ctx.raw_items:
            return "No news today. Try again later!", None

        ctx = await self.writer.run(ctx)

        if ctx.top_items:
            memory.mark_seen([i.url for i in ctx.top_items], self.module.name)
            _STATUS_CACHE[self.module.name] = {
                "timestamp": time.time(),
                "status": self._build_status_dict(ctx),
            }

        if ctx.errors:
            logger.warning(f"[Supervisor] {len(ctx.errors)} error(s): {ctx.errors}")
            footer = f"\n\n⚠️ _{len(ctx.errors)} source(s) had issues and were skipped._"
            report = ctx.report_text or "Could not generate report."
            return report + footer, ctx
        logger.info("[Supervisor] Pipeline complete.")
        return ctx.report_text or "Could not generate report.", ctx

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
            return f"No news found for *{topic}* today."

        ctx = await self.writer.run(ctx)
        return ctx.report_text or "Could not generate report."


async def generate_report_for_module(module_name: str) -> str:
    """Convenience: load a module by name and run the full report pipeline."""
    module = load_module(module_name)
    supervisor = SupervisorAgent(module)
    return await supervisor.generate_report()


async def generate_report_for_module_with_ctx(module_name: str):
    """Like generate_report_for_module but also returns the pipeline context (for TrendPost push)."""
    module = load_module(module_name)
    supervisor = SupervisorAgent(module)
    return await supervisor.generate_report_with_ctx()


def load_module(module_name: str) -> BaseModule:
    from modules.tech.sources import TechModule
    from modules.crypto.sources import CryptoModule
    from modules.vietnam.sources import VietnamModule
    from modules.indie.sources import IndieModule

    registry: dict[str, type[BaseModule]] = {
        "tech":    TechModule,
        "crypto":  CryptoModule,
        "vietnam": VietnamModule,
        "indie":   IndieModule,
    }
    cls = registry.get(module_name)
    if cls is None:
        raise ValueError(f"Unknown module: '{module_name}'. Available: {list(registry)}")
    return cls()
