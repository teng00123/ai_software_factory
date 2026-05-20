from sqlalchemy import Column, String, Integer, DateTime, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.session import Base
import enum


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    prompt = Column(Text, nullable=False, comment="用户输入的需求提示")
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, comment="任务状态")
    current_agent = Column(String(50), nullable=True, comment="当前执行的Agent")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=func.now(), onupdate=lambda: datetime.now(timezone.utc), comment="更新时间")

    # 关系
    steps = relationship("TaskStep", back_populates="task", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Task(id={self.id}, status={self.status})>"