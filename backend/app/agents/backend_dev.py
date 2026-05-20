import json
import logging

from app.agents.base import BaseAgent, AgentInput, AgentOutput
from app.agents.registry import AgentRegistry
from app.core.llm import call_llm
from app.prompts.backend import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)


@AgentRegistry.register
class BackendAgent(BaseAgent):
    """Backend Agent - 根据任务描述生成 FastAPI 代码"""

    name = "backend"
    description = "Backend Agent - 根据任务描述生成 FastAPI + SQLAlchemy 代码"

    async def run(self, input: AgentInput) -> AgentOutput:
        # 从 context 中获取任务信息
        title = input.context.get("title", "")
        description = input.context.get("description", input.prompt)
        context = input.context.get("project_context", "")

        user_prompt = USER_PROMPT_TEMPLATE.format(
            title=title or input.prompt,
            description=description,
            context=context or "无额外上下文",
        )

        response = await call_llm(
            prompt=user_prompt,
            system=SYSTEM_PROMPT,
        )

        # 解析 JSON 响应
        try:
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                content = content.rsplit("```", 1)[0]
            result = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Backend Agent: Failed to parse response: {e}")
            return AgentOutput(
                success=False,
                error=f"Failed to parse response: {e}",
                token_usage=response.total_tokens,
                cost_usd=response.cost_usd,
            )

        # 校验
        if "files" not in result:
            return AgentOutput(
                success=False,
                error="Response missing 'files' field",
                token_usage=response.total_tokens,
                cost_usd=response.cost_usd,
            )

        return AgentOutput(
            success=True,
            result=result,
            token_usage=response.total_tokens,
            cost_usd=response.cost_usd,
            metadata={
                "model": response.model,
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
                "files_count": len(result["files"]),
            },
        )
