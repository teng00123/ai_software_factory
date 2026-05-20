import json
import logging

from app.agents.base import BaseAgent, AgentInput, AgentOutput
from app.agents.registry import AgentRegistry
from app.core.llm import call_llm
from app.prompts.architect import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)


@AgentRegistry.register
class ArchitectAgent(BaseAgent):
    """Architect Agent - 系统架构设计"""

    name = "architect"
    description = "Architect Agent - 技术选型、API Schema、DB Schema 设计"

    async def run(self, input: AgentInput) -> AgentOutput:
        user_prompt = USER_PROMPT_TEMPLATE.format(prompt=input.prompt)
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
            metadata={"model": response.model},
        )
