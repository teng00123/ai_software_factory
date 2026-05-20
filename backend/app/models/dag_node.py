from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Enum, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.session import Base
import enum


class DagNodeStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskDagNode(Base):
    """DAG 节点模型"""
    __tablename__ = "task_dag_nodes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    node_id = Column(String(50), nullable=False, comment="DAG 内节点标识")
    agent = Column(String(50), nullable=False, comment="执行的 Agent 类型")
    label = Column(String(255), nullable=True, comment="节点显示标签")
    description = Column(Text, nullable=True, comment="节点详细描述")
    status = Column(Enum(DagNodeStatus), default=DagNodeStatus.PENDING)
    depends_on = Column(JSON, default=list, comment="依赖的节点 ID 列表")
    input_data = Column(JSON, nullable=True, comment="节点输入数据")
    output_data = Column(JSON, nullable=True, comment="节点输出数据")
    error_msg = Column(Text, nullable=True, comment="错误信息")
    duration_ms = Column(Integer, nullable=True, comment="执行耗时(ms)")
    token_usage = Column(Integer, default=0, comment="Token 消耗")
    cost_usd = Column(String(20), default="0", comment="费用")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=func.now())
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=func.now(), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<DagNode(task_id={self.task_id}, node_id={self.node_id}, agent={self.agent})>"
