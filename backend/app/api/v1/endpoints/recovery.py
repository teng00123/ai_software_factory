from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel

from app.db.session import get_db
from app.models.task import Task
from app.models.dag_node import TaskDagNode, DagNodeStatus
from app.models.error_log import ErrorLog, RetryHistory
from app.services.retry import retry_node
from app.api.v1.endpoints.ws import ws_manager

router = APIRouter()


# --- Schemas ---

class ErrorLogResponse(BaseModel):
    id: int
    task_id: int
    node_id: Optional[str] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    is_recoverable: bool = True

    class Config:
        from_attributes = True


class RetryHistoryResponse(BaseModel):
    id: int
    task_id: int
    node_id: Optional[str] = None
    attempt: int = 1
    strategy: Optional[str] = None
    model_used: Optional[str] = None
    status: str
    duration_ms: int = 0

    class Config:
        from_attributes = True


class RetryRequest(BaseModel):
    max_retries: int = 3


# --- Endpoints ---

@router.get("/{task_id}/errors", response_model=List[ErrorLogResponse], summary="获取错误历史")
async def get_task_errors(task_id: int, db: AsyncSession = Depends(get_db)):
    """获取任务的错误日志"""
    result = await db.execute(
        select(ErrorLog).where(ErrorLog.task_id == task_id).order_by(ErrorLog.id.desc())
    )
    return result.scalars().all()


@router.get("/{task_id}/retries", response_model=List[RetryHistoryResponse], summary="获取重试历史")
async def get_retry_history(task_id: int, db: AsyncSession = Depends(get_db)):
    """获取任务的重试历史"""
    result = await db.execute(
        select(RetryHistory).where(RetryHistory.task_id == task_id).order_by(RetryHistory.id)
    )
    return result.scalars().all()


@router.post("/{task_id}/retry", summary="重试失败节点")
async def retry_failed_nodes(
    task_id: int,
    body: RetryRequest = RetryRequest(),
    db: AsyncSession = Depends(get_db),
):
    """
    重试任务中所有失败的 DAG 节点
    """
    # 获取任务
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    # 获取失败节点
    result = await db.execute(
        select(TaskDagNode).where(
            TaskDagNode.task_id == task_id,
            TaskDagNode.status == DagNodeStatus.FAILED,
        )
    )
    failed_nodes = result.scalars().all()

    if not failed_nodes:
        return {"message": "No failed nodes to retry", "retried": 0, "recovered": 0}

    # WS 回调
    async def log_callback(tid: int, message: str):
        await ws_manager.send_to_task(tid, message)

    recovered = 0
    for node in failed_nodes:
        success = await retry_node(
            task_id=task_id,
            node=node,
            original_prompt=task.prompt,
            db=db,
            log_callback=log_callback,
            max_retries=body.max_retries,
        )
        if success:
            recovered += 1

    return {
        "message": f"Retried {len(failed_nodes)} nodes, recovered {recovered}",
        "retried": len(failed_nodes),
        "recovered": recovered,
    }


@router.post("/{task_id}/nodes/{node_id}/fix", summary="修复指定节点")
async def fix_node(
    task_id: int,
    node_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    对指定的失败节点执行 Fix Agent 修复
    """
    # 获取任务
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    # 获取节点
    result = await db.execute(
        select(TaskDagNode).where(
            TaskDagNode.task_id == task_id,
            TaskDagNode.node_id == node_id,
        )
    )
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")

    if node.status != DagNodeStatus.FAILED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Node is not in failed state")

    # WS 回调
    async def log_callback(tid: int, message: str):
        await ws_manager.send_to_task(tid, message)

    success = await retry_node(
        task_id=task_id,
        node=node,
        original_prompt=task.prompt,
        db=db,
        log_callback=log_callback,
        max_retries=3,
    )

    return {
        "node_id": node_id,
        "recovered": success,
        "status": node.status.value,
    }
