# ChatGPT 克隆应用规格说明 (Spec)

## Why
用户希望使用 FastAPI 和 Vite (Vue 3 + Element Plus) 构建一个类似 ChatGPT 的网页端应用，支持流式对话、响应式设计（适配电脑和手机），并提供一键启动的 Docker 环境（包含 PostgreSQL）。

## What Changes
- **后端 (FastAPI)**: 
  - 模块化设计。
  - 实现 `/chatstreaming` 流式响应接口。
  - 集成 PostgreSQL 数据库。
  - 为新手提供详尽注释。
- **前端 (Vite + Vue 3)**:
  - 使用 Element Plus 组件库。
  - 使用 Tailwind CSS 进行辅助布局和响应式设计。
  - 实现类似 ChatGPT 的聊天交互和侧边栏。
- **部署 (CentOS 7.9)**: 
  - 适配 CentOS 7.9 的环境搭建指南。
  - Docker 与 Docker Compose 的安装配置。
  - 安全配置（Firewalld 端口开放）。
- **GitHub**:
  - 配置 `dev` 和 `prod` 环境。

## Impact
- **Affected code**:
  - `backend/`: FastAPI 源码，模块化结构。
  - `frontend/`: Vite + Vue 源码。
  - `docker-compose.yml`: 环境编排。
  - `.github/`: GitHub 环境与 Actions 配置。

## ADDED Requirements
### Requirement: 流式对话
系统应支持流式获取 AI 回复。
#### Scenario: 流式输出
- **WHEN** 用户发送消息。
- **THEN** 后端通过 Server-Sent Events (SSE) 或 StreamingResponse 逐字返回结果，前端实时渲染。

### Requirement: 响应式 UI (Element Plus + Tailwind)
使用 Element Plus 组件实现专业 UI，Tailwind 实现灵活布局。
#### Scenario: 自动适配
- **WHEN** 窗口大小改变。
- **THEN** 侧边栏在手机端自动折叠，通过抽屉 (Drawer) 或汉堡菜单访问。

### Requirement: 数据库集成 (PostgreSQL)
存储聊天记录和用户信息。

### Requirement: Docker 一键启动
提供 `docker-compose.yml`。

## MODIFIED Requirements
- 前端框架明确为 **Vue 3 + Element Plus**。
- 后端接口明确为 **流式接口 (`/chatstreaming`)**。
- 增加 **PostgreSQL** 数据库支持。

## REMOVED Requirements
无。
