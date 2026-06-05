"""
router — conditional edge functions for the Kyvra LangGraph pipeline.

LangGraph calls these after a node completes to decide which node runs next.
Each function returns a string key that maps to a node name in the graph.

  after_collect  — called after collect_node
  after_parallel — called after analyst_node + scout_node both finish
"""

from agents.state import KyvraState


def after_collect(state: KyvraState) -> str:
    """Route after collect_node.

    "empty"  → no items fetched at all; short-circuit to END
    "score"  → normal: hand off to analyst + scout (parallel)
    """
    if not state.get("raw_items"):
        return "empty"
    return "score"


def after_parallel(state: KyvraState) -> str:
    """Route after analyst + scout both finish.

    "quick_end"    → mode "quick" or "breaking": skip LLM, go to END
    "write"        → mode "full" or "topic": call writer_node
    """
    mode = state.get("mode") or "full"
    if mode in ("quick", "breaking"):
        return "quick_end"
    return "write"
