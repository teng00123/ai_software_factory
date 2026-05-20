from fastapi import APIRouter

from app.agents import AgentRegistry

router = APIRouter()


@router.get("/", summary="获取已注册 Agent 列表")
async def list_agents():
    """获取所有已注册的 Agent 信息"""
    return AgentRegistry.info()


@router.get("/{name}", summary="获取 Agent 详情")
async def get_agent(name: str):
    """获取指定 Agent 的详细信息"""
    agent = AgentRegistry.get(name)
    if not agent:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{name}' not found",
        )
    return {
        "name": agent.name,
        "description": agent.description,
    }
