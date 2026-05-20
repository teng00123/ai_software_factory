from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Enum
from sqlalchemy.sql import func
from datetime import datetime, timezone
from app.db.session import Base
import enum


class DeployStatus(str, enum.Enum):
    BUILDING = "building"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"


class Deployment(Base):
    """部署记录"""
    __tablename__ = "deployments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    status = Column(Enum(DeployStatus), default=DeployStatus.BUILDING)
    container_id = Column(String(100), nullable=True)
    preview_url = Column(String(500), nullable=True)
    port = Column(Integer, nullable=True)
    build_log = Column(Text, nullable=True)
    dockerfile = Column(Text, nullable=True)
    compose_yaml = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=func.now())
    stopped_at = Column(DateTime, nullable=True)
