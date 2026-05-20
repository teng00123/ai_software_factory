from typing import Dict, Type, Optional
from app.agents.base import BaseAgent


class AgentRegistry:
    """Agent 注册表，管理所有已注册的 Agent"""

    _agents: Dict[str, BaseAgent] = {}

    @classmethod
    def register(cls, agent_class: Type[BaseAgent]) -> Type[BaseAgent]:
        """
        注册 Agent 的装饰器

        Usage:
            @AgentRegistry.register
            class MyAgent(BaseAgent):
                name = "my_agent"
                ...
        """
        instance = agent_class()
        cls._agents[instance.name] = instance
        return agent_class

    @classmethod
    def get(cls, name: str) -> Optional[BaseAgent]:
        """根据名称获取 Agent 实例"""
        return cls._agents.get(name)

    @classmethod
    def list_all(cls) -> Dict[str, BaseAgent]:
        """获取所有已注册的 Agent"""
        return cls._agents.copy()

    @classmethod
    def names(cls) -> list:
        """获取所有已注册的 Agent 名称"""
        return list(cls._agents.keys())

    @classmethod
    def info(cls) -> list:
        """获取所有 Agent 信息"""
        return [
            {
                "name": agent.name,
                "description": agent.description,
            }
            for agent in cls._agents.values()
        ]
