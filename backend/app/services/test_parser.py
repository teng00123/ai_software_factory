"""
测试报告解析器

解析 pytest 输出为结构化数据。
"""
import re
from typing import List
from dataclasses import dataclass


@dataclass
class TestCaseResult:
    """单个测试用例结果"""
    name: str
    status: str  # passed, failed, error, skipped
    duration_ms: int = 0
    error_msg: str = ""


@dataclass
class TestReport:
    """测试报告"""
    total: int
    passed: int
    failed: int
    errors: int
    skipped: int
    duration_ms: int
    cases: List[TestCaseResult]
    raw_output: str


def parse_pytest_output(output: str) -> TestReport:
    """
    解析 pytest 输出

    Args:
        output: pytest 的 stdout 输出

    Returns:
        TestReport
    """
    cases = []

    # 解析单行结果: test_name PASSED/FAILED
    for line in output.splitlines():
        line = line.strip()
        if "PASSED" in line:
            name = line.split(" ")[0].strip()
            if name and not name.startswith("="):
                cases.append(TestCaseResult(name=name, status="passed"))
        elif "FAILED" in line:
            name = line.split(" ")[0].strip()
            if name and not name.startswith("="):
                cases.append(TestCaseResult(name=name, status="failed"))
        elif "ERROR" in line:
            name = line.split(" ")[0].strip()
            if name and not name.startswith("="):
                cases.append(TestCaseResult(name=name, status="error"))
        elif "SKIPPED" in line:
            name = line.split(" ")[0].strip()
            if name and not name.startswith("="):
                cases.append(TestCaseResult(name=name, status="skipped"))

    # 解析总结行: ===== N passed in X.XXs =====
    passed = len([c for c in cases if c.status == "passed"])
    failed = len([c for c in cases if c.status == "failed"])
    errors = len([c for c in cases if c.status == "error"])
    skipped = len([c for c in cases if c.status == "skipped"])
    total = len(cases)

    # 尝试解析总时间
    duration_ms = 0
    time_match = re.search(r"(\d+\.?\d*)\s*s\s*=", output)
    if time_match:
        duration_ms = int(float(time_match.group(1)) * 1000)

    return TestReport(
        total=total,
        passed=passed,
        failed=failed,
        errors=errors,
        skipped=skipped,
        duration_ms=duration_ms,
        cases=cases,
        raw_output=output,
    )
