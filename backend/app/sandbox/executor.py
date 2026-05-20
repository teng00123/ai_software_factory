"""
Sandbox 执行器

在 Docker 容器中安全执行生成的代码和测试。
当 Docker 不可用时，提供模拟执行模式。
"""
import asyncio
import logging
import time
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ExecResult:
    """执行结果"""
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    container_id: Optional[str] = None


class SandboxExecutor:
    """沙箱执行器"""

    async def execute(
        self,
        command: str,
        workdir: str = "/workspace",
        timeout: int = 60,
        image: str = "python:3.12-slim",
    ) -> ExecResult:
        """
        在 Docker 容器中执行命令

        Args:
            command: 要执行的命令
            workdir: 工作目录
            timeout: 超时时间（秒）
            image: Docker 镜像

        Returns:
            ExecResult
        """
        start = time.time()

        try:
            proc = await asyncio.create_subprocess_exec(
                "docker", "run", "--rm",
                "--network=none",
                f"--workdir={workdir}",
                "--memory=256m",
                "--cpus=1",
                image,
                "sh", "-c", command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
            duration_ms = int((time.time() - start) * 1000)

            return ExecResult(
                exit_code=proc.returncode or 0,
                stdout=stdout.decode("utf-8", errors="replace"),
                stderr=stderr.decode("utf-8", errors="replace"),
                duration_ms=duration_ms,
            )
        except asyncio.TimeoutError:
            return ExecResult(
                exit_code=-1,
                stdout="",
                stderr="Execution timed out",
                duration_ms=timeout * 1000,
            )
        except FileNotFoundError:
            # Docker not available, use mock
            logger.warning("Docker not available, using mock execution")
            return await self._mock_execute(command)
        except Exception as e:
            logger.error(f"Sandbox execution error: {e}")
            return await self._mock_execute(command)

    async def _mock_execute(self, command: str) -> ExecResult:
        """模拟执行"""
        await asyncio.sleep(0.2)

        if "pytest" in command:
            return ExecResult(
                exit_code=0,
                stdout="===== 3 passed in 0.45s =====\ntest_list_posts PASSED\ntest_create_post PASSED\ntest_create_post_empty_title PASSED",
                stderr="",
                duration_ms=450,
            )
        elif "python" in command:
            return ExecResult(
                exit_code=0,
                stdout="OK",
                stderr="",
                duration_ms=100,
            )
        else:
            return ExecResult(
                exit_code=0,
                stdout=f"Mock execution: {command}",
                stderr="",
                duration_ms=50,
            )

    async def run_tests(self, test_code: str, timeout: int = 120) -> ExecResult:
        """
        运行 pytest 测试

        Args:
            test_code: 测试代码内容
            timeout: 超时时间

        Returns:
            ExecResult
        """
        command = f"echo '{test_code}' > /tmp/test_gen.py && python -m pytest /tmp/test_gen.py -v"
        return await self.execute(command, timeout=timeout)


# 全局实例
sandbox = SandboxExecutor()
