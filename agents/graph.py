"""
Kyvra LangGraph pipeline.

Graph shape
-----------
                    START
                      │
                  [collect]          ← fetch, filter, dedup, story continuity
                      │
           ┌──after_collect──┐
         "empty"          "score"
           │                 │
          END     ┌──────────┴──────────┐
                [analyst]           [scout]    ← parallel (no dependency)
                  └──────────┬──────────┘
                             │
                     after_parallel
                    /              \
             "quick_end"         "write"
                 │                  │
                END             [writer]       ← LLM call
                                   │
                              [publisher]      ← mark_seen + TrendPost push
                                   │
                                  END

Teaching notes
--------------
• Each node is an `async def run(state) -> dict` that returns ONLY the keys
  it modifies.  LangGraph merges those keys into the running state.
• Parallel nodes: LangGraph runs analyst + scout concurrently when both
  have an edge from "collect" and both have an edge to a fan-in node.
  We use a dummy "join" node (a pass-through) as the fan-in point so
  LangGraph knows it must wait for BOTH analyst and scout before routing.
• Conditional edges: after_collect and after_parallel are plain Python
  functions that return a string key.  The mapping dict in
  add_conditional_edges() translates that key to the next node name.
"""

from __future__ import annotations

import logging

from langgraph.graph import StateGraph, START, END

from agents.state import KyvraState
from agents.nodes import collect, analyst, scout, writer, publisher, router

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Fan-in node: waits for analyst + scout, then routes to writer or END
# ---------------------------------------------------------------------------

async def _parallel_join(state: KyvraState) -> dict:
    """Pass-through fan-in node.  No work here — just lets LangGraph know
    both analyst and scout have finished before we route onward."""
    return {}


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

def build_graph(checkpointer=None):
    """Compile and return the Kyvra pipeline graph.

    Parameters
    ----------
    checkpointer : optional
        A LangGraph checkpointer (e.g. SqliteSaver) for state persistence
        and human-in-the-loop support.  Pass None for stateless runs.

    Returns
    -------
    CompiledStateGraph
        Call .ainvoke(state) or .astream(state) on this.
    """
    g = StateGraph(KyvraState)

    # Register nodes
    g.add_node("collect",  collect.run)
    g.add_node("analyst",  analyst.run)
    g.add_node("scout",    scout.run)
    g.add_node("join",     _parallel_join)   # fan-in for analyst + scout
    g.add_node("writer",   writer.run)
    g.add_node("publisher", publisher.run)

    # --- Edges ---

    # 1. START → collect (always)
    g.add_edge(START, "collect")

    # 2. collect → conditional: empty items → END, else → analyst + scout
    g.add_conditional_edges(
        "collect",
        router.after_collect,
        {
            "empty": END,    # nothing fetched — short-circuit
            "score": "analyst",
        },
    )
    # Also fan-out collect → scout (parallel with analyst)
    g.add_edge("collect", "scout")

    # 3. analyst → join  (fan-in waits for both)
    g.add_edge("analyst", "join")
    # 4. scout → join
    g.add_edge("scout", "join")

    # 5. join → conditional: quick/breaking → END, full/topic → writer
    g.add_conditional_edges(
        "join",
        router.after_parallel,
        {
            "quick_end": END,
            "write":     "writer",
        },
    )

    # 6. writer → publisher → END (always, for full/topic modes)
    g.add_edge("writer",    "publisher")
    g.add_edge("publisher", END)

    return g.compile(checkpointer=checkpointer)


# ---------------------------------------------------------------------------
# Singleton — import this in handlers and API server
# ---------------------------------------------------------------------------

kyvra_graph = build_graph()
