import json
import logging

from app.agents.base import BaseAgent, AgentInput, AgentOutput
from app.agents.registry import AgentRegistry
from app.core.llm import call_llm
from app.prompts.fix import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)


@AgentRegistry.register
class FixAgent(BaseAgent):
    """Fix Agent - 分析错误并生成修复补丁"""

    name = "fixer"
    description = "Fix Agent - 分析错误日志，生成修复代码"

    async def run(self, input: AgentInput) -> AgentOutput:
        title = input.context.get("title", input.prompt)
        error_message = input.context.get("error_message", "Unknown error")
        context = input.context.get("code_context", "")

        user_prompt = USER_PROMPT_TEMPLATE.format(
            title=title,
            error_message=error_message,
            context=context or "无相关代码上下文",
        )
        response = await call_llm(prompt=user_prompt, system=SYSTEM_PROMPT)

        try:
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0]
            result = json.loads(content)
        except json.JSONDecodeError as e:
            return AgentOutput(success=False, error=f"JSON parse error: {e}", token_usage=response.total_tokens, cost_usd=response.cost_usd)

        return AgentOutput(
            success=True,
            result=result,
            token_usage=response.total_tokens,
            cost_usd=response.cost_usd,
            metadata={"model": response.model, "confidence": result.get("confidence", 0)},
        )
