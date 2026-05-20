from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Enum, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base
import enum


class StepStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskStep(Base):
    __tablename__ = "task_steps"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, comment="关联的任务ID")
    agent = Column(String(50), nullable=False, comment="执行的Agent类型")
    input = Column(Text, nullable=True, comment="Agent输入")
    output = Column(Text, nullable=True, comment="Agent输出")
    status = Column(Enum(StepStatus), default=StepStatus.PENDING, comment="步骤状态")
    duration = Column(Integer, nullable=True, comment="执行时长(毫秒)")
    token_usage = Column(Integer, default=0, comment="Token消耗")
    cost_usd = Column(Numeric(10, 6), default=0, comment="费用(USD)")
    error_msg = Column(Text, nullable=True, comment="错误信息")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    task = relationship("Task", back_populates="steps")

    def __repr__(self):
        return f"<TaskStep(id={self.id}, agent={self.agent}, status={self.status})>"