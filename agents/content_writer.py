import logging
import anthropic
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from modules.base import BaseModule

logger = logging.getLogger(__name__)

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


class ContentWriterAgent:
    """Calls Claude to generate the Vietnamese report from scored + analyzed items."""

    async def run(self, context: dict) -> dict:
        module: BaseModule = context["module"]
        top_items: list[dict] = context.get("top_items", [])
        trend_heatmap: str = context.get("trend_heatmap", "")

        if not top_items:
            context["report_text"] = "Hôm nay không có đủ tin tức để tạo report. Thử lại sau nhé! 🤷"
            return context

        # Inject trend heatmap into items for the prompt
        enriched_items = []
        for item in top_items:
            enriched_items.append({**item, "trend_heatmap": trend_heatmap})

        prompt = module.get_report_prompt(enriched_items)
        logger.info(f"[ContentWriter] Calling Claude ({CLAUDE_MODEL}) to write report...")

        try:
            message = _client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )
            report_text = message.content[0].text
        except Exception as e:
            logger.error(f"[ContentWriter] Claude API error: {e}")
            report_text = f"Lỗi khi tạo report: {e}"

        context["report_text"] = report_text
        logger.info("[ContentWriter] Report generated successfully.")
        return context


async def chat_with_claude(user_message: str, system_prompt: str, history: list[dict]) -> str:
    """Handle a single chat turn. history = list of {role, content} dicts."""
    messages = history + [{"role": "user", "content": user_message}]

    try:
        response = _client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1000,
            system=system_prompt,
            messages=messages,
        )
        return response.content[0].text
    except Exception as e:
        logger.error(f"[Chat] Claude error: {e}")
        return f"Lỗi kết nối AI: {e}"
