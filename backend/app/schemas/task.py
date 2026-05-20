from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from decimal import Decimal

from app.models.task import TaskStatus
from app.models.task_step import StepStatus


class TaskBase(BaseModel):
    prompt: str = Field(..., description="用户输入的需求提示")


class TaskCreate(TaskBase):
    current_agent: Optional[str] = Field(None, description="指定执行的Agent")


class TaskUpdate(BaseModel):
    status: Optional[TaskStatus] = Field(None, description="任务状态")
    current_agent: Optional[str] = Field(None, description="当前执行的Agent")


class TaskStepResponse(BaseModel):
    id: int
    agent: str
    input: Optional[str] = None
    output: Optional[str] = None
    status: StepStatus
    duration: Optional[int] = None
    token_usage: int = 0
    cost_usd: float = 0.0
    error_msg: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TaskResponse(BaseModel):
    id: int
    prompt: str
    status: TaskStatus
    current_agent: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    steps: List[TaskStepResponse] = []

    class Config:
        from_attributes = True
