from app.agents.base import BaseAgent, AgentInput, AgentOutput  # noqa: F401
from app.agents.registry import AgentRegistry  # noqa: F401

# 导入所有 Agent 以触发注册
from app.agents.echo import EchoAgent  # noqa: F401
from app.agents.pm import PMAgent  # noqa: F401
from app.agents.architect import ArchitectAgent  # noqa: F401
from app.agents.backend_dev import BackendAgent  # noqa: F401
from app.agents.frontend_dev import FrontendAgent  # noqa: F401
from app.agents.qa import QAAgent  # noqa: F401
from app.agents.reviewer import ReviewAgent  # noqa: F401
from app.agents.fixer import FixAgent  # noqa: F401
from app.agents.devops import DevOpsAgent  # noqa: F401
