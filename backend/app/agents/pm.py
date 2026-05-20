import json
import logging

from app.agents.base import BaseAgent, AgentInput, AgentOutput
from app.agents.registry import AgentRegistry
from app.core.llm import call_llm
from app.prompts.pm import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)


@AgentRegistry.register
class PMAgent(BaseAgent):
    """PM Agent - 需求拆解为子任务 DAG"""

    name = "pm"
    description = "PM Agent - 将用户需求拆解为可执行的技术子任务"

    async def run(self, input: AgentInput) -> AgentOutput:
        user_prompt = USER_PROMPT_TEMPLATE.format(prompt=input.prompt)

        response = await call_llm(
            prompt=user_prompt,
            system=SYSTEM_PROMPT,
        )

        # 解析 JSON 响应
        try:
            # 尝试从响应中提取 JSON
            content = response.content.strip()
            # 处理 markdown 代码块包裹的情况
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                content = content.rsplit("```", 1)[0]
            result = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"PM Agent: Failed to parse LLM response as JSON: {e}")
            return AgentOutput(
                success=False,
                error=f"Failed to parse response: {e}",
                token_usage=response.total_tokens,
                cost_usd=response.cost_usd,
            )

        # 校验结构
        if "tasks" not in result:
            return AgentOutput(
                success=False,
                error="Response missing 'tasks' field",
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
            },
        )
