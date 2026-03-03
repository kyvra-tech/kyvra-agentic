import logging
from modules.base import BaseModule
from agents.data_collector import DataCollectorAgent
from agents.analyst import AnalystAgent
from agents.narrative_scout import NarrativeScoutAgent
from agents.content_writer import ContentWriterAgent

logger = logging.getLogger(__name__)


class SupervisorAgent:
    """Orchestrates the full report pipeline: collect → analyze → scout → write."""

    def __init__(self, module: BaseModule):
        self.module = module
        self.collector = DataCollectorAgent()
        self.analyst = AnalystAgent()
        self.scout = NarrativeScoutAgent()
        self.writer = ContentWriterAgent()

    async def generate_report(self) -> str:
        """Run the full pipeline and return the final report text."""
        context: dict = {"module": self.module}

        logger.info("[Supervisor] Starting report pipeline...")
        context = await self.collector.run(context)
        context = await self.analyst.run(context)
        context = await self.scout.run(context)
        context = await self.writer.run(context)

        logger.info("[Supervisor] Pipeline complete.")
        return context.get("report_text", "Không thể tạo report.")


def load_module(module_name: str) -> BaseModule:
    """Load the active module by name."""
    if module_name == "tech":
        from modules.tech.sources import TechModule
        return TechModule()
    # Future: add crypto, finance, news here
    raise ValueError(f"Unknown module: {module_name}")
