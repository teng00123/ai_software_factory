from fastapi import APIRouter

from app.api.v1.endpoints import tasks, auth, agents, ws, dag, review, recovery, metrics, deploy

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(dag.router, prefix="/tasks", tags=["dag"])
api_router.include_router(review.router, prefix="/tasks", tags=["review & test"])
api_router.include_router(recovery.router, prefix="/tasks", tags=["recovery"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
api_router.include_router(deploy.router, prefix="/deploy", tags=["deploy"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(ws.router, prefix="/ws", tags=["websocket"])
