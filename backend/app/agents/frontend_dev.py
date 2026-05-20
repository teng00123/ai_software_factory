import json
import logging

from app.agents.base import BaseAgent, AgentInput, AgentOutput
from app.agents.registry import AgentRegistry
from app.core.llm import call_llm
from app.prompts.frontend import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)


@AgentRegistry.register
class FrontendAgent(BaseAgent):
    """Frontend Agent - Vue 组件代码生成"""

    name = "frontend"
    description = "Frontend Agent - 生成 Vue 3 + TypeScript 前端代码"

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

        if "files" not in result:
            return AgentOutput(success=False, error="Missing 'files' field", token_usage=response.total_tokens, cost_usd=response.cost_usd)

        return AgentOutput(
            success=True,
            result=result,
            token_usage=response.total_tokens,
            cost_usd=response.cost_usd,
            metadata={"model": response.model, "files_count": len(result["files"])},
        )
