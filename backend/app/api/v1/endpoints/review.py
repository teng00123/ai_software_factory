from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel

from app.db.session import get_db
from app.models.review import ReviewComment, Severity
from app.models.test_result import TestResult, TestStatus
from app.models.sandbox_run import SandboxRun

router = APIRouter()


# --- Schemas ---

class ReviewCommentResponse(BaseModel):
    id: int
    task_id: int
    node_id: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    severity: Severity
    category: Optional[str] = None
    message: str
    suggestion: Optional[str] = None

    class Config:
        from_attributes = True


class ReviewSummaryResponse(BaseModel):
    total: int
    errors: int
    warnings: int
    infos: int
    comments: List[ReviewCommentResponse]


class TestResultResponse(BaseModel):
    id: int
    task_id: int
    node_id: Optional[str] = None
    test_name: str
    status: TestStatus
    duration_ms: int = 0
    error_msg: Optional[str] = None

    class Config:
        from_attributes = True


class TestSummaryResponse(BaseModel):
    total: int
    passed: int
    failed: int
    errors: int
    skipped: int
    results: List[TestResultResponse]


class SandboxRunResponse(BaseModel):
    id: int
    task_id: int
    command: Optional[str] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    exit_code: int = 0
    duration_ms: int = 0

    class Config:
        from_attributes = True


# --- Endpoints ---

@router.get("/{task_id}/review", response_model=ReviewSummaryResponse, summary="获取 Review 结果")
async def get_task_review(task_id: int, db: AsyncSession = Depends(get_db)):
    """获取任务的 Code Review 结果"""
    result = await db.execute(
        select(ReviewComment).where(ReviewComment.task_id == task_id).order_by(ReviewComment.id)
    )
    comments = result.scalars().all()

    errors = sum(1 for c in comments if c.severity == Severity.ERROR)
    warnings = sum(1 for c in comments if c.severity == Severity.WARNING)
    infos = sum(1 for c in comments if c.severity == Severity.INFO)

    return ReviewSummaryResponse(
        total=len(comments),
        errors=errors,
        warnings=warnings,
        infos=infos,
        comments=comments,
    )


@router.get("/{task_id}/tests", response_model=TestSummaryResponse, summary="获取测试结果")
async def get_task_tests(task_id: int, db: AsyncSession = Depends(get_db)):
    """获取任务的测试结果"""
    result = await db.execute(
        select(TestResult).where(TestResult.task_id == task_id).order_by(TestResult.id)
    )
    results = result.scalars().all()

    passed = sum(1 for r in results if r.status == TestStatus.PASSED)
    failed = sum(1 for r in results if r.status == TestStatus.FAILED)
    errors = sum(1 for r in results if r.status == TestStatus.ERROR)
    skipped = sum(1 for r in results if r.status == TestStatus.SKIPPED)

    return TestSummaryResponse(
        total=len(results),
        passed=passed,
        failed=failed,
        errors=errors,
        skipped=skipped,
        results=results,
    )


@router.get("/{task_id}/sandbox", response_model=List[SandboxRunResponse], summary="获取沙箱执行记录")
async def get_sandbox_runs(task_id: int, db: AsyncSession = Depends(get_db)):
    """获取任务的沙箱执行记录"""
    result = await db.execute(
        select(SandboxRun).where(SandboxRun.task_id == task_id).order_by(SandboxRun.id.desc())
    )
    return result.scalars().all()
