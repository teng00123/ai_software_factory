from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel

from app.db.session import get_db
from app.models.task import Task, TaskStatus
from app.models.dag_node import TaskDagNode, DagNodeStatus
from app.models.artifact import TaskArtifact
from app.services.dag_scheduler import dag_scheduler
from app.api.v1.endpoints.ws import ws_manager

router = APIRouter()


# --- Response Schemas ---

class DagNodeResponse(BaseModel):
    id: int
    node_id: str
    agent: str
    label: Optional[str] = None
    description: Optional[str] = None
    status: DagNodeStatus
    depends_on: Optional[list] = None
    output_data: Optional[dict] = None
    error_msg: Optional[str] = None
    duration_ms: Optional[int] = None
    token_usage: int = 0
    cost_usd: str = "0"

    class Config:
        from_attributes = True


class DagEdge(BaseModel):
    source: str
    target: str


class DagResponse(BaseModel):
    nodes: List[DagNodeResponse]
    edges: List[DagEdge]


class ArtifactResponse(BaseModel):
    id: int
    task_id: int
    node_id: Optional[str] = None
    file_path: str
    content: str
    language: Optional[str] = None

    class Config:
        from_attributes = True


# --- Endpoints ---

@router.get("/{task_id}/dag", response_model=DagResponse, summary="获取任务 DAG")
async def get_task_dag(task_id: int, db: AsyncSession = Depends(get_db)):
    """获取任务的 DAG 结构（节点 + 边）"""
    result = await db.execute(
        select(TaskDagNode).where(TaskDagNode.task_id == task_id).order_by(TaskDagNode.id)
    )
    nodes = result.scalars().all()

    # 构造边
    edges = []
    for node in nodes:
        deps = node.depends_on or []
        for dep in deps:
            edges.append(DagEdge(source=dep, target=node.node_id))

    return DagResponse(nodes=nodes, edges=edges)


@router.post("/{task_id}/dag/run", summary="按 DAG 执行任务")
async def run_task_dag(task_id: int, db: AsyncSession = Depends(get_db)):
    """
    按 DAG 模式执行任务：
    1. PM Agent 拆解需求
    2. 创建 DAG 节点
    3. 拓扑排序并按序执行各 Agent
    """
    # 检查任务
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if task.status == TaskStatus.RUNNING:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Task is already running")

    # WebSocket 日志回调
    async def log_callback(tid: int, message: str):
        await ws_manager.send_to_task(tid, message)

    # 执行 DAG
    try:
        await dag_scheduler.execute_dag(task_id, db, log_callback=log_callback)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # 返回最新 DAG
    result = await db.execute(
        select(TaskDagNode).where(TaskDagNode.task_id == task_id).order_by(TaskDagNode.id)
    )
    nodes = result.scalars().all()
    edges = []
    for node in nodes:
        deps = node.depends_on or []
        for dep in deps:
            edges.append(DagEdge(source=dep, target=node.node_id))

    return DagResponse(nodes=nodes, edges=edges)


@router.get("/{task_id}/artifacts", response_model=List[ArtifactResponse], summary="获取任务产物")
async def get_task_artifacts(task_id: int, db: AsyncSession = Depends(get_db)):
    """获取任务生成的代码产物"""
    result = await db.execute(
        select(TaskArtifact).where(TaskArtifact.task_id == task_id).order_by(TaskArtifact.id)
    )
    artifacts = result.scalars().all()
    return artifacts
