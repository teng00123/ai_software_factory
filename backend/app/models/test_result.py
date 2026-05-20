from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Enum
from sqlalchemy.sql import func
from datetime import datetime, timezone
from app.db.session import Base
import enum


class TestStatus(str, enum.Enum):
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


class TestResult(Base):
    """测试结果"""
    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    node_id = Column(String(50), nullable=True)
    test_name = Column(String(255), nullable=False)
    status = Column(Enum(TestStatus), nullable=False)
    duration_ms = Column(Integer, default=0)
    error_msg = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=func.now())
