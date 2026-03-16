from agents.base import BaseAgent, PipelineContext
import services.llm as llm


class ContentWriterAgent(BaseAgent):
    """Calls the LLM to generate the daily report from scored + analyzed items."""

    async def run(self, ctx: PipelineContext) -> PipelineContext:
        if not ctx.top_items:
            ctx.report_text = "Không có tin tức đủ điểm hôm nay. Thử lại sau! 🤷"
            return ctx

        enriched = [
            {
                "title": item.title,
                "url": item.url,
                "source": item.source,
                "published_at": item.published_at,
                "summary": item.summary,
                "confidence_score": item.confidence_score,
                "is_spike": item.is_spike,
                "raw_score": item.raw_score,
                "trend_heatmap": ctx.trend_heatmap,
            }
            for item in ctx.top_items
        ]

        prompt = ctx.module.get_report_prompt(enriched)
        self._log(f"Calling LLM to write report ({len(ctx.top_items)} items)...")

        try:
            ctx.report_text = await llm.complete(prompt, max_tokens=2000)
            self._log("Report generated successfully.")
        except Exception as e:
            self._record_error(ctx, f"LLM call failed: {e}")
            ctx.report_text = f"Lỗi khi tạo report: {e}"

        return ctx


async def chat_with_llm(
    user_message: str,
    system_prompt: str,
    history: list[dict],
) -> str:
    """Single chat turn. history = [{role, content}, ...]."""
    messages = [{"role": "system", "content": system_prompt}] + history + [
        {"role": "user", "content": user_message}
    ]
    try:
        return await llm.chat(messages, max_tokens=1000)
    except Exception as e:
        return f"Lỗi kết nối AI: {e}"
