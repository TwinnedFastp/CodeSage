# Tasks

- [x] Task 1: 初始化项目结构
  - [x] SubTask 1.1: 创建 `backend` 目录，设计模块化结构 (app, api, core, models, schemas, db)。
  - [x] SubTask 1.2: 创建 `frontend` 目录，使用 Vite + Vue 3 + TypeScript 初始化。
  - [x] SubTask 1.3: 配置项目根目录的 `.gitignore` 和基础说明。

- [x] Task 2: 后端模块化开发 (FastAPI + PostgreSQL)
  - [x] SubTask 2.1: 安装依赖并配置异步数据库连接 (SQLAlchemy + asyncpg)。
  - [x] SubTask 2.2: 实现模块化目录结构，并为关键代码编写详细的中文注释。
  - [x] SubTask 2.3: 实现 `/api/v1/chatstreaming` 接口，支持 StreamingResponse。
  - [x] SubTask 2.4: 实现基础的数据库模型和迁移配置。

- [x] Task 3: 前端开发 (Vite + Vue 3 + Element Plus + Tailwind)
  - [x] SubTask 3.1: 配置 Element Plus 和 Tailwind CSS。
  - [x] SubTask 3.2: 使用 `frontend-design` 技能实现响应式聊天界面（包含侧边栏折叠逻辑）。
  - [x] SubTask 3.3: 实现流式消息接收逻辑（处理 SSE/ReadableStream）。

- [x] Task 4: 基础设施与 GitHub 配置
  - [x] SubTask 4.1: 编写 `docker-compose.yml`，集成 backend, frontend, postgres。
  - [x] SubTask 4.2: 创建 `.github/workflows` 并配置 GitHub Environment 示例。
  - [x] SubTask 4.3: 编写 README.md，详细说明如何一键启动以及如何上传到 GitHub。

- [x] Task 5: CentOS 7.9 部署适配
  - [x] SubTask 5.1: 编写针对 CentOS 7.9 的环境初始化脚本 (安装 Docker, Docker Compose)。
  - [x] SubTask 5.2: 配置 CentOS 防火墙 (firewalld) 开放 80, 8000, 5432 端口。
  - [x] SubTask 5.3: 更新 README.md，增加 CentOS 7.9 生产环境部署手册。

# Task Dependencies
- [Task 2] 依赖 [Task 1]
- [Task 3] 依赖 [Task 1] 和 [Task 2]
- [Task 4] 依赖 [Task 1], [Task 2], [Task 3]
