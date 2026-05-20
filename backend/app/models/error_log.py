from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Boolean, JSON
from sqlalchemy.sql import func
from datetime import datetime, timezone
from app.db.session import Base


class ErrorLog(Base):
    """错误日志"""
    __tablename__ = "error_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    node_id = Column(String(50), nullable=True)
    error_type = Column(String(50), nullable=True, comment="syntax, runtime, timeout, llm_error")
    error_message = Column(Text, nullable=True)
    is_recoverable = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=func.now())


class RetryHistory(Base):
    """重试历史"""
    __tablename__ = "retry_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    node_id = Column(String(50), nullable=True)
    attempt = Column(Integer, default=1)
    strategy = Column(String(50), nullable=True, comment="retry, fix_and_retry, model_switch")
    model_used = Column(String(50), nullable=True)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    status = Column(String(20), nullable=False, comment="success or failed")
    duration_ms = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=func.now())
