import json
import logging

from app.agents.base import BaseAgent, AgentInput, AgentOutput
from app.agents.registry import AgentRegistry
from app.core.llm import call_llm
from app.prompts.review import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)


@AgentRegistry.register
class ReviewAgent(BaseAgent):
    """Review Agent - Code Review"""

    name = "reviewer"
    description = "Review Agent - 代码审查，安全扫描，性能建议"

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
            metadata={"model": response.model, "score": result.get("score", 0), "passed": result.get("passed", False)},
        )
