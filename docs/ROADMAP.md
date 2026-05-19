# 多 Agent 软件研发协作系统（AI Software Factory）迭代文档

## 一、项目目标

打造一个可用于面试展示的企业级多 Agent 协作研发平台，模拟真实软件团队协作流程，实现：

* 需求自动拆解
* 架构设计生成
* 前后端代码生成
* 自动测试
* 自动 Code Review
* 自动修复
* 自动部署
* 可视化执行 DAG
* 任务状态持久化

定位：

> 面向 AI Infra / Agent Engineering / 平台工程岗位的高质量作品集项目

---

# 二、系统架构

## Agent 层

### PM Agent

负责：

* PRD解析
* 用户故事拆解
* Feature Tree生成
* Sprint规划

输出：Task Graph

---

### Architect Agent

负责：

* 技术选型
* 系统设计
* API Schema
* DB Schema

输出：Architecture Spec

---

### Backend Agent

负责：

* FastAPI代码生成
* SQLAlchemy模型生成
* Alembic迁移

输出：Backend Patch

---

### Frontend Agent

负责：

* Vue页面生成
* 状态管理
* API对接

输出：Frontend Patch

---

### QA Agent

负责：

* 单测生成
* 接口测试
* 回归验证

输出：Test Report

---

### Review Agent

负责：

* Code Review
* 安全扫描
* 性能建议

输出：Review Feedback

---

### Fix Agent

负责：

* 修复失败任务
* Retry策略执行

输出：Recovery Patch

---

### DevOps Agent

负责：

* Dockerfile生成
* Compose/K8s部署
* Preview环境启动

输出：Deployment URL

---

# 三、技术栈

## Backend

* FastAPI
* SQLAlchemy
* Alembic
* PostgreSQL
* Redis
* Celery
* LangGraph
* PydanticAI

## Sandbox

* Docker Executor
* Git Patch Apply
* Pytest Runner

## Frontend

* Vue3
* Monaco Editor
* DAG可视化（VueFlow）
* WebSocket日志流

## Infra

* Docker Compose
* Helm（后续）
* Kubernetes（后期）

---

# 四、迭代路线

# Milestone 0：基础框架（1周）

目标：跑通最小闭环

完成：

* FastAPI项目初始化
* Vue管理台
* PostgreSQL模型
* Agent注册机制
* 基础任务调度器

交付：

可创建任务并执行单 Agent

---

# Milestone 1：双 Agent 协作（1周）

完成：

* PM Agent
* Backend Agent
* Task DAG
* 状态机调度

流程：

输入需求 → PM拆解 → Backend生成代码

交付：

能生成 FastAPI CRUD

面试价值：★★★

---

# Milestone 2：完整研发链（2周）

新增：

* Frontend Agent
* QA Agent
* Review Agent
* Patch Apply

交付：

生成完整全栈Demo

面试价值：★★★★

---

# Milestone 3：错误恢复系统（1周）

新增：

* Retry策略
* Fallback模型切换
* 自动修复闭环

流程：

失败 → 分析 → 修复 → 重试

面试价值：★★★★★

---

# Milestone 4：可观测平台（1周）

新增：

* DAG实时流
* Token统计
* Cost统计
* Agent耗时分析
* Replay执行

面试价值：★★★★★

---

# Milestone 5：真实部署（1周）

新增：

* Docker Preview
* Git自动提交
* 一键发布

交付：

真实可访问生成应用

面试价值：★★★★★

---

# 五、数据库设计

## tasks

* id
* prompt
* status
* current_agent
* created_at

## task_steps

* task_id
* agent
* input
* output
* duration
* status

## agent_runs

* token_usage
* cost
* retry_count

## patches

* diff
* apply_status

---

# 六、面试包装话术

## 项目介绍

设计并实现了一套企业级多智能体协作研发平台，通过状态机编排多个专业 Agent，实现需求拆解、代码生成、自动测试、错误恢复和部署预览闭环。

---

## 技术亮点

### 多 Agent DAG 编排

支持并行调度与依赖控制

### Sandbox隔离执行

Docker安全运行生成代码

### 自动错误恢复

失败分析 + Patch修复

### 可观测Agent Runtime

全链路追踪与Replay

### Tool Calling Framework

统一工具协议

---

# 七、第一版必须完成（建议本周）

只做：

* PM Agent
* Backend Agent
* Task Graph
* FastAPI生成
* Vue DAG页面
* PostgreSQL持久化

做到：

输入：

“做一个博客系统”

输出：

* 任务拆解
* DAG展示
* FastAPI代码生成
* 存储执行记录

即可开始写进简历。
