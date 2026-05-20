"""
错误分类器

将错误信息分类为可恢复/不可恢复，并确定错误类型。
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class ErrorClassification:
    """错误分类结果"""
    error_type: str  # syntax, runtime, timeout, llm_error, network, unknown
    is_recoverable: bool
    suggested_strategy: str  # retry, fix_and_retry, model_switch, manual
    confidence: float  # 0-1


def classify_error(error_message: str, agent: Optional[str] = None) -> ErrorClassification:
    """
    对错误信息进行分类

    Args:
        error_message: 错误信息
        agent: 触发错误的 Agent 名称

    Returns:
        ErrorClassification
    """
    msg = error_message.lower()

    # 超时错误
    if "timeout" in msg or "timed out" in msg:
        return ErrorClassification(
            error_type="timeout",
            is_recoverable=True,
            suggested_strategy="retry",
            confidence=0.9,
        )

    # 网络错误
    if "connection" in msg or "network" in msg or "dns" in msg:
        return ErrorClassification(
            error_type="network",
            is_recoverable=True,
            suggested_strategy="retry",
            confidence=0.85,
        )

    # LLM 相关错误
    if "rate limit" in msg or "429" in msg:
        return ErrorClassification(
            error_type="llm_error",
            is_recoverable=True,
            suggested_strategy="retry",
            confidence=0.95,
        )
    if "api" in msg and ("error" in msg or "invalid" in msg):
        return ErrorClassification(
            error_type="llm_error",
            is_recoverable=True,
            suggested_strategy="model_switch",
            confidence=0.7,
        )

    # JSON 解析错误（LLM 输出格式不对）
    if "json" in msg or "parse" in msg or "decode" in msg:
        return ErrorClassification(
            error_type="llm_error",
            is_recoverable=True,
            suggested_strategy="retry",
            confidence=0.8,
        )

    # 语法错误
    if "syntax" in msg or "indentation" in msg or "unexpected" in msg:
        return ErrorClassification(
            error_type="syntax",
            is_recoverable=True,
            suggested_strategy="fix_and_retry",
            confidence=0.75,
        )

    # 运行时错误
    if "typeerror" in msg or "nameerror" in msg or "attributeerror" in msg or "importerror" in msg:
        return ErrorClassification(
            error_type="runtime",
            is_recoverable=True,
            suggested_strategy="fix_and_retry",
            confidence=0.7,
        )

    # 权限/配置错误（通常不可自动恢复）
    if "permission" in msg or "authentication" in msg or "forbidden" in msg:
        return ErrorClassification(
            error_type="runtime",
            is_recoverable=False,
            suggested_strategy="manual",
            confidence=0.8,
        )

    # 未知错误
    return ErrorClassification(
        error_type="unknown",
        is_recoverable=True,
        suggested_strategy="fix_and_retry",
        confidence=0.5,
    )
