# AI Software Factory — 技术迭代计划（前后端分离）

> 基于 ROADMAP.md 细化，面向实际开发落地，每个 Sprint 明确前后端各自的交付物、接口契约、数据库变更。

---

## 技术栈总览

| 层 | 技术 |
|---|---|
| Frontend | Vue 3 + TypeScript + Element Plus + VueFlow + Monaco Editor + WebSocket |
| Backend | FastAPI + SQLAlchemy(async) + Alembic + Celery + Redis + LangGraph |
| Database | MySQL (当前) / PostgreSQL (后续迁移) |
| Sandbox | Docker Executor + Git Patch + Pytest Runner |
| Infra | Docker Compose → Helm → K8s |

---

## Sprint 0：基础框架搭建（第 1 周）

### 目标

跑通最小闭环：创建任务 → 单 Agent 执行 → 返回结果 → 前端展示

---

### 后端任务

| # | 任务 | 输出 |
|---|------|------|
| B0.1 | 数据库迁移管理（Alembic 初始化） | `alembic/` 目录，初始迁移脚本 |
| B0.2 | Agent 注册表设计 | `app/agents/registry.py`，Agent 基类 + 注册装饰器 |
| B0.3 | Agent 基类抽象 | `app/agents/base.py`：`BaseAgent.run(input) → output` |
| B0.4 | Echo Agent（测试用） | `app/agents/echo.py`，接收输入原样返回 |
| B0.5 | 任务调度器 V1（同步） | `app/services/scheduler.py`，按 Task.current_agent 调用对应 Agent |
| B0.6 | 任务执行接口 | `POST /api/v1/tasks/{id}/run` 触发执行，更新 task_steps |
| B0.7 | WebSocket 日志推送 | `app/api/v1/endpoints/ws.py`，实时推送 step 执行日志 |

**接口契约：**

```
POST   /api/v1/tasks/              # 创建任务（已完成）
POST   /api/v1/tasks/{id}/run      # 触发执行
GET    /api/v1/tasks/{id}          # 查询详情+steps（已完成）
GET    /api/v1/tasks/{id}/steps    # 查询执行步骤列表
WS     /api/v1/ws/tasks/{id}       # 实时日志流
GET    /api/v1/agents/             # 获取已注册 Agent 列表
```

---

### 前端任务

| # | 任务 | 输出 |
|---|------|------|
| F0.1 | 任务列表页 | `views/tasks/index.vue`，表格展示所有任务，支持状态筛选 |
| F0.2 | 创建任务对话框 | 输入 prompt → 调用 POST /tasks |
| F0.3 | 任务详情页 | `views/tasks/detail.vue`，展示 prompt + steps 列表 |
| F0.4 | 执行按钮 | 详情页一键执行，调用 POST /tasks/{id}/run |
| F0.5 | WebSocket 日志面板 | 实时显示 Agent 执行输出 |
| F0.6 | 路由 & 菜单完善 | 侧边栏增加「任务管理」 |

---

### 数据库变更

```sql
-- 已有：tasks, task_steps, users
-- 新增：
CREATE TABLE agents (
    id          INT PRIMARY KEY AUTO_INCREMENT,
    name        VARCHAR(50) UNIQUE NOT NULL,    -- 如 'echo', 'pm', 'backend'
    description VARCHAR(255),
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  DATETIME DEFAULT NOW()
);

ALTER TABLE task_steps ADD COLUMN token_usage  INT DEFAULT 0;
ALTER TABLE task_steps ADD COLUMN cost_usd     DECIMAL(10,6) DEFAULT 0;
ALTER TABLE task_steps ADD COLUMN error_msg    TEXT;
```

---

## Sprint 1：PM + Backend Agent 双 Agent 协作（第 2 周）

### 目标

输入需求 → PM 拆解为子任务 → Backend Agent 生成 FastAPI 代码

---

### 后端任务

| # | 任务 | 输出 |
|---|------|------|
| B1.1 | PM Agent 实现 | `app/agents/pm.py`，调用 LLM 进行需求拆解，输出 JSON 子任务列表 |
| B1.2 | Backend Agent 实现 | `app/agents/backend_dev.py`，根据子任务生成 FastAPI 代码片段 |
| B1.3 | Task DAG 数据结构 | `app/models/task_dag.py`，节点 + 边，存储任务依赖关系 |
| B1.4 | DAG 调度器 | `app/services/dag_scheduler.py`，拓扑排序 → 按依赖顺序执行 |
| B1.5 | LLM 调用封装 | `app/core/llm.py`，统一 Claude/OpenAI 调用，含重试、token 统计 |
| B1.6 | Prompt 模板管理 | `app/prompts/pm.py`, `app/prompts/backend.py` |
| B1.7 | Celery 异步执行 | Task 执行改为 Celery worker，避免阻塞 API |

**新增接口：**

```
GET    /api/v1/tasks/{id}/dag       # 获取 DAG 结构（nodes + edges）
POST   /api/v1/tasks/{id}/dag/run   # 按 DAG 调度执行
GET    /api/v1/tasks/{id}/artifacts # 获取生成产物（代码）
```

**DAG 数据结构：**

```json
{
  "nodes": [
    {"id": "step_1", "agent": "pm", "status": "completed", "label": "需求拆解"},
    {"id": "step_2", "agent": "backend", "status": "running", "label": "生成用户模型"},
    {"id": "step_3", "agent": "backend", "status": "pending", "label": "生成API接口"}
  ],
  "edges": [
    {"source": "step_1", "target": "step_2"},
    {"source": "step_1", "target": "step_3"}
  ]
}
```

---

### 前端任务

| # | 任务 | 输出 |
|---|------|------|
| F1.1 | DAG 可视化组件 | `components/DagView.vue`，基于 VueFlow 渲染执行图 |
| F1.2 | 节点状态样式 | pending=灰, running=蓝动画, completed=绿, failed=红 |
| F1.3 | 任务详情页集成 DAG | 详情页顶部展示 DAG，下方展示选中节点的 input/output |
| F1.4 | 代码产物展示 | `components/CodeViewer.vue`，Monaco Editor 只读展示生成代码 |
| F1.5 | 实时状态更新 | WebSocket 推送 → DAG 节点状态实时刷新 |

**安装依赖：**

```bash
npm install @vue-flow/core @vue-flow/background @vue-flow/controls monaco-editor
```

---

### 数据库变更

```sql
CREATE TABLE task_dag_nodes (
    id          INT PRIMARY KEY AUTO_INCREMENT,
    task_id     INT NOT NULL,
    node_id     VARCHAR(50) NOT NULL,       -- DAG 内节点标识
    agent       VARCHAR(50) NOT NULL,
    label       VARCHAR(255),
    status      ENUM('pending','running','completed','failed') DEFAULT 'pending',
    input       JSON,
    output      JSON,
    depends_on  JSON,                       -- ["node_id_1", "node_id_2"]
    created_at  DATETIME DEFAULT NOW(),
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

CREATE TABLE task_artifacts (
    id          INT PRIMARY KEY AUTO_INCREMENT,
    task_id     INT NOT NULL,
    node_id     VARCHAR(50),
    file_path   VARCHAR(500),
    content     LONGTEXT,
    language    VARCHAR(20),                -- python, vue, sql
    created_at  DATETIME DEFAULT NOW(),
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);
```

---

## Sprint 2：完整研发链（第 3-4 周）

### 目标

PM → Architect → Backend → Frontend → QA → Review 全链路

---

### 后端任务

| # | 任务 | 输出 |
|---|------|------|
| B2.1 | Architect Agent | `app/agents/architect.py`，输出技术选型 + API Schema + DB Schema |
| B2.2 | Frontend Agent | `app/agents/frontend_dev.py`，生成 Vue 组件代码 |
| B2.3 | QA Agent | `app/agents/qa.py`，生成 pytest 测试代码 |
| B2.4 | Review Agent | `app/agents/reviewer.py`，对生成代码进行 Review，输出反馈 |
| B2.5 | Sandbox 执行器 | `app/sandbox/executor.py`，Docker 内运行生成代码 & 测试 |
| B2.6 | Git Patch 生成/应用 | `app/sandbox/git_patch.py`，将产物转为 git diff 格式 |
| B2.7 | 测试报告解析 | `app/services/test_parser.py`，解析 pytest 输出为结构化数据 |

**新增接口：**

```
POST   /api/v1/sandbox/exec         # 在沙箱中执行代码
GET    /api/v1/tasks/{id}/review     # 获取 Review 反馈
GET    /api/v1/tasks/{id}/tests      # 获取测试结果
POST   /api/v1/tasks/{id}/patch      # 应用代码 patch
```

---

### 前端任务

| # | 任务 | 输出 |
|---|------|------|
| F2.1 | DAG 扩展至 6 Agent 类型 | 不同 Agent 节点不同图标/颜色 |
| F2.2 | Review 反馈面板 | `components/ReviewPanel.vue`，展示代码建议 |
| F2.3 | 测试结果面板 | `components/TestReport.vue`，pass/fail 统计 |
| F2.4 | Diff 对比视图 | Monaco Diff Editor 展示 patch |
| F2.5 | 文件树组件 | `components/FileTree.vue`，展示生成项目结构 |
| F2.6 | 全链路进度条 | 顶部展示 PM → Arch → Backend → Frontend → QA → Review 进度 |

---

### 数据库变更

```sql
CREATE TABLE sandbox_runs (
    id           INT PRIMARY KEY AUTO_INCREMENT,
    task_id      INT NOT NULL,
    container_id VARCHAR(100),
    command      TEXT,
    stdout       LONGTEXT,
    stderr       LONGTEXT,
    exit_code    INT,
    duration_ms  INT,
    created_at   DATETIME DEFAULT NOW(),
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

CREATE TABLE review_comments (
    id          INT PRIMARY KEY AUTO_INCREMENT,
    task_id     INT NOT NULL,
    file_path   VARCHAR(500),
    line_number INT,
    severity    ENUM('info','warning','error') DEFAULT 'info',
    message     TEXT,
    suggestion  TEXT,
    created_at  DATETIME DEFAULT NOW(),
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

CREATE TABLE test_results (
    id          INT PRIMARY KEY AUTO_INCREMENT,
    task_id     INT NOT NULL,
    test_name   VARCHAR(255),
    status      ENUM('passed','failed','error','skipped'),
    duration_ms INT,
    error_msg   TEXT,
    created_at  DATETIME DEFAULT NOW(),
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);
```

---

## Sprint 3：错误恢复系统（第 5 周）

### 目标

Agent 执行失败 → 自动分析错误 → Fix Agent 生成修复 → 重试

---

### 后端任务

| # | 任务 | 输出 |
|---|------|------|
| B3.1 | Fix Agent | `app/agents/fixer.py`，分析错误日志 + 生成修复 patch |
| B3.2 | Retry 策略引擎 | `app/services/retry.py`，指数退避 + 最大重试次数 |
| B3.3 | Fallback 模型切换 | 失败时切换模型（如 Sonnet → Opus） |
| B3.4 | 错误分类器 | `app/services/error_classifier.py`，分为可恢复/不可恢复 |
| B3.5 | 恢复闭环调度 | DAG 节点失败 → Fix → Retry → 成功/人工介入 |

**新增接口：**

```
POST   /api/v1/tasks/{id}/retry             # 手动重试失败节点
GET    /api/v1/tasks/{id}/errors            # 错误历史列表
POST   /api/v1/tasks/{id}/nodes/{nid}/fix   # 触发自动修复
```

---

### 前端任务

| # | 任务 | 输出 |
|---|------|------|
| F3.1 | 失败节点交互 | DAG 上 failed 节点可点击查看错误 + 一键重试 |
| F3.2 | 错误详情抽屉 | `components/ErrorDrawer.vue`，展示错误堆栈 + Fix 建议 |
| F3.3 | 修复历史时间线 | 展示 retry 历史：原始 → fix1 → fix2 → 成功 |
| F3.4 | 手动干预入口 | 人工输入修复指令，传给 Fix Agent |

---

### 数据库变更

```sql
CREATE TABLE error_logs (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    task_id         INT NOT NULL,
    node_id         VARCHAR(50),
    error_type      VARCHAR(50),            -- syntax, runtime, timeout, llm_error
    error_message   TEXT,
    is_recoverable  BOOLEAN DEFAULT TRUE,
    created_at      DATETIME DEFAULT NOW(),
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

CREATE TABLE retry_history (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    task_id         INT NOT NULL,
    node_id         VARCHAR(50),
    attempt         INT DEFAULT 1,
    strategy        VARCHAR(50),            -- retry, fix_and_retry, model_switch
    model_used      VARCHAR(50),
    input           JSON,
    output          JSON,
    status          ENUM('success','failed'),
    duration_ms     INT,
    created_at      DATETIME DEFAULT NOW(),
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);
```

---

## Sprint 4：可观测平台（第 6 周）

### 目标

全链路追踪、成本分析、执行回放

---

### 后端任务

| # | 任务 | 输出 |
|---|------|------|
| B4.1 | Token / Cost 统计服务 | `app/services/metrics.py`，按 task/agent/model 汇总 |
| B4.2 | 全链路 Trace | 每个 step 记录 trace_id、span，支持 OpenTelemetry |
| B4.3 | 执行快照 & Replay | 存储每步 input/output 快照，支持回放 |
| B4.4 | 统计 API | 聚合查询各维度指标 |
| B4.5 | SSE 实时推送 | 大 DAG 任务用 SSE 替代 WS 推送节点状态 |

**新增接口：**

```
GET    /api/v1/metrics/overview             # 总览：总任务、总 token、总费用
GET    /api/v1/metrics/agents               # 按 Agent 维度统计
GET    /api/v1/metrics/tasks/{id}/trace     # 单任务全链路追踪
GET    /api/v1/metrics/tasks/{id}/replay    # 获取回放数据
GET    /api/v1/metrics/cost?range=7d        # 费用趋势
```

---

### 前端任务

| # | 任务 | 输出 |
|---|------|------|
| F4.1 | 数据总览 Dashboard | 改造首页，接入真实统计数据 |
| F4.2 | Token/Cost 图表 | `components/CostChart.vue`，ECharts 折线图 |
| F4.3 | Agent 耗时分析 | 各 Agent 平均耗时柱状图 |
| F4.4 | Trace 时间线视图 | `components/TraceTimeline.vue`，甘特图式展示 |
| F4.5 | Replay 播放器 | 按步骤回放 DAG 执行过程，带时间轴控制 |
| F4.6 | 费用告警配置 | 设置单任务/日费用阈值 |

**安装依赖：**

```bash
npm install echarts vue-echarts
```

---

### 数据库变更

```sql
CREATE TABLE agent_metrics (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    task_id         INT NOT NULL,
    node_id         VARCHAR(50),
    agent           VARCHAR(50),
    model           VARCHAR(50),            -- claude-sonnet, claude-opus
    input_tokens    INT DEFAULT 0,
    output_tokens   INT DEFAULT 0,
    total_tokens    INT DEFAULT 0,
    cost_usd        DECIMAL(10,6) DEFAULT 0,
    latency_ms      INT DEFAULT 0,
    created_at      DATETIME DEFAULT NOW(),
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

CREATE TABLE execution_snapshots (
    id          INT PRIMARY KEY AUTO_INCREMENT,
    task_id     INT NOT NULL,
    node_id     VARCHAR(50),
    step_index  INT,
    state       JSON,                       -- DAG 完整状态快照
    timestamp   DATETIME DEFAULT NOW(),
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);
```

---

## Sprint 5：真实部署 & DevOps Agent（第 7 周）

### 目标

生成的应用可一键部署为可访问的 Preview 环境

---

### 后端任务

| # | 任务 | 输出 |
|---|------|------|
| B5.1 | DevOps Agent | `app/agents/devops.py`，生成 Dockerfile + docker-compose |
| B5.2 | Preview 环境管理 | `app/services/preview.py`，启动/停止/销毁容器 |
| B5.3 | Git 自动提交 | `app/services/git_ops.py`，将产物提交到 Git 仓库 |
| B5.4 | 构建状态追踪 | 构建日志 streaming，状态持久化 |
| B5.5 | 一键发布 API | 串联 patch apply → build → deploy |

**新增接口：**

```
POST   /api/v1/deploy/preview              # 启动 Preview 环境
GET    /api/v1/deploy/preview/{id}         # 获取 Preview 状态 & URL
DELETE /api/v1/deploy/preview/{id}         # 销毁 Preview
GET    /api/v1/deploy/preview/{id}/logs    # 构建/运行日志
POST   /api/v1/tasks/{id}/publish          # 一键发布
```

---

### 前端任务

| # | 任务 | 输出 |
|---|------|------|
| F5.1 | 部署面板 | `views/deploy/index.vue`，展示 Preview 列表 |
| F5.2 | 一键部署按钮 | 任务详情页增加「Deploy」操作 |
| F5.3 | 构建日志实时流 | 终端样式展示 docker build 日志 |
| F5.4 | Preview 预览 | iframe 内嵌展示已部署的应用 |
| F5.5 | 环境管理 | 启动/停止/删除 Preview 容器 |

---

### 数据库变更

```sql
CREATE TABLE deployments (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    task_id         INT NOT NULL,
    status          ENUM('building','running','stopped','failed') DEFAULT 'building',
    container_id    VARCHAR(100),
    preview_url     VARCHAR(500),
    port            INT,
    build_log       LONGTEXT,
    created_at      DATETIME DEFAULT NOW(),
    stopped_at      DATETIME,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);
```

---

## 接口版本规范

| 规则 | 说明 |
|------|------|
| 路径前缀 | `/api/v1/` |
| 认证 | Bearer Token（JWT） |
| 分页 | `?skip=0&limit=20` |
| 错误格式 | `{"detail": "message"}` |
| 时间格式 | ISO 8601 (`2026-05-19T10:00:00Z`) |
| WebSocket | `/api/v1/ws/tasks/{id}` |

---

## 前后端协作约定

1. **接口先行**：每个 Sprint 开始前，后端先出 OpenAPI Schema（FastAPI 自动生成 `/docs`）
2. **Mock 并行**：前端根据 Schema 用 Mock 数据开发，不阻塞等待后端
3. **联调窗口**：每个 Sprint 最后 1-2 天进行前后端联调
4. **类型共享**：后端 Pydantic Schema → 前端 TypeScript interface 保持一致
5. **Git 分支**：`feat/sprint-{n}-{module}` 格式，如 `feat/sprint-1-dag-scheduler`

---

## 当前进度

| 模块 | 状态 |
|------|------|
| FastAPI 项目框架 | ✅ 已完成 |
| 用户认证（JWT） | ✅ 已完成 |
| Task CRUD API | ✅ 已完成 |
| Task/TaskStep 模型 | ✅ 已完成 |
| Vue 管理台框架 | ✅ 已完成 |
| 登录页 | ✅ 已完成 |
| Dashboard 页 | ✅ 已完成 |
| 多语言支持 | ✅ 已完成 |
| **下一步 → Sprint 0 剩余** | Agent 注册 + 调度器 + 任务列表页 |
