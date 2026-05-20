import json
import logging

from app.agents.base import BaseAgent, AgentInput, AgentOutput
from app.agents.registry import AgentRegistry
from app.core.llm import call_llm
from app.prompts.devops import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)


@AgentRegistry.register
class DevOpsAgent(BaseAgent):
    """DevOps Agent - 生成 Dockerfile 和 docker-compose"""

    name = "devops"
    description = "DevOps Agent - 生成 Dockerfile、docker-compose 部署配置"

    async def run(self, input: AgentInput) -> AgentOutput:
        file_list = input.context.get("file_list", "无文件列表")

        user_prompt = USER_PROMPT_TEMPLATE.format(
            prompt=input.prompt,
            file_list=file_list,
        )
        response = await call_llm(prompt=user_prompt, system=SYSTEM_PROMPT)

        try:
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0]
            result = json.loads(content)
        except json.JSONDecodeError as e:
            return AgentOutput(success=False, error=f"JSON parse error: {e}", token_usage=response.total_tokens, cost_usd=response.cost_usd)

        if "dockerfile" not in result:
            return AgentOutput(success=False, error="Missing 'dockerfile' field", token_usage=response.total_tokens, cost_usd=response.cost_usd)

        return AgentOutput(
            success=True,
            result=result,
            token_usage=response.total_tokens,
            cost_usd=response.cost_usd,
            metadata={"model": response.model},
        )
