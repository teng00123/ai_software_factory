# AI Software Factory - 多Agent软件研发协作系统

基于FastAPI的多Agent协作研发平台，实现需求自动拆解、代码生成、测试和部署的全流程自动化。

## 功能特性

- 🚀 多Agent协作：PM、架构、前后端、QA、Review、Fix、DevOps七大Agent
- 📊 可视化DAG：实时任务执行流程图
- 🔄 自动错误恢复：智能重试和修复机制
- 🐳 容器化部署：Docker + Docker Compose
- 🗄️ 数据持久化：PostgreSQL数据库

## 技术栈

### 后端
- FastAPI
- SQLAlchemy + AsyncPG
- PostgreSQL
- Pydantic

### 前端 (后续开发)
- Vue 3
- TypeScript
- VueFlow (DAG可视化)

## 快速开始

### 环境要求
- Python 3.11+
- Docker & Docker Compose
- PostgreSQL (可通过Docker启动)

### 使用Docker Compose (推荐)

1. 启动所有服务：
```bash
docker-compose up -d
```

2. 访问API文档：
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### 本地开发

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 启动PostgreSQL数据库：
```bash
docker-compose up -d postgres
```

3. 启动应用：
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API接口

### 任务管理
- `GET /api/v1/tasks` - 获取任务列表
- `POST /api/v1/tasks` - 创建新任务
- `GET /api/v1/tasks/{id}` - 获取任务详情
- `PATCH /api/v1/tasks/{id}` - 更新任务状态
- `DELETE /api/v1/tasks/{id}` - 删除任务

### 数据结构

#### 任务 (Task)
```json
{
  "id": 1,
  "prompt": "创建一个博客系统",
  "status": "pending",
  "current_agent": "pm",
  "created_at": "2023-12-01T10:00:00",
  "updated_at": "2023-12-01T10:00:00"
}
```

#### 任务步骤 (TaskStep)
```json
{
  "id": 1,
  "task_id": 1,
  "agent": "pm",
  "input": "创建一个博客系统",
  "output": "需求拆解完成...",
  "status": "completed",
  "duration": 1500,
  "created_at": "2023-12-01T10:00:00",
  "updated_at": "2023-12-01T10:00:00"
}
```

## 项目结构

```
ai_software_factory/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   └── tasks.py
│   │       └── api.py
│   ├── core/
│   │   └── config.py
│   ├── db/
│   │   └── session.py
│   ├── models/
│   │   ├── task.py
│   │   └── task_step.py
│   └── schemas/
│       └── task.py
├── main.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env
```

## 开发计划

### Milestone 0: 基础框架 (当前)
- ✅ FastAPI项目初始化
- ✅ PostgreSQL模型定义
- ✅ 基础任务API
- 🔄 Vue管理台
- 🔄 Agent注册机制

### Milestone 1: 双Agent协作
- PM Agent + Backend Agent
- Task DAG可视化
- 状态机调度

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

MIT License