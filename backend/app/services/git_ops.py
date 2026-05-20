"""
Git 操作服务

模拟将产物提交到 Git 仓库。
"""
import logging
from typing import List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


async def commit_artifacts(
    task_id: int,
    artifacts: List[dict],
    message: str = "",
) -> dict:
    """
    将任务产物提交到 Git

    Args:
        task_id: 任务 ID
        artifacts: [{"file_path": "...", "content": "..."}]
        message: commit message

    Returns:
        Git commit 信息
    """
    if not message:
        message = f"feat: auto-generated code from task #{task_id}"

    # Mock: 模拟 git 操作
    commit_hash = f"abc{task_id:04d}"
    files_changed = len(artifacts)

    logger.info(f"Git commit: {message} ({files_changed} files)")

    return {
        "commit_hash": commit_hash,
        "message": message,
        "files_changed": files_changed,
        "branch": f"auto/task-{task_id}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
