from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Any
from datetime import datetime, timezone


@dataclass
class AgentInput:
    """Agent 执行输入"""
    task_id: int
    prompt: str
    context: dict = field(default_factory=dict)


@dataclass
class AgentOutput:
    """Agent 执行输出"""
    success: bool
    result: Any = None
    error: Optional[str] = None
    duration_ms: int = 0
    token_usage: int = 0
    cost_usd: float = 0.0
    metadata: dict = field(default_factory=dict)


class BaseAgent(ABC):
    """Agent 基类，所有 Agent 必须继承此类"""

    name: str = "base"
    description: str = "Base Agent"

    @abstractmethod
    async def run(self, input: AgentInput) -> AgentOutput:
        """
        执行 Agent 任务

        Args:
            input: Agent 输入数据

        Returns:
            AgentOutput: 执行结果
        """
        raise NotImplementedError

    async def execute(self, input: AgentInput) -> AgentOutput:
        """
        包装执行方法，自动计算耗时

        Args:
            input: Agent 输入数据

        Returns:
            AgentOutput: 执行结果（含耗时）
        """
        start = datetime.now(timezone.utc)
        try:
            output = await self.run(input)
        except Exception as e:
            output = AgentOutput(
                success=False,
                error=str(e),
            )
        end = datetime.now(timezone.utc)
        output.duration_ms = int((end - start).total_seconds() * 1000)
        return output

    def __repr__(self) -> str:
        return f"<Agent: {self.name}>"
