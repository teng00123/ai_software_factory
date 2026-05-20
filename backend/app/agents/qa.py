import json
import logging

from app.agents.base import BaseAgent, AgentInput, AgentOutput
from app.agents.registry import AgentRegistry
from app.core.llm import call_llm
from app.prompts.qa import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)


@AgentRegistry.register
class QAAgent(BaseAgent):
    """QA Agent - 生成测试用例"""

    name = "qa"
    description = "QA Agent - 生成 pytest 测试代码和测试计划"

    async def run(self, input: AgentInput) -> AgentOutput:
        title = input.context.get("title", input.prompt)
        description = input.context.get("description", input.prompt)
        context = input.context.get("project_context", "")

        user_prompt = USER_PROMPT_TEMPLATE.format(title=title, description=description, context=context or "无额外上下文")
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
            metadata={"model": response.model, "test_count": len(result.get("test_plan", []))},
        )
