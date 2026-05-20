"""
Preview 环境管理

负责启动/停止/销毁 Preview 容器，模拟真实部署。
当 Docker 不可用时使用模拟模式。
"""
import asyncio
import logging
import random
from typing import Optional
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.deployment import Deployment, DeployStatus
from app.models.artifact import TaskArtifact

logger = logging.getLogger(__name__)

# 端口池
_used_ports: set = set()
PORT_RANGE = (9000, 9100)


def _allocate_port() -> int:
    """分配一个可用端口"""
    for port in range(PORT_RANGE[0], PORT_RANGE[1]):
        if port not in _used_ports:
            _used_ports.add(port)
            return port
    return random.randint(9100, 9999)


def _release_port(port: int):
    """释放端口"""
    _used_ports.discard(port)


async def create_preview(
    task_id: int,
    dockerfile: str,
    compose_yaml: str,
    db: AsyncSession,
) -> Deployment:
    """
    创建 Preview 环境

    实际流程: docker-compose up -d
    Mock 流程: 直接标记为 running 并生成 URL
    """
    port = _allocate_port()
    preview_url = f"http://localhost:{port}"

    deployment = Deployment(
        task_id=task_id,
        status=DeployStatus.BUILDING,
        port=port,
        dockerfile=dockerfile,
        compose_yaml=compose_yaml,
        build_log="",
    )
    db.add(deployment)
    await db.commit()
    await db.refresh(deployment)

    # 模拟构建过程
    build_logs = []
    build_logs.append(f"[{_now()}] Starting build...")
    build_logs.append(f"[{_now()}] Step 1/5: FROM python:3.12-slim")
    await asyncio.sleep(0.2)
    build_logs.append(f"[{_now()}] Step 2/5: COPY requirements.txt .")
    build_logs.append(f"[{_now()}] Step 3/5: RUN pip install")
    await asyncio.sleep(0.2)
    build_logs.append(f"[{_now()}] Step 4/5: COPY . .")
    build_logs.append(f"[{_now()}] Step 5/5: EXPOSE 8000")
    await asyncio.sleep(0.1)
    build_logs.append(f"[{_now()}] Build complete!")
    build_logs.append(f"[{_now()}] Starting container on port {port}...")
    build_logs.append(f"[{_now()}] Container started successfully")
    build_logs.append(f"[{_now()}] Preview URL: {preview_url}")

    deployment.build_log = "\n".join(build_logs)
    deployment.status = DeployStatus.RUNNING
    deployment.preview_url = preview_url
    deployment.container_id = f"mock-container-{deployment.id}"
    await db.commit()

    return deployment


async def stop_preview(deployment_id: int, db: AsyncSession) -> Optional[Deployment]:
    """停止 Preview 环境"""
    result = await db.execute(select(Deployment).where(Deployment.id == deployment_id))
    deployment = result.scalar_one_or_none()
    if not deployment:
        return None

    deployment.status = DeployStatus.STOPPED
    deployment.stopped_at = datetime.now(timezone.utc)
    if deployment.port:
        _release_port(deployment.port)
    await db.commit()
    return deployment


async def destroy_preview(deployment_id: int, db: AsyncSession) -> bool:
    """销毁 Preview 环境"""
    result = await db.execute(select(Deployment).where(Deployment.id == deployment_id))
    deployment = result.scalar_one_or_none()
    if not deployment:
        return False

    if deployment.port:
        _release_port(deployment.port)
    await db.delete(deployment)
    await db.commit()
    return True


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%H:%M:%S")
