from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional

from app.db.session import get_db
from app.models.task import Task, TaskStatus
from app.models.task_step import TaskStep, StepStatus
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate
from app.services import scheduler
from app.api.v1.endpoints.ws import ws_manager

router = APIRouter()


@router.get("/", response_model=List[TaskResponse])
async def list_tasks(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[TaskStatus] = None,
    db: AsyncSession = Depends(get_db),
):
    """获取任务列表"""
    query = select(Task).options(selectinload(Task.steps)).order_by(Task.id.desc())
    if status_filter:
        query = query.where(Task.status == status_filter)

    result = await db.execute(query.offset(skip).limit(limit))
    tasks = result.scalars().all()
    return tasks


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """获取单个任务详情"""
    result = await db.execute(
        select(Task).options(selectinload(Task.steps)).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    return task


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task_data: TaskCreate, db: AsyncSession = Depends(get_db)):
    """创建新任务"""
    task = Task(
        prompt=task_data.prompt,
        status=TaskStatus.PENDING,
        current_agent=task_data.current_agent,
    )

    db.add(task)
    await db.commit()
    await db.refresh(task)

    # 重新查询带 eager load
    result = await db.execute(
        select(Task).options(selectinload(Task.steps)).where(Task.id == task.id)
    )
    return result.scalar_one()


@router.post("/{task_id}/run", response_model=TaskResponse)
async def run_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """
    触发执行任务

    调用调度器执行任务，根据 current_agent 分配给对应 Agent。
    如果未设置 current_agent，默认使用 echo agent。
    """
    # 检查任务存在
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    if task.status == TaskStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Task is already running"
        )

    # 定义 WebSocket 日志回调
    async def log_callback(tid: int, message: str):
        await ws_manager.send_to_task(tid, message)

    # 执行任务
    try:
        await scheduler.execute_task(task_id, db, log_callback=log_callback)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # 重新查询带 eager load 返回最新状态
    result = await db.execute(
        select(Task).options(selectinload(Task.steps)).where(Task.id == task_id)
    )
    return result.scalar_one()


@router.get("/{task_id}/steps", summary="获取任务执行步骤")
async def get_task_steps(task_id: int, db: AsyncSession = Depends(get_db)):
    """获取指定任务的所有执行步骤"""
    result = await db.execute(
        select(TaskStep).where(TaskStep.task_id == task_id).order_by(TaskStep.id)
    )
    steps = result.scalars().all()
    return steps


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新任务信息"""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # 更新字段
    if task_update.status is not None:
        task.status = task_update.status
    if task_update.current_agent is not None:
        task.current_agent = task_update.current_agent

    await db.commit()

    # 重新查询带 eager load
    result = await db.execute(
        select(Task).options(selectinload(Task.steps)).where(Task.id == task_id)
    )
    return result.scalar_one()


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """删除任务"""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    await db.delete(task)
    await db.commit()