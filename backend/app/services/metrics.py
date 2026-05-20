"""
Metrics 统计服务

提供 Token/Cost/Latency 的聚合查询。
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func as sqlfunc
from datetime import datetime, timedelta, timezone

from app.models.task import Task, TaskStatus
from app.models.dag_node import TaskDagNode
from app.models.metrics import AgentMetric


async def get_overview(db: AsyncSession) -> dict:
    """总览指标"""
    # 总任务数
    result = await db.execute(select(sqlfunc.count(Task.id)))
    total_tasks = result.scalar() or 0

    # 各状态数
    result = await db.execute(
        select(Task.status, sqlfunc.count(Task.id)).group_by(Task.status)
    )
    status_counts = {row[0].value if row[0] else "unknown": row[1] for row in result.all()}

    # 总 token
    result = await db.execute(select(sqlfunc.sum(AgentMetric.total_tokens)))
    total_tokens = result.scalar() or 0

    # 总费用
    result = await db.execute(select(sqlfunc.sum(AgentMetric.cost_usd)))
    total_cost = float(result.scalar() or 0)

    # 总 DAG 节点数
    result = await db.execute(select(sqlfunc.count(TaskDagNode.id)))
    total_nodes = result.scalar() or 0

    return {
        "total_tasks": total_tasks,
        "status_counts": status_counts,
        "total_tokens": total_tokens,
        "total_cost_usd": round(total_cost, 6),
        "total_dag_nodes": total_nodes,
    }


async def get_agent_stats(db: AsyncSession) -> list:
    """按 Agent 维度统计"""
    result = await db.execute(
        select(
            AgentMetric.agent,
            sqlfunc.count(AgentMetric.id).label("executions"),
            sqlfunc.sum(AgentMetric.total_tokens).label("tokens"),
            sqlfunc.sum(AgentMetric.cost_usd).label("cost"),
            sqlfunc.avg(AgentMetric.latency_ms).label("avg_latency"),
        ).group_by(AgentMetric.agent)
    )
    return [
        {
            "agent": row[0],
            "executions": row[1],
            "total_tokens": row[2] or 0,
            "total_cost_usd": round(float(row[3] or 0), 6),
            "avg_latency_ms": round(float(row[4] or 0)),
        }
        for row in result.all()
    ]


async def get_cost_trend(db: AsyncSession, days: int = 7) -> list:
    """费用趋势（按天）"""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(
            sqlfunc.date(AgentMetric.created_at).label("date"),
            sqlfunc.sum(AgentMetric.cost_usd).label("cost"),
            sqlfunc.sum(AgentMetric.total_tokens).label("tokens"),
        )
        .where(AgentMetric.created_at >= since)
        .group_by(sqlfunc.date(AgentMetric.created_at))
        .order_by(sqlfunc.date(AgentMetric.created_at))
    )
    return [
        {
            "date": str(row[0]),
            "cost_usd": round(float(row[1] or 0), 6),
            "tokens": row[2] or 0,
        }
        for row in result.all()
    ]


async def record_metric(
    db: AsyncSession,
    task_id: int,
    node_id: str,
    agent: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    cost_usd: float,
    latency_ms: int,
):
    """记录一次 Agent 执行指标"""
    metric = AgentMetric(
        task_id=task_id,
        node_id=node_id,
        agent=agent,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=input_tokens + output_tokens,
        cost_usd=cost_usd,
        latency_ms=latency_ms,
    )
    db.add(metric)
    await db.commit()
