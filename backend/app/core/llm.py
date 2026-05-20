"""
统一 LLM 调用封装

支持两种模式:
1. Claude API 模式 (需要 ANTHROPIC_API_KEY)
2. Mock 模式 (无 API Key 时自动降级，用于测试)
"""
import json
import logging
import time
from typing import Optional
from dataclasses import dataclass

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """LLM 响应"""
    content: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0


# Token 价格 (per 1M tokens, USD)
MODEL_PRICING = {
    "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
    "claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0},
    "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
}


def _calc_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """计算费用"""
    pricing = MODEL_PRICING.get(model, {"input": 3.0, "output": 15.0})
    return (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1_000_000


async def call_llm(
    prompt: str,
    system: str = "",
    model: Optional[str] = None,
    max_tokens: int = 4096,
    temperature: float = 0.7,
) -> LLMResponse:
    """
    调用 LLM

    自动检测是否有 ANTHROPIC_API_KEY:
    - 有: 调用 Claude API
    - 无: 使用 Mock 模式

    Args:
        prompt: 用户消息
        system: 系统提示词
        model: 模型名称
        max_tokens: 最大输出 token
        temperature: 温度

    Returns:
        LLMResponse
    """
    model = model or settings.LLM_MODEL
    api_key = settings.ANTHROPIC_API_KEY

    if not api_key:
        logger.warning("No ANTHROPIC_API_KEY set, using mock mode")
        return await _mock_call(prompt, system, model)

    return await _claude_call(prompt, system, model, max_tokens, temperature, api_key)


async def _claude_call(
    prompt: str,
    system: str,
    model: str,
    max_tokens: int,
    temperature: float,
    api_key: str,
) -> LLMResponse:
    """调用 Claude API"""
    import anthropic

    client = anthropic.AsyncAnthropic(api_key=api_key)

    start = time.time()
    try:
        message = await client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system if system else anthropic.NOT_GIVEN,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        # 降级到 mock
        logger.warning("Falling back to mock mode")
        return await _mock_call(prompt, system, model)

    latency_ms = int((time.time() - start) * 1000)

    content = message.content[0].text if message.content else ""
    input_tokens = message.usage.input_tokens
    output_tokens = message.usage.output_tokens

    return LLMResponse(
        content=content,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=input_tokens + output_tokens,
        cost_usd=_calc_cost(model, input_tokens, output_tokens),
        latency_ms=latency_ms,
    )


async def _mock_call(prompt: str, system: str, model: str) -> LLMResponse:
    """Mock 模式：根据 system prompt 中的关键词返回模板数据"""
    import asyncio
    await asyncio.sleep(0.3)  # 模拟延迟

    # 根据 prompt 内容判断场景
    if "拆解" in system or "decompose" in system.lower() or "pm" in system.lower():
        content = _mock_pm_response(prompt)
    elif "架构" in system or "architect" in system.lower():
        content = _mock_architect_response(prompt)
    elif "修复" in system or "fix" in system.lower() or "故障" in system:
        content = _mock_fix_response(prompt)
    elif "devops" in system.lower() or "dockerfile" in system.lower() or "部署" in system:
        content = _mock_devops_response(prompt)
    elif "前端" in system or "vue" in system.lower() or "frontend" in system.lower():
        content = _mock_frontend_response(prompt)
    elif "测试" in system or "test" in system.lower() or "qa" in system.lower():
        content = _mock_qa_response(prompt)
    elif "review" in system.lower() or "审查" in system:
        content = _mock_review_response(prompt)
    elif "代码" in system or "code" in system.lower() or "backend" in system.lower():
        content = _mock_backend_response(prompt)
    else:
        content = json.dumps({"message": f"Mock response for: {prompt[:50]}"})

    return LLMResponse(
        content=content,
        model=f"{model}-mock",
        input_tokens=len(prompt) // 4,
        output_tokens=len(content) // 4,
        total_tokens=(len(prompt) + len(content)) // 4,
        cost_usd=0.0,
        latency_ms=300,
    )


def _mock_pm_response(prompt: str) -> str:
    """PM Agent Mock 响应"""
    return json.dumps({
        "project_name": prompt[:20],
        "tasks": [
            {
                "id": "task_1",
                "title": "设计数据模型",
                "description": f"根据需求「{prompt[:30]}」设计数据库模型，包含核心实体和关系",
                "agent": "backend",
                "depends_on": [],
            },
            {
                "id": "task_2",
                "title": "实现 API 接口",
                "description": "基于数据模型实现 RESTful API，包含 CRUD 操作",
                "agent": "backend",
                "depends_on": ["task_1"],
            },
            {
                "id": "task_3",
                "title": "实现前端页面",
                "description": "实现前端列表页和表单页，对接 API",
                "agent": "frontend",
                "depends_on": ["task_2"],
            },
            {
                "id": "task_4",
                "title": "编写测试用例",
                "description": "为 API 接口编写单元测试和集成测试",
                "agent": "qa",
                "depends_on": ["task_2"],
            },
            {
                "id": "task_5",
                "title": "代码审查",
                "description": "对生成的代码进行 Code Review，检查安全性和性能",
                "agent": "reviewer",
                "depends_on": ["task_2", "task_3"],
            },
        ],
    }, ensure_ascii=False)


def _mock_backend_response(prompt: str) -> str:
    """Backend Agent Mock 响应"""
    return json.dumps({
        "files": [
            {
                "path": "app/models/generated.py",
                "language": "python",
                "content": '''from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.db.session import Base


class GeneratedModel(Base):
    """Auto-generated model"""
    __tablename__ = "generated_items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
''',
            },
            {
                "path": "app/api/generated.py",
                "language": "python",
                "content": '''from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

router = APIRouter()


@router.get("/")
async def list_items():
    """List all items"""
    return {"items": []}


@router.post("/")
async def create_item(title: str, content: str = ""):
    """Create a new item"""
    return {"id": 1, "title": title, "content": content}
''',
            },
        ],
        "summary": f"Generated backend code for: {prompt[:50]}",
    }, ensure_ascii=False)


def _mock_architect_response(prompt: str) -> str:
    """Architect Agent Mock 响应"""
    return json.dumps({
        "tech_stack": {
            "backend": "FastAPI + SQLAlchemy",
            "database": "MySQL",
            "cache": "Redis",
            "frontend": "Vue 3 + Element Plus",
        },
        "api_schema": [
            {"method": "GET", "path": "/api/v1/posts", "description": "获取文章列表", "request_body": None, "response": {"type": "array"}},
            {"method": "POST", "path": "/api/v1/posts", "description": "创建文章", "request_body": {"title": "string", "content": "string"}, "response": {"type": "object"}},
            {"method": "GET", "path": "/api/v1/posts/{id}", "description": "获取文章详情", "request_body": None, "response": {"type": "object"}},
            {"method": "PUT", "path": "/api/v1/posts/{id}", "description": "更新文章", "request_body": {"title": "string", "content": "string"}, "response": {"type": "object"}},
            {"method": "DELETE", "path": "/api/v1/posts/{id}", "description": "删除文章", "request_body": None, "response": None},
        ],
        "db_schema": [
            {
                "table": "posts",
                "columns": [
                    {"name": "id", "type": "INT", "primary_key": True},
                    {"name": "title", "type": "VARCHAR(200)", "nullable": False},
                    {"name": "content", "type": "TEXT", "nullable": True},
                    {"name": "author_id", "type": "INT", "nullable": False},
                    {"name": "created_at", "type": "DATETIME", "nullable": False},
                ],
                "indexes": ["idx_author_id", "idx_created_at"],
            }
        ],
        "summary": f"Architecture design for: {prompt[:50]}",
    }, ensure_ascii=False)


def _mock_frontend_response(prompt: str) -> str:
    """Frontend Agent Mock 响应"""
    return json.dumps({
        "files": [
            {
                "path": "src/views/posts/index.vue",
                "language": "vue",
                "content": """<template>
  <div class="posts-page">
    <el-button type="primary" @click="showCreate = true">New Post</el-button>
    <el-table :data="posts" stripe>
      <el-table-column prop="title" label="Title" />
      <el-table-column prop="created_at" label="Created" />
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const posts = ref([])
const showCreate = ref(false)

onMounted(() => { /* fetch posts */ })
</script>
""",
            },
            {
                "path": "src/api/posts.ts",
                "language": "typescript",
                "content": """import request from '@/utils/request'

export function getPosts() {
  return request.get('/posts')
}

export function createPost(data: { title: string; content: string }) {
  return request.post('/posts', data)
}
""",
            },
        ],
        "summary": f"Generated frontend code for: {prompt[:50]}",
    }, ensure_ascii=False)


def _mock_qa_response(prompt: str) -> str:
    """QA Agent Mock 响应"""
    return json.dumps({
        "test_files": [
            {
                "path": "tests/test_posts.py",
                "language": "python",
                "content": """import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_list_posts(client: AsyncClient):
    response = await client.get("/api/v1/posts")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_create_post(client: AsyncClient):
    data = {"title": "Test Post", "content": "Hello"}
    response = await client.post("/api/v1/posts", json=data)
    assert response.status_code == 201
    assert response.json()["title"] == "Test Post"

@pytest.mark.asyncio
async def test_create_post_empty_title(client: AsyncClient):
    data = {"title": "", "content": "Hello"}
    response = await client.post("/api/v1/posts", json=data)
    assert response.status_code == 422
""",
            }
        ],
        "test_plan": [
            {"name": "test_list_posts", "type": "api", "description": "测试文章列表接口"},
            {"name": "test_create_post", "type": "api", "description": "测试创建文章"},
            {"name": "test_create_post_empty_title", "type": "api", "description": "测试空标题校验"},
        ],
        "summary": f"Generated tests for: {prompt[:50]}",
    }, ensure_ascii=False)


def _mock_review_response(prompt: str) -> str:
    """Review Agent Mock 响应"""
    return json.dumps({
        "comments": [
            {
                "file_path": "app/api/posts.py",
                "line_number": 15,
                "severity": "warning",
                "category": "performance",
                "message": "查询缺少分页，大数据量时会有性能问题",
                "suggestion": "添加 skip/limit 参数实现分页",
            },
            {
                "file_path": "app/models/post.py",
                "line_number": 8,
                "severity": "info",
                "category": "suggestion",
                "message": "建议添加 updated_at 字段追踪更新时间",
                "suggestion": "updated_at = Column(DateTime, onupdate=func.now())",
            },
            {
                "file_path": "app/api/posts.py",
                "line_number": 22,
                "severity": "error",
                "category": "security",
                "message": "缺少权限校验，任何用户可以删除他人文章",
                "suggestion": "添加 current_user 依赖，校验 post.author_id == current_user.id",
            },
        ],
        "summary": "代码整体结构清晰，但存在安全和性能问题需要修复",
        "score": 72,
        "passed": False,
    }, ensure_ascii=False)


def _mock_fix_response(prompt: str) -> str:
    """Fix Agent Mock 响应"""
    return json.dumps({
        "diagnosis": "函数缺少空值校验，当输入为 None 时触发 TypeError",
        "fix_strategy": "在函数入口添加参数校验，对 None 值返回合理默认值",
        "patches": [
            {
                "file_path": "app/api/posts.py",
                "language": "python",
                "content": """from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional

router = APIRouter()


@router.get("/")
async def list_posts(skip: int = 0, limit: int = 20):
    \"\"\"List posts with pagination\"\"\"
    if skip < 0:
        skip = 0
    if limit <= 0 or limit > 100:
        limit = 20
    return {"items": [], "skip": skip, "limit": limit}


@router.post("/")
async def create_post(title: str, content: Optional[str] = ""):
    \"\"\"Create post with validation\"\"\"
    if not title or not title.strip():
        raise HTTPException(status_code=422, detail="Title cannot be empty")
    return {"id": 1, "title": title.strip(), "content": content or ""}
""",
            }
        ],
        "confidence": 0.92,
        "summary": "添加了参数校验和空值处理，修复了 TypeError",
    }, ensure_ascii=False)


def _mock_devops_response(prompt: str) -> str:
    """DevOps Agent Mock 响应"""
    return json.dumps({
        "dockerfile": """FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
""",
        "compose": """version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=mysql+aiomysql://root:123456@db:3306/app
    depends_on:
      - db
    restart: unless-stopped

  db:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: "123456"
      MYSQL_DATABASE: app
    ports:
      - "3306:3306"
    volumes:
      - db_data:/var/lib/mysql

volumes:
  db_data:
""",
        "env_vars": {
            "DATABASE_URL": "mysql+aiomysql://root:123456@db:3306/app",
            "DEBUG": "false",
        },
        "ports": [8000],
        "health_check": "/docs",
        "summary": f"Generated Docker deployment for: {prompt[:50]}",
    }, ensure_ascii=False)
