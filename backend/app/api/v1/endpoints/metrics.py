from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.db.session import get_db
from app.models.metrics import AgentMetric, ExecutionSnapshot
from app.models.dag_node import TaskDagNode
from app.services.metrics import get_overview, get_agent_stats, get_cost_trend

router = APIRouter()


@router.get("/overview", summary="总览指标")
async def metrics_overview(db: AsyncSession = Depends(get_db)):
    """
    获取平台总览指标：总任务数、Token消耗、总费用、各状态分布
    """
    return await get_overview(db)


@router.get("/agents", summary="Agent 维度统计")
async def metrics_agents(db: AsyncSession = Depends(get_db)):
    """
    按 Agent 维度统计：执行次数、Token消耗、费用、平均延迟
    """
    return await get_agent_stats(db)


@router.get("/cost", summary="费用趋势")
async def metrics_cost(days: int = 7, db: AsyncSession = Depends(get_db)):
    """
    费用趋势（按天），默认最近 7 天
    """
    return await get_cost_trend(db, days=days)


@router.get("/tasks/{task_id}/trace", summary="单任务全链路追踪")
async def metrics_task_trace(task_id: int, db: AsyncSession = Depends(get_db)):
    """
    获取单个任务的全链路追踪：每个节点的 Agent、耗时、Token、费用
    """
    result = await db.execute(
        select(AgentMetric).where(AgentMetric.task_id == task_id).order_by(AgentMetric.id)
    )
    metrics = result.scalars().all()

    # 同时获取 DAG 节点
    result = await db.execute(
        select(TaskDagNode).where(TaskDagNode.task_id == task_id).order_by(TaskDagNode.id)
    )
    nodes = result.scalars().all()

    trace_items = []
    for node in nodes:
        node_metrics = [m for m in metrics if m.node_id == node.node_id]
        trace_items.append({
            "node_id": node.node_id,
            "agent": node.agent,
            "label": node.label,
            "status": node.status.value,
            "duration_ms": node.duration_ms or 0,
            "token_usage": sum(m.total_tokens for m in node_metrics),
            "cost_usd": sum(float(m.cost_usd) for m in node_metrics),
            "start_offset_ms": 0,  # 简化：实际需要计算相对于任务开始的偏移
        })

    return {
        "task_id": task_id,
        "total_duration_ms": sum(t["duration_ms"] for t in trace_items),
        "total_tokens": sum(t["token_usage"] for t in trace_items),
        "total_cost_usd": round(sum(t["cost_usd"] for t in trace_items), 6),
        "trace": trace_items,
    }


@router.get("/tasks/{task_id}/replay", summary="获取回放数据")
async def metrics_task_replay(task_id: int, db: AsyncSession = Depends(get_db)):
    """
    获取任务执行回放数据：按时间排序的事件快照列表
    """
    result = await db.execute(
        select(ExecutionSnapshot)
        .where(ExecutionSnapshot.task_id == task_id)
        .order_by(ExecutionSnapshot.step_index)
    )
    snapshots = result.scalars().all()

    return {
        "task_id": task_id,
        "total_steps": len(snapshots),
        "steps": [
            {
                "step_index": s.step_index,
                "event": s.event,
                "node_id": s.node_id,
                "state": s.state,
                "timestamp": s.timestamp.isoformat() if s.timestamp else None,
            }
            for s in snapshots
        ],
    }
