"""
GraphRunner — drop-in replacement for SupervisorAgent, backed by kyvra_graph.

Teaching notes
--------------
This is the "adapter" pattern: we wrap the new LangGraph graph with the same
public API that handlers.py and web/app.py expect.  This lets us swap out
the orchestration engine without rewriting all 15 Telegram commands at once.

Compare SupervisorAgent vs GraphRunner:
  SupervisorAgent:  hand-rolled asyncio.gather + manual PipelineContext threading
  GraphRunner:      kyvra_graph.ainvoke(state) — LangGraph handles parallelism

Both expose the same methods so the callers don't need to know which one runs.

Progress streaming (Phase 6) is added to GraphRunner.run_with_stream() which
handlers.py can call when it wants live Telegram progress updates.
"""

from __future__ import annotations

import logging
import time
from collections import Counter
from typing import AsyncIterator

from agents.graph import kyvra_graph
from agents.registry import load_module
from agents.state import KyvraState, empty_state
import services.memory as memory
import services.llm as llm

logger = logging.getLogger(__name__)

# Status cache (same as SupervisorAgent._STATUS_CACHE — shared via module name key)
_STATUS_CACHE: dict[str, dict] = {}
_STATUS_CACHE_TTL = 7200


class GraphRunner:
    """Graph-backed orchestrator.  Public API mirrors SupervisorAgent."""

    def __init__(self, module_name: str) -> None:
        self.module_name = module_name
        self._module = load_module(module_name)

    # ------------------------------------------------------------------
    # Core: invoke the graph
    # ------------------------------------------------------------------

    async def _run(self, mode: str, topic_filter: str | None = None,
                   content_format: str = "report", content_rank: int = 1) -> KyvraState:
        """Run the full LangGraph pipeline and return the final state."""
        initial = empty_state(
            module_name=self.module_name,
            mode=mode,
            topic_filter=topic_filter,
            content_format=content_format,
            content_rank=content_rank,
        )
        result: KyvraState = await kyvra_graph.ainvoke(initial)
        return result

    # ------------------------------------------------------------------
    # Streaming: yields node labels as they complete (for Telegram progress)
    # ------------------------------------------------------------------

    async def stream_events(
        self, mode: str = "full", topic_filter: str | None = None
    ) -> AsyncIterator[tuple[str, KyvraState | None]]:
        """Async generator that yields (node_name, final_state_or_None).

        Yields one (node_name, None) per completed node during the run,
        then yields ("__end__", final_state) when done.

        Usage in handlers.py:
            async for node, state in runner.stream_events():
                if node in PROGRESS_LABELS:
                    await msg.edit_text(PROGRESS_LABELS[node])
            # state is the final KyvraState
        """
        initial = empty_state(
            module_name=self.module_name,
            mode=mode,
            topic_filter=topic_filter,
        )
        final_state = initial.copy()
        async for event in kyvra_graph.astream(initial):
            for node_name, node_state in event.items():
                if isinstance(node_state, dict):
                    final_state.update(node_state)
                yield node_name, None
        yield "__end__", final_state

    # ------------------------------------------------------------------
    # SupervisorAgent-compatible public API
    # ------------------------------------------------------------------

    async def generate_report(self) -> str:
        """Full pipeline → AI report text."""
        logger.info("[GraphRunner] generate_report module=%s", self.module_name)
        state = await self._run("full")
        self._cache_status(state)
        return self._format_report(state)

    async def generate_report_with_ctx(self) -> tuple[str, KyvraState | None]:
        """Full pipeline → (report_text, final_state).  State replaces PipelineContext."""
        logger.info("[GraphRunner] generate_report_with_ctx module=%s", self.module_name)
        state = await self._run("full")
        self._cache_status(state)
        return self._format_report(state), state

    async def quick_scan(self) -> KyvraState:
        """Collect + score only — no LLM.  Returns final state."""
        logger.info("[GraphRunner] quick_scan module=%s", self.module_name)
        return await self._run("quick")

    async def generate_report_for_topic(self, topic: str) -> str:
        """Full pipeline keyword-scoped to topic."""
        logger.info("[GraphRunner] generate_report_for_topic module=%s topic=%r", self.module_name, topic)
        # Topic filtering is handled inside collect_node via state["topic_filter"].
        # After scoring we additionally filter top_items here.
        state = await self._run("topic", topic_filter=topic)
        kw = topic.lower()
        top = [
            i for i in (state.get("top_items") or [])
            if kw in (i.title + " " + i.summary).lower()
        ]
        if not top:
            return f"No news found for *{topic}* today."
        # Re-generate report text with the filtered items via LLM
        enriched = [
            {
                "title": i.title, "url": i.url, "source": i.source,
                "summary": i.summary, "confidence_score": i.confidence_score,
                "is_spike": i.is_spike, "raw_score": i.raw_score,
                "trend_heatmap": state.get("trend_heatmap", ""),
            }
            for i in top[:7]
        ]
        prompt = self._module.get_report_prompt(enriched)
        try:
            return await llm.complete(prompt, max_tokens=2000)
        except Exception as e:
            logger.error("[GraphRunner] topic LLM call failed: %s", e)
            return "Could not generate report right now. Try again later."

    async def generate_brief(self, user_id: int | None = None, rank: int = 1) -> str:
        return await self._content_format("brief", rank=rank, user_id=user_id)

    async def generate_thread(self, user_id: int | None = None, rank: int = 1) -> str:
        return await self._content_format("thread", rank=rank, user_id=user_id)

    async def generate_newsletter(self, user_id: int | None = None, rank: int = 1) -> str:
        return await self._content_format("newsletter", rank=rank, user_id=user_id)

    async def generate_script(self, user_id: int | None = None, rank: int = 1) -> str:
        return await self._content_format("script", rank=rank, user_id=user_id)

    async def generate_tweet_hook(self, rank: int = 1, lang: str = "en") -> str:
        state = await self._run("quick")
        top = state.get("top_items") or []
        if not top:
            return "No stories available right now."
        item = top[max(0, min(rank, len(top)) - 1)]
        prompt = self._module.get_tweet_hook_prompt(
            {"title": item.title, "url": item.url, "summary": item.summary}, lang=lang
        )
        try:
            return await llm.complete(prompt, max_tokens=160)
        except Exception as e:
            logger.error("[GraphRunner] tweet_hook LLM failed: %s", e)
            return "Could not generate tweet. Try again later."

    async def generate_newsletter_from_text(self, text: str, user_id: int | None = None) -> str:
        voice = memory.get_voice_profile(user_id) if user_id is not None else None
        item = {"title": text[:80], "url": "", "source": "User input",
                "summary": text, "confidence_score": 80, "is_spike": False}
        prompt = self._module.get_newsletter_prompt(item, voice=voice)
        try:
            return await llm.complete(prompt, max_tokens=800)
        except Exception as e:
            logger.error("[GraphRunner] newsletter_from_text LLM failed: %s", e)
            return "Could not generate newsletter section right now. Try again later."

    async def generate_newsletter_from_url(self, url: str, user_id: int | None = None) -> str:
        from utils.api_client import fetch_article
        article = await fetch_article(url)
        if article["error"] or not article["text"]:
            return "❌ Could not read the article at that URL. Make sure it's a public page."
        voice = memory.get_voice_profile(user_id) if user_id is not None else None
        item = {"title": article["title"] or url, "url": url, "source": "URL",
                "summary": article["text"], "confidence_score": 80, "is_spike": False}
        prompt = self._module.get_newsletter_prompt(item, voice=voice)
        try:
            return await llm.complete(prompt, max_tokens=800)
        except Exception as e:
            logger.error("[GraphRunner] newsletter_from_url LLM failed: %s", e)
            return "Could not generate newsletter section right now. Try again later."

    async def get_status(self) -> dict:
        cached = _STATUS_CACHE.get(self.module_name)
        if cached and (time.time() - cached["timestamp"]) < _STATUS_CACHE_TTL:
            return cached["status"]
        state = await self._run("quick")
        status = self._build_status_dict(state)
        _STATUS_CACHE[self.module_name] = {"timestamp": time.time(), "status": status}
        return status

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _content_format(self, fmt: str, rank: int = 1,
                               user_id: int | None = None) -> str:
        """Run quick scan then call LLM with the right prompt format."""
        from services.llm_provider import get_content_provider
        state = await self._run("quick")
        top = state.get("top_items") or []
        if not top:
            return f"No news today to build a {fmt} from. Try again later!"

        voice = memory.get_voice_profile(user_id) if user_id is not None else None
        clamped = max(0, min(rank, len(top)) - 1)
        selected = {"title": top[clamped].title, "url": top[clamped].url,
                    "source": top[clamped].source, "summary": top[clamped].summary,
                    "confidence_score": top[clamped].confidence_score,
                    "is_spike": top[clamped].is_spike, "raw_score": top[clamped].raw_score,
                    "published_at": top[clamped].published_at}

        max_tokens = {"thread": 1200, "brief": 400, "newsletter": 800, "script": 600}.get(fmt, 800)

        if fmt == "thread":
            prompt = self._module.get_thread_prompt(selected, voice=voice)
        elif fmt == "brief":
            payload = [
                {"title": i.title, "url": i.url, "source": i.source, "summary": i.summary,
                 "confidence_score": i.confidence_score, "is_spike": i.is_spike,
                 "raw_score": i.raw_score, "published_at": i.published_at}
                for i in top[:3]
            ]
            prompt = self._module.get_brief_prompt(payload, voice=voice)
        elif fmt == "newsletter":
            prompt = self._module.get_newsletter_prompt(selected, voice=voice)
        elif fmt == "script":
            prompt = self._module.get_script_prompt(selected, voice=voice)
        else:
            return f"Unknown format: {fmt}"

        try:
            return await get_content_provider().complete(prompt, max_tokens=max_tokens)
        except Exception as e:
            logger.error("[GraphRunner] %s LLM call failed: %s", fmt, e)
            return f"Could not generate {fmt} right now. Try again later!"

    def _format_report(self, state: KyvraState) -> str:
        report = state.get("report_text") or "Could not generate report."
        errors = state.get("errors") or []
        if errors:
            logger.warning("[GraphRunner] %d error(s): %s", len(errors), errors)
            report += f"\n\n⚠️ _{len(errors)} source(s) had issues and were skipped._"
        return report

    def _build_status_dict(self, state: KyvraState) -> dict:
        raw = state.get("raw_items") or []
        top = state.get("top_items") or []
        scored = state.get("scored_items") or []
        return {
            "module": self.module_name,
            "total_fetched": len(raw),
            "top_score": top[0].confidence_score if top else 0,
            "spikes": sum(1 for i in scored if i.is_spike),
            "sources": Counter(item.source for item in raw),
        }

    def _cache_status(self, state: KyvraState) -> None:
        if state.get("top_items"):
            _STATUS_CACHE[self.module_name] = {
                "timestamp": time.time(),
                "status": self._build_status_dict(state),
            }
