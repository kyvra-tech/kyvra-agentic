"""
Module registry — maps module name → concrete BaseModule class.

Kept separate from supervisor.py so node files can import load_module
without pulling in the full SupervisorAgent (which has Python 3.10+
type annotations that fail on Python 3.9 under strict evaluation).

All imports here are deferred (inside the function) so that Python 3.9
only evaluates them at call time, not at import time.
"""

from __future__ import annotations


def load_module(module_name: str):
    """Return an instantiated BaseModule for the given name."""
    from modules.tech.sources import TechModule
    from modules.crypto.sources import CryptoModule
    from modules.parody.sources import ParodyModule
    from modules.sport.sources import SportModule
    from modules.political.sources import PoliticalModule
    from modules.war.sources import WarModule
    from modules.humor.sources import HumorModule
    from modules.energy.sources import EnergyModule
    from modules.markets.sources import MarketsModule

    registry = {
        "tech":      TechModule,
        "crypto":    CryptoModule,
        "parody":    ParodyModule,
        "sport":     SportModule,
        "political": PoliticalModule,
        "war":       WarModule,
        "humor":     HumorModule,
        "energy":    EnergyModule,
        "markets":   MarketsModule,
    }
    cls = registry.get(module_name)
    if cls is None:
        raise ValueError(f"Unknown module: '{module_name}'. Available: {sorted(registry)}")
    return cls()
