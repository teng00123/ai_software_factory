import json
import asyncio
import logging
from typing import Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        # task_id -> set of websocket connections
        self._connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, task_id: int):
        """接受 WebSocket 连接"""
        await websocket.accept()
        if task_id not in self._connections:
            self._connections[task_id] = set()
        self._connections[task_id].add(websocket)
        logger.info(f"WebSocket connected for task {task_id}")

    def disconnect(self, websocket: WebSocket, task_id: int):
        """断开 WebSocket 连接"""
        if task_id in self._connections:
            self._connections[task_id].discard(websocket)
            if not self._connections[task_id]:
                del self._connections[task_id]
        logger.info(f"WebSocket disconnected for task {task_id}")

    async def send_to_task(self, task_id: int, message: str):
        """向指定任务的所有连接发送消息"""
        if task_id not in self._connections:
            return
        disconnected = set()
        for ws in self._connections[task_id]:
            try:
                await ws.send_text(message)
            except Exception:
                disconnected.add(ws)
        # 清理断开的连接
        for ws in disconnected:
            self._connections[task_id].discard(ws)


# 全局连接管理器
ws_manager = ConnectionManager()


@router.websocket("/tasks/{task_id}")
async def task_websocket(websocket: WebSocket, task_id: int):
    """
    任务执行日志 WebSocket 端点

    客户端连接后会实时接收该任务的执行日志：
    - task_started: 任务开始执行
    - step_started: 某个 step 开始
    - task_completed: 任务执行完成
    - task_failed: 任务执行失败
    """
    await ws_manager.connect(websocket, task_id)
    try:
        # 发送连接确认
        await websocket.send_text(json.dumps({
            "event": "connected",
            "task_id": task_id,
            "message": f"Connected to task {task_id} log stream",
        }))
        # 保持连接，等待客户端断开
        while True:
            # 接收客户端心跳或命令
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"event": "pong"}))
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, task_id)
    except Exception:
        ws_manager.disconnect(websocket, task_id)
