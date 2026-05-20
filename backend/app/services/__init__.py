import json
import logging
from typing import Optional, Callable, Awaitable

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.agents import AgentRegistry
from app.agents.base import AgentInput, AgentOutput
from app.models.task import Task, TaskStatus
from app.models.task_step import TaskStep, StepStatus

logger = logging.getLogger(__name__)

# 日志回调类型：(task_id, message) -> None
LogCallback = Optional[Callable[[int, str], Awaitable[None]]]


class TaskScheduler:
    """任务调度器 V1：同步顺序执行"""

    async def execute_task(
        self,
        task_id: int,
        db: AsyncSession,
        log_callback: LogCallback = None,
    ) -> AgentOutput:
        """
        执行任务：根据 task.current_agent 调用对应 Agent

        Args:
            task_id: 任务 ID
            db: 数据库会话
            log_callback: 日志回调函数（用于 WebSocket 推送）

        Returns:
            AgentOutput: Agent 执行结果
        """
        # 1. 获取任务
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()

        if not task:
            raise ValueError(f"Task {task_id} not found")

        if task.status == TaskStatus.RUNNING:
            raise ValueError(f"Task {task_id} is already running")

        # 2. 确定要执行的 Agent
        agent_name = task.current_agent or "echo"
        agent = AgentRegistry.get(agent_name)

        if not agent:
            available = AgentRegistry.names()
            raise ValueError(
                f"Agent '{agent_name}' not found. Available: {available}"
            )

        # 3. 更新任务状态为 running
        task.status = TaskStatus.RUNNING
        task.current_agent = agent_name
        await db.commit()

        if log_callback:
            await log_callback(
                task_id,
                json.dumps({
                    "event": "task_started",
                    "agent": agent_name,
                    "task_id": task_id,
                }),
            )

        # 4. 创建 step 记录
        step = TaskStep(
            task_id=task_id,
            agent=agent_name,
            input=task.prompt,
            status=StepStatus.RUNNING,
        )
        db.add(step)
        await db.commit()
        await db.refresh(step)

        if log_callback:
            await log_callback(
                task_id,
                json.dumps({
                    "event": "step_started",
                    "step_id": step.id,
                    "agent": agent_name,
                }),
            )

        # 5. 执行 Agent
        agent_input = AgentInput(
            task_id=task_id,
            prompt=task.prompt,
            context={},
        )

        output = await agent.execute(agent_input)

        # 6. 更新 step 结果
        step.output = json.dumps(output.result) if output.result else None
        step.status = StepStatus.COMPLETED if output.success else StepStatus.FAILED
        step.duration = output.duration_ms
        step.token_usage = output.token_usage
        step.cost_usd = output.cost_usd
        if output.error:
            step.error_msg = output.error
        await db.commit()

        # 7. 更新任务状态
        task.status = TaskStatus.COMPLETED if output.success else TaskStatus.FAILED
        await db.commit()

        if log_callback:
            await log_callback(
                task_id,
                json.dumps({
                    "event": "task_completed" if output.success else "task_failed",
                    "task_id": task_id,
                    "agent": agent_name,
                    "success": output.success,
                    "duration_ms": output.duration_ms,
                    "error": output.error,
                }),
            )

        return output


# 全局调度器实例
scheduler = TaskScheduler()
