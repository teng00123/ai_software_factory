from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Numeric, JSON
from sqlalchemy.sql import func
from datetime import datetime, timezone
from app.db.session import Base


class AgentMetric(Base):
    """Agent 执行指标"""
    __tablename__ = "agent_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    node_id = Column(String(50), nullable=True)
    agent = Column(String(50), nullable=False, index=True)
    model = Column(String(50), nullable=True)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    cost_usd = Column(Numeric(10, 6), default=0)
    latency_ms = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=func.now())


class ExecutionSnapshot(Base):
    """执行快照 - 用于 Replay"""
    __tablename__ = "execution_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    node_id = Column(String(50), nullable=True)
    step_index = Column(Integer, default=0)
    event = Column(String(50), nullable=False)
    state = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=func.now())
