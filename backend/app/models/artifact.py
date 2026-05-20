from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from datetime import datetime, timezone
from app.db.session import Base


class TaskArtifact(Base):
    """任务产物模型 - 存储生成的代码文件"""
    __tablename__ = "task_artifacts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    node_id = Column(String(50), nullable=True, comment="关联的 DAG 节点 ID")
    file_path = Column(String(500), nullable=False, comment="文件路径")
    content = Column(Text, nullable=False, comment="文件内容")
    language = Column(String(20), nullable=True, comment="编程语言")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=func.now())

    def __repr__(self):
        return f"<Artifact(task_id={self.task_id}, path={self.file_path})>"
