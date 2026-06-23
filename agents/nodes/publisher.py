"""
publisher_node — LangGraph node: mark delivered stories as seen.

Reads:  state["top_items"], state["module_name"]
Writes: state["published"]

This node only runs for mode=="full" and mode=="topic" (skipped by router for
"quick" and "breaking").
"""

import logging

from agents.state import KyvraState
import services.memory as memory

logger = logging.getLogger(__name__)


async def run(state: KyvraState) -> dict:
    top_items = state.get("top_items") or []
    module_name = state["module_name"]

    if top_items:
        memory.mark_seen(top_items, module_name)
        logger.info("[publisher] Marked %d items as seen for module '%s'.", len(top_items), module_name)

    return {"published": True}
