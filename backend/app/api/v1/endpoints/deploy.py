from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.db.session import get_db
from app.models.task import Task
from app.models.deployment import Deployment, DeployStatus
from app.models.artifact import TaskArtifact
from app.agents import AgentRegistry
from app.agents.base import AgentInput
from app.services.preview import create_preview, stop_preview, destroy_preview
from app.services.git_ops import commit_artifacts

router = APIRouter()


# --- Schemas ---

class DeploymentResponse(BaseModel):
    id: int
    task_id: int
    status: DeployStatus
    container_id: Optional[str] = None
    preview_url: Optional[str] = None
    port: Optional[int] = None
    build_log: Optional[str] = None
    dockerfile: Optional[str] = None
    compose_yaml: Optional[str] = None
    created_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class GitCommitResponse(BaseModel):
    commit_hash: str
    message: str
    files_changed: int
    branch: str
    timestamp: str


class PublishResponse(BaseModel):
    git: GitCommitResponse
    deployment: DeploymentResponse


# --- Endpoints ---

@router.post("/preview", response_model=DeploymentResponse, summary="启动 Preview 环境")
async def deploy_preview(task_id: int, db: AsyncSession = Depends(get_db)):
    """
    为指定任务启动 Preview 环境:
    1. 调用 DevOps Agent 生成 Dockerfile
    2. 启动容器
    3. 返回 Preview URL
    """
    # 检查任务
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    # 获取产物文件列表
    result = await db.execute(select(TaskArtifact).where(TaskArtifact.task_id == task_id))
    artifacts = result.scalars().all()
    file_list = "\n".join([f"- {a.file_path} ({a.language})" for a in artifacts]) or "No files"

    # 调用 DevOps Agent
    devops = AgentRegistry.get("devops")
    if not devops:
        raise HTTPException(status_code=500, detail="DevOps Agent not registered")

    devops_input = AgentInput(
        task_id=task_id,
        prompt=task.prompt,
        context={"file_list": file_list},
    )
    output = await devops.execute(devops_input)

    if not output.success:
        raise HTTPException(status_code=500, detail=f"DevOps Agent failed: {output.error}")

    dockerfile = output.result.get("dockerfile", "")
    compose_yaml = output.result.get("compose", "")

    # 创建 Preview 环境
    deployment = await create_preview(task_id, dockerfile, compose_yaml, db)
    return deployment


@router.get("/preview/{deployment_id}", response_model=DeploymentResponse, summary="获取 Preview 状态")
async def get_preview(deployment_id: int, db: AsyncSession = Depends(get_db)):
    """获取 Preview 环境状态"""
    result = await db.execute(select(Deployment).where(Deployment.id == deployment_id))
    deployment = result.scalar_one_or_none()
    if not deployment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found")
    return deployment


@router.get("/preview", response_model=List[DeploymentResponse], summary="获取 Preview 列表")
async def list_previews(task_id: Optional[int] = None, db: AsyncSession = Depends(get_db)):
    """获取所有 Preview 环境列表，可按 task_id 筛选"""
    query = select(Deployment).order_by(Deployment.id.desc())
    if task_id:
        query = query.where(Deployment.task_id == task_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/preview/{deployment_id}/stop", response_model=DeploymentResponse, summary="停止 Preview")
async def stop_preview_endpoint(deployment_id: int, db: AsyncSession = Depends(get_db)):
    """停止 Preview 环境"""
    deployment = await stop_preview(deployment_id, db)
    if not deployment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found")
    return deployment


@router.delete("/preview/{deployment_id}", status_code=status.HTTP_204_NO_CONTENT, summary="销毁 Preview")
async def delete_preview(deployment_id: int, db: AsyncSession = Depends(get_db)):
    """销毁 Preview 环境"""
    success = await destroy_preview(deployment_id, db)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found")


@router.get("/preview/{deployment_id}/logs", summary="获取构建日志")
async def get_preview_logs(deployment_id: int, db: AsyncSession = Depends(get_db)):
    """获取 Preview 环境的构建日志"""
    result = await db.execute(select(Deployment).where(Deployment.id == deployment_id))
    deployment = result.scalar_one_or_none()
    if not deployment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found")
    return {"logs": deployment.build_log or ""}


@router.post("/publish", response_model=PublishResponse, summary="一键发布")
async def publish_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """
    一键发布：
    1. Git commit 产物
    2. 启动 Preview 环境
    """
    # 检查任务
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    # 获取产物
    result = await db.execute(select(TaskArtifact).where(TaskArtifact.task_id == task_id))
    artifacts = result.scalars().all()
    if not artifacts:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No artifacts to publish")

    # Git commit
    artifact_dicts = [{"file_path": a.file_path, "content": a.content} for a in artifacts]
    git_result = await commit_artifacts(task_id, artifact_dicts)

    # Deploy
    file_list = "\n".join([f"- {a.file_path}" for a in artifacts])
    devops = AgentRegistry.get("devops")
    devops_input = AgentInput(task_id=task_id, prompt=task.prompt, context={"file_list": file_list})
    output = await devops.execute(devops_input)

    dockerfile = output.result.get("dockerfile", "") if output.success else ""
    compose_yaml = output.result.get("compose", "") if output.success else ""

    deployment = await create_preview(task_id, dockerfile, compose_yaml, db)

    return PublishResponse(
        git=GitCommitResponse(**git_result),
        deployment=deployment,
    )
