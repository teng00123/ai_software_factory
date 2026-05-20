import asyncio
from app.agents.base import BaseAgent, AgentInput, AgentOutput
from app.agents.registry import AgentRegistry


@AgentRegistry.register
class EchoAgent(BaseAgent):
    """测试用 Echo Agent，原样返回输入"""

    name = "echo"
    description = "Echo Agent - 原样返回输入内容，用于测试调度流程"

    async def run(self, input: AgentInput) -> AgentOutput:
        # 模拟一点处理时间
        await asyncio.sleep(0.5)

        return AgentOutput(
            success=True,
            result={
                "echo": input.prompt,
                "context": input.context,
                "message": f"Echo Agent received task #{input.task_id}: {input.prompt}",
            },
            token_usage=0,
            cost_usd=0.0,
            metadata={"agent": self.name},
        )
