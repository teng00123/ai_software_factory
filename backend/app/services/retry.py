"""
Retry 策略引擎

支持多种恢复策略:
1. retry: 直接重试
2. fix_and_retry: 调用 Fix Agent 修复后重试
3. model_switch: 切换模型重试
"""
import json
import logging
import time
from typing import Optional, Callable, Awaitable

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import AgentRegistry
from app.agents.base import AgentInput, AgentOutput
from app.models.dag_node import TaskDagNode, DagNodeStatus
from app.models.error_log import ErrorLog, RetryHistory
from app.services.error_classifier import classify_error

logger = logging.getLogger(__name__)

LogCallback = Optional[Callable[[int, str], Awaitable[None]]]

# 配置
MAX_RETRIES = 3
FALLBACK_MODELS = ["claude-sonnet-4-20250514", "claude-3-5-sonnet-20241022"]


async def retry_node(
    task_id: int,
    node: TaskDagNode,
    original_prompt: str,
    db: AsyncSession,
    log_callback: LogCallback = None,
    max_retries: int = MAX_RETRIES,
) -> bool:
    """
    对失败节点执行重试策略

    Returns:
        True if recovery succeeded
    """
    error_msg = node.error_msg or "Unknown error"

    # 分类错误
    classification = classify_error(error_msg, node.agent)

    # 记录错误日志
    error_log = ErrorLog(
        task_id=task_id,
        node_id=node.node_id,
        error_type=classification.error_type,
        error_message=error_msg,
        is_recoverable=classification.is_recoverable,
    )
    db.add(error_log)
    await db.commit()

    if not classification.is_recoverable:
        if log_callback:
            await log_callback(task_id, json.dumps({
                "event": "retry_skipped",
                "node_id": node.node_id,
                "reason": "Error is not recoverable",
                "error_type": classification.error_type,
            }))
        return False

    strategy = classification.suggested_strategy

    if log_callback:
        await log_callback(task_id, json.dumps({
            "event": "retry_started",
            "node_id": node.node_id,
            "strategy": strategy,
            "error_type": classification.error_type,
            "max_retries": max_retries,
        }))

    for attempt in range(1, max_retries + 1):
        if log_callback:
            await log_callback(task_id, json.dumps({
                "event": "retry_attempt",
                "node_id": node.node_id,
                "attempt": attempt,
                "strategy": strategy,
            }))

        success = False
        output: Optional[AgentOutput] = None

        if strategy == "retry":
            output = await _direct_retry(node, original_prompt, task_id)
        elif strategy == "fix_and_retry":
            output = await _fix_and_retry(node, original_prompt, error_msg, task_id)
        elif strategy == "model_switch":
            output = await _model_switch_retry(node, original_prompt, task_id, attempt)
        else:
            output = await _direct_retry(node, original_prompt, task_id)

        success = output.success if output else False

        # 记录重试历史
        retry_record = RetryHistory(
            task_id=task_id,
            node_id=node.node_id,
            attempt=attempt,
            strategy=strategy,
            model_used=output.metadata.get("model", "") if output else "",
            input_data={"prompt": original_prompt[:200]},
            output_data=output.result if output and output.success else {"error": output.error if output else "No output"},
            status="success" if success else "failed",
            duration_ms=output.duration_ms if output else 0,
        )
        db.add(retry_record)
        await db.commit()

        if success:
            # 更新节点状态
            node.status = DagNodeStatus.COMPLETED
            node.output_data = output.result
            node.error_msg = None
            node.duration_ms = output.duration_ms
            await db.commit()

            if log_callback:
                await log_callback(task_id, json.dumps({
                    "event": "retry_success",
                    "node_id": node.node_id,
                    "attempt": attempt,
                    "strategy": strategy,
                }))
            return True
        else:
            # 如果直接 retry 失败，升级策略
            if strategy == "retry" and attempt >= 2:
                strategy = "fix_and_retry"

    # 所有重试失败
    if log_callback:
        await log_callback(task_id, json.dumps({
            "event": "retry_exhausted",
            "node_id": node.node_id,
            "total_attempts": max_retries,
        }))
    return False


async def _direct_retry(node: TaskDagNode, prompt: str, task_id: int) -> AgentOutput:
    """直接重试"""
    agent = AgentRegistry.get(node.agent)
    if not agent:
        return AgentOutput(success=False, error=f"Agent '{node.agent}' not found")

    agent_input = AgentInput(
        task_id=task_id,
        prompt=node.description or prompt,
        context={
            "title": node.label,
            "description": node.description,
            "project_context": prompt,
            "node_id": node.node_id,
        },
    )
    return await agent.execute(agent_input)


async def _fix_and_retry(node: TaskDagNode, prompt: str, error_msg: str, task_id: int) -> AgentOutput:
    """Fix Agent 修复后重试"""
    fixer = AgentRegistry.get("fixer")
    if not fixer:
        return await _direct_retry(node, prompt, task_id)

    # 先调用 Fix Agent
    fix_input = AgentInput(
        task_id=task_id,
        prompt=f"Fix error in {node.label}: {error_msg}",
        context={
            "title": node.label,
            "error_message": error_msg,
            "code_context": json.dumps(node.output_data) if node.output_data else "",
        },
    )
    fix_output = await fixer.execute(fix_input)

    if fix_output.success and fix_output.result:
        # 用修复结果作为成功输出
        return AgentOutput(
            success=True,
            result=fix_output.result,
            duration_ms=fix_output.duration_ms,
            token_usage=fix_output.token_usage,
            cost_usd=fix_output.cost_usd,
            metadata=fix_output.metadata,
        )

    # Fix 失败，降级为直接重试
    return await _direct_retry(node, prompt, task_id)


async def _model_switch_retry(node: TaskDagNode, prompt: str, task_id: int, attempt: int) -> AgentOutput:
    """切换模型重试"""
    # 简化实现：直接重试（真实场景中会切换 model 参数）
    agent = AgentRegistry.get(node.agent)
    if not agent:
        return AgentOutput(success=False, error=f"Agent '{node.agent}' not found")

    model_idx = min(attempt - 1, len(FALLBACK_MODELS) - 1)
    model = FALLBACK_MODELS[model_idx]

    agent_input = AgentInput(
        task_id=task_id,
        prompt=node.description or prompt,
        context={
            "title": node.label,
            "description": node.description,
            "project_context": prompt,
            "node_id": node.node_id,
            "model_override": model,
        },
    )
    output = await agent.execute(agent_input)
    output.metadata["model"] = model
    return output
