# AI Software Factory

> 多 Agent 协作研发平台 — 模拟真实软件团队，实现需求拆解、代码生成、自动测试、Code Review、错误恢复、一键部署的全流程自动化。

## 架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Vue 3)                         │
│  Dashboard │ Tasks │ DAG View │ Code Viewer │ Deploy │ Metrics  │
└──────────────────────────────┬──────────────────────────────────┘
                               │ REST API + WebSocket
┌──────────────────────────────▼──────────────────────────────────┐
│                        Backend (FastAPI)                         │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    Agent Layer (9 Agents)                 │    │
│  │  PM │ Architect │ Backend │ Frontend │ QA │ Review │ Fix │    │
│  │  DevOps │ Echo                                           │    │
│  └─────────────────────────┬───────────────────────────────┘    │
│                             │                                    │
│  ┌──────────────┐  ┌───────▼───────┐  ┌──────────────────┐    │
│  │ DAG Scheduler │  │   LLM Layer   │  │  Error Recovery  │    │
│  │ (拓扑排序执行) │  │ (Claude/Mock) │  │ (Retry + Fix)   │    │
│  └──────────────┘  └───────────────┘  └──────────────────┘    │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌─────────┐  ┌──────────────┐   │
│  │ Sandbox  │  │ Git Ops  │  │ Preview │  │   Metrics    │   │
│  │ (Docker) │  │ (Patch)  │  │ (Deploy)│  │ (Trace/Cost) │   │
│  └──────────┘  └──────────┘  └─────────┘  └──────────────┘   │
└──────────────────────────────────────────────────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   MySQL + Alembic   │
                    └─────────────────────┘
```

## 核心特性

### Multi-Agent DAG 编排
- 9 个专业 Agent 协作，支持并行调度与依赖控制
- 拓扑排序自动确定执行顺序
- 实时 WebSocket 推送执行状态

### 完整研发链
```
输入需求 → PM 拆解 → 代码生成 → 测试 → Review → 部署
```

### 自动错误恢复
- 错误分类器自动判断可恢复性
- 3 种策略：直接重试 / Fix Agent 修复 / 模型切换
- 重试历史追溯

### 可观测平台
- Token / Cost 全链路追踪
- Agent 维度性能统计
- 执行回放 (Replay)
- ECharts 可视化 Dashboard

### 一键部署
- DevOps Agent 生成 Dockerfile + docker-compose
- Preview 环境即时启动
- Git 自动提交

## 技术栈

| 层 | 技术 |
|---|---|
| Frontend | Vue 3 + TypeScript + Element Plus + VueFlow + Monaco Editor + ECharts |
| Backend | FastAPI + SQLAlchemy (async) + Alembic + Pydantic v2 |
| LLM | Claude API (Anthropic SDK) + Mock 模式 |
| Database | MySQL (aiomysql) |
| Sandbox | Docker Executor |
| Auth | JWT (python-jose + bcrypt) |

## 项目结构

```
ai_software_factory/
├── backend/
│   ├── main.py                    # FastAPI 入口
│   ├── alembic/                   # 数据库迁移
│   ├── app/
│   │   ├── agents/                # 9 个 Agent 实现
│   │   │   ├── base.py            # Agent 基类
│   │   │   ├── registry.py        # 注册表
│   │   │   ├── pm.py              # 需求拆解
│   │   │   ├── architect.py       # 架构设计
│   │   │   ├── backend_dev.py     # 后端代码生成
│   │   │   ├── frontend_dev.py    # 前端代码生成
│   │   │   ├── qa.py              # 测试生成
│   │   │   ├── reviewer.py        # Code Review
│   │   │   ├── fixer.py           # 错误修复
│   │   │   └── devops.py          # 部署配置生成
│   │   ├── api/v1/endpoints/      # 35 个 REST API
│   │   ├── core/                  # 配置、LLM、安全
│   │   ├── models/                # 11 张数据库表
│   │   ├── prompts/               # Agent Prompt 模板
│   │   ├── sandbox/               # Docker 沙箱 + Git Patch
│   │   ├── schemas/               # Pydantic 序列化
│   │   └── services/              # 调度器、Metrics、Retry
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/                   # 后端接口封装
│   │   ├── components/            # 可复用组件
│   │   │   ├── DagView.vue        # DAG 可视化 (VueFlow)
│   │   │   ├── CodeViewer.vue     # 代码查看 (Monaco)
│   │   │   ├── PipelineProgress.vue
│   │   │   ├── ReviewPanel.vue
│   │   │   ├── TestReport.vue
│   │   │   ├── RecoveryPanel.vue
│   │   │   └── TraceTimeline.vue
│   │   ├── views/                 # 页面
│   │   │   ├── dashboard/         # 可观测 Dashboard
│   │   │   ├── tasks/             # 任务管理 + 详情
│   │   │   ├── deploy/            # 部署管理
│   │   │   └── login/             # 登录
│   │   ├── i18n/                  # 中英文国际化
│   │   ├── router/                # 路由
│   │   └── stores/                # Pinia 状态管理
│   └── package.json
└── docs/
    └── ITERATION_PLAN.md          # 技术迭代计划
```

## 快速开始

### 环境要求

- Python 3.12+
- Node.js 18+
- MySQL 8.0+

### 后端启动

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入数据库密码和 API Key

# 数据库迁移
alembic upgrade head

# 启动
python main.py
```

### 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 配置环境变量
cp .env.example .env

# 启动开发服务器
npm run dev
```

### 访问

- 前端：http://localhost:3000
- 后端 API 文档：http://localhost:8000/docs
- 初始化管理员：页面底部点击「初始化管理员账号」(admin / admin123)

## API 概览

| 模块 | 接口数 | 说明 |
|------|--------|------|
| Auth | 3 | 登录、用户信息、初始化 |
| Tasks | 7 | CRUD + 执行 + 步骤查询 |
| DAG | 3 | DAG 查询 + 执行 + 产物 |
| Review & Test | 3 | Code Review + 测试结果 + 沙箱记录 |
| Recovery | 4 | 错误日志 + 重试历史 + 自动修复 |
| Metrics | 5 | 总览 + Agent 统计 + 费用趋势 + Trace + Replay |
| Deploy | 7 | Preview CRUD + 日志 + 一键发布 |
| Agents | 2 | Agent 列表 + 详情 |
| WebSocket | 1 | 实时日志流 |

## Agent 列表

| Agent | 职责 | 输出 |
|-------|------|------|
| PM | 需求拆解为子任务 DAG | Task Graph (JSON) |
| Architect | 技术选型 + API/DB Schema | Architecture Spec |
| Backend | FastAPI 代码生成 | Python 文件 |
| Frontend | Vue 组件生成 | Vue/TS 文件 |
| QA | pytest 测试生成 | 测试代码 + 报告 |
| Reviewer | Code Review | 评论 + 评分 |
| Fixer | 错误分析 + 修复 | Recovery Patch |
| DevOps | Dockerfile + Compose | 部署配置 |
| Echo | 测试用 | 原样返回 |

## LLM 模式

| 模式 | 条件 | 说明 |
|------|------|------|
| Claude API | 配置了 `ANTHROPIC_API_KEY` | 调用真实 Claude 模型 |
| Mock | 未配置 API Key | 使用模板数据，零成本跑通全流程 |

## 数据库表

```
users, tasks, task_steps, task_dag_nodes, task_artifacts,
review_comments, test_results, sandbox_runs,
error_logs, retry_history, agent_metrics,
execution_snapshots, deployments
```

## 开发迭代

| Sprint | 内容 | 状态 |
|--------|------|------|
| Sprint 0 | 基础框架 + Agent 机制 + 任务 CRUD | ✅ |
| Sprint 1 | PM + Backend Agent + DAG 调度 + 可视化 | ✅ |
| Sprint 2 | 6 Agent 全链路 + Sandbox + Review/Test | ✅ |
| Sprint 3 | 错误恢复系统 (Fix + Retry + Fallback) | ✅ |
| Sprint 4 | 可观测平台 (Metrics + Trace + Replay) | ✅ |
| Sprint 5 | DevOps Agent + Preview 部署 + 一键发布 | ✅ |

## License

MIT
