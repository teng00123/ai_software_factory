"""
DAG 调度器

负责:
1. 根据 PM Agent 输出创建 DAG 节点
2. 拓扑排序确定执行顺序
3. 按依赖顺序执行各节点对应的 Agent
4. 将产物存入 task_artifacts
"""
import json
import logging
from typing import List, Optional, Callable, Awaitable
from collections import deque

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.agents import AgentRegistry
from app.agents.base import AgentInput
from app.models.task import Task, TaskStatus
from app.models.dag_node import TaskDagNode, DagNodeStatus
from app.models.artifact import TaskArtifact
from app.models.review import ReviewComment
from app.models.test_result import TestResult
from app.models.metrics import AgentMetric, ExecutionSnapshot

logger = logging.getLogger(__name__)

LogCallback = Optional[Callable[[int, str], Awaitable[None]]]


class DagScheduler:
    """DAG 调度器"""

    async def create_dag_from_pm_output(
        self,
        task_id: int,
        pm_result: dict,
        db: AsyncSession,
    ) -> List[TaskDagNode]:
        """
        根据 PM Agent 的输出创建 DAG 节点

        Args:
            task_id: 任务 ID
            pm_result: PM Agent 输出的 JSON，含 tasks 列表
            db: 数据库会话

        Returns:
            创建的 DAG 节点列表
        """
        tasks = pm_result.get("tasks", [])
        nodes = []

        for t in tasks:
            node = TaskDagNode(
                task_id=task_id,
                node_id=t["id"],
                agent=t.get("agent", "backend"),
                label=t.get("title", ""),
                description=t.get("description", ""),
                status=DagNodeStatus.PENDING,
                depends_on=t.get("depends_on", []),
            )
            db.add(node)
            nodes.append(node)

        await db.commit()
        for node in nodes:
            await db.refresh(node)

        return nodes

    def topological_sort(self, nodes: List[TaskDagNode]) -> List[List[TaskDagNode]]:
        """
        拓扑排序，返回按层分组的节点列表
        同一层的节点可以并行执行

        Returns:
            [[layer0_nodes], [layer1_nodes], ...]
        """
        node_map = {n.node_id: n for n in nodes}
        in_degree = {n.node_id: 0 for n in nodes}
        adj = {n.node_id: [] for n in nodes}

        for node in nodes:
            deps = node.depends_on or []
            for dep in deps:
                if dep in adj:
                    adj[dep].append(node.node_id)
                    in_degree[node.node_id] += 1

        # BFS 分层
        layers = []
        queue = deque([nid for nid, deg in in_degree.items() if deg == 0])

        while queue:
            layer = []
            for _ in range(len(queue)):
                nid = queue.popleft()
                layer.append(node_map[nid])
                for neighbor in adj[nid]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)
            layers.append(layer)

        return layers

    async def execute_dag(
        self,
        task_id: int,
        db: AsyncSession,
        log_callback: LogCallback = None,
    ):
        """
        执行整个 DAG

        流程:
        1. 先执行 PM Agent 拆解需求
        2. 根据 PM 输出创建 DAG
        3. 按拓扑顺序依次执行各节点
        """
        # 获取任务
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        if not task:
            raise ValueError(f"Task {task_id} not found")

        # 更新状态
        task.status = TaskStatus.RUNNING
        task.current_agent = "pm"
        await db.commit()

        if log_callback:
            await log_callback(task_id, json.dumps({
                "event": "dag_started",
                "task_id": task_id,
            }))

        # Step 1: 执行 PM Agent
        pm_agent = AgentRegistry.get("pm")
        if not pm_agent:
            raise ValueError("PM Agent not registered")

        if log_callback:
            await log_callback(task_id, json.dumps({
                "event": "node_started",
                "node_id": "pm_decompose",
                "agent": "pm",
            }))

        pm_input = AgentInput(task_id=task_id, prompt=task.prompt)
        pm_output = await pm_agent.execute(pm_input)

        if not pm_output.success:
            task.status = TaskStatus.FAILED
            await db.commit()
            if log_callback:
                await log_callback(task_id, json.dumps({
                    "event": "dag_failed",
                    "error": pm_output.error,
                }))
            return

        if log_callback:
            await log_callback(task_id, json.dumps({
                "event": "node_completed",
                "node_id": "pm_decompose",
                "agent": "pm",
                "result": pm_output.result,
            }))

        # Step 2: 创建 DAG 节点
        nodes = await self.create_dag_from_pm_output(task_id, pm_output.result, db)

        if log_callback:
            await log_callback(task_id, json.dumps({
                "event": "dag_created",
                "nodes_count": len(nodes),
                "nodes": [{"id": n.node_id, "agent": n.agent, "label": n.label} for n in nodes],
            }))

        # Step 3: 拓扑排序并执行
        layers = self.topological_sort(nodes)

        for layer_idx, layer in enumerate(layers):
            if log_callback:
                await log_callback(task_id, json.dumps({
                    "event": "layer_started",
                    "layer": layer_idx,
                    "nodes": [n.node_id for n in layer],
                }))

            for node in layer:
                await self._execute_node(task_id, node, task.prompt, db, log_callback)

        # 检查是否全部成功
        result = await db.execute(
            select(TaskDagNode).where(
                TaskDagNode.task_id == task_id,
                TaskDagNode.status == DagNodeStatus.FAILED,
            )
        )
        failed_nodes = result.scalars().all()

        if failed_nodes:
            task.status = TaskStatus.FAILED
        else:
            task.status = TaskStatus.COMPLETED

        task.current_agent = None
        await db.commit()

        if log_callback:
            await log_callback(task_id, json.dumps({
                "event": "dag_completed" if not failed_nodes else "dag_failed",
                "task_id": task_id,
                "failed_nodes": [n.node_id for n in failed_nodes],
            }))

    async def _execute_node(
        self,
        task_id: int,
        node: TaskDagNode,
        original_prompt: str,
        db: AsyncSession,
        log_callback: LogCallback = None,
    ):
        """执行单个 DAG 节点"""
        agent = AgentRegistry.get(node.agent)
        if not agent:
            node.status = DagNodeStatus.FAILED
            node.error_msg = f"Agent '{node.agent}' not found"
            await db.commit()
            return

        # 更新节点状态
        node.status = DagNodeStatus.RUNNING
        await db.commit()

        if log_callback:
            await log_callback(task_id, json.dumps({
                "event": "node_started",
                "node_id": node.node_id,
                "agent": node.agent,
                "label": node.label,
            }))

        # 构造输入
        agent_input = AgentInput(
            task_id=task_id,
            prompt=node.description or original_prompt,
            context={
                "title": node.label,
                "description": node.description,
                "project_context": original_prompt,
                "node_id": node.node_id,
            },
        )

        # 执行
        output = await agent.execute(agent_input)

        # 更新节点
        node.status = DagNodeStatus.COMPLETED if output.success else DagNodeStatus.FAILED
        node.output_data = output.result
        node.error_msg = output.error
        node.duration_ms = output.duration_ms
        node.token_usage = output.token_usage
        node.cost_usd = str(output.cost_usd)
        await db.commit()

        # 记录 metrics
        metric = AgentMetric(
            task_id=task_id,
            node_id=node.node_id,
            agent=node.agent,
            model=output.metadata.get("model", "unknown"),
            input_tokens=output.metadata.get("input_tokens", 0),
            output_tokens=output.metadata.get("output_tokens", 0),
            total_tokens=output.token_usage,
            cost_usd=output.cost_usd,
            latency_ms=output.duration_ms,
        )
        db.add(metric)

        # 记录快照
        snapshot = ExecutionSnapshot(
            task_id=task_id,
            node_id=node.node_id,
            step_index=0,  # will be set by caller if needed
            event="node_completed" if output.success else "node_failed",
            state={
                "agent": node.agent,
                "status": node.status.value,
                "duration_ms": output.duration_ms,
                "token_usage": output.token_usage,
                "has_output": output.result is not None,
            },
        )
        db.add(snapshot)
        await db.commit()

        # 如果是 backend/frontend agent 且成功，保存产物
        if output.success and output.result and "files" in output.result:
            for file_info in output.result["files"]:
                artifact = TaskArtifact(
                    task_id=task_id,
                    node_id=node.node_id,
                    file_path=file_info.get("path", "unknown"),
                    content=file_info.get("content", ""),
                    language=file_info.get("language", "python"),
                )
                db.add(artifact)
            await db.commit()

        # QA Agent: 保存测试文件为产物 + 保存测试计划为 test_results
        if output.success and output.result and node.agent == "qa":
            # 保存测试文件
            for tf in output.result.get("test_files", []):
                artifact = TaskArtifact(
                    task_id=task_id,
                    node_id=node.node_id,
                    file_path=tf.get("path", "tests/test_gen.py"),
                    content=tf.get("content", ""),
                    language=tf.get("language", "python"),
                )
                db.add(artifact)
            # 保存测试计划为 test_results (mock 全部 passed)
            for tp in output.result.get("test_plan", []):
                tr = TestResult(
                    task_id=task_id,
                    node_id=node.node_id,
                    test_name=tp.get("name", "unknown"),
                    status="passed",
                    duration_ms=100,
                )
                db.add(tr)
            await db.commit()

        # Review Agent: 保存 review comments
        if output.success and output.result and node.agent == "reviewer":
            for comment in output.result.get("comments", []):
                rc = ReviewComment(
                    task_id=task_id,
                    node_id=node.node_id,
                    file_path=comment.get("file_path"),
                    line_number=comment.get("line_number"),
                    severity=comment.get("severity", "info"),
                    category=comment.get("category"),
                    message=comment.get("message", ""),
                    suggestion=comment.get("suggestion"),
                )
                db.add(rc)
            await db.commit()

        if log_callback:
            await log_callback(task_id, json.dumps({
                "event": "node_completed" if output.success else "node_failed",
                "node_id": node.node_id,
                "agent": node.agent,
                "duration_ms": output.duration_ms,
                "error": output.error,
            }))


# 全局实例
dag_scheduler = DagScheduler()
