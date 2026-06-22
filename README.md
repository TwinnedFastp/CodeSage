# ChatGPT Clone

这是一个使用 FastAPI 和 Vite (Vue 3 + Element Plus) 构建的类似 ChatGPT 的网页端应用。

## 技术栈

- **后端**: FastAPI, SQLAlchemy, PostgreSQL, asyncpg
- **前端**: Vite, Vue 3, TypeScript, Element Plus, Tailwind CSS
- **部署**: Docker, Docker Compose

## 项目结构

- `backend/`: FastAPI 后端代码。
- `frontend/`: Vue 3 前端代码。
- `docker_data/`: Docker 运行时数据卷（PostgreSQL 初始化脚本、Redis 配置、MinIO 数据）。
- `docker-compose.yml`: 一键启动配置。

## 服务端口一览

| 服务 | 端口 | 访问地址 |
|------|------|----------|
| 前端页面 | 80 | `http://localhost` |
| 后端 API | 8000 | `http://localhost:8000` |
| PostgreSQL | 5432 | `localhost:5432` |
| Redis | 6379 | `localhost:6379` |
| MinIO API (S3) | 9000 | `http://localhost:9000` |
| MinIO 控制台 | 9001 | `http://localhost:9001` |

## 如何运行

### 使用 Docker (推荐)

```bash
docker-compose up -d --build
```

## MinIO 对象存储

项目使用 MinIO 存储用户头像等文件资源（S3 兼容协议）。

### MinIO 控制台

打开浏览器访问 `http://localhost:9001`：

- **用户名**: `codesage_minio`（由 `MINIO_ROOT_USER` 环境变量控制）
- **密码**: `codesage_minio_change_me_32_chars`（由 `MINIO_ROOT_PASSWORD` 环境变量控制，**生产环境务必修改**）

### 头像上传流程

1. 浏览器调用 `POST /api/v1/auth/me/avatar/upload` 获取 MinIO 预签名上传 URL
2. 浏览器通过 `PUT` 请求直接将图片上传到 MinIO
3. 上传成功后调用 `POST /api/v1/auth/me/avatar/commit` 保存头像引用

### 相关配置（docker-compose.yml backend 环境变量）

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `S3_ENABLED` | 启用 MinIO | `true` |
| `S3_ENDPOINT_URL` | MinIO API 端点（Docker 内部） | `http://minio:9000` |
| `S3_PUBLIC_BASE_URL` | MinIO API 公开地址（浏览器） | `http://localhost:9000` |
| `S3_ACCESS_KEY_ID` | MinIO 用户名 | `codesage_minio` |
| `S3_SECRET_ACCESS_KEY` | MinIO 密码 | 与 `MINIO_ROOT_PASSWORD` 一致 |
| `S3_BUCKET_AVATARS` | 头像存储桶 | `codesage-avatars` |

### 本地开发

#### 后端

```bash
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

## LightRAG + 阿里百炼

本项目已把 LightRAG 嵌入到后端，默认使用阿里云百炼 OpenAI 兼容接口。

### 1. 配置模型

复制 `.env.example` 为 `.env`，然后至少填写一个 API Key：

```bash
DASHSCOPE_API_KEY=你的百炼APIKey
```

默认配置如下：

```bash
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus
EMBEDDING_MODEL=text-embedding-v4
EMBEDDING_DIM=1024
```

### 2. 写入知识库

```bash
curl -X POST http://localhost:8000/api/v1/rag/documents \
  -H "Content-Type: application/json" \
  -d "{\"source\":\"学习笔记\",\"text\":\"CodeSage 是一个集成 LightRAG 的 AI 学习项目。\"}"
```

### 3. 查询知识库

```bash
curl -X POST http://localhost:8000/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"CodeSage 是什么？\",\"mode\":\"hybrid\"}"
```

聊天流式接口也支持 LightRAG：

```bash
curl -X POST http://localhost:8000/api/v1/chat/chatstreaming \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"CodeSage 是什么？\",\"use_rag\":true,\"mode\":\"hybrid\"}"
```

### 4. 使用 LiteLLM 统一管理更多模型

如果你想“一键配置各种大模型”，可以使用已加入依赖的 LiteLLM Proxy。

```bash
pip install -r backend/requirements.txt
litellm --config backend/litellm_config.example.yaml --port 4000
```

然后把 `.env` 改成：

```bash
LLM_BASE_URL=http://localhost:4000/v1
LLM_API_KEY=sk-anything
LLM_MODEL=qwen-plus
```

之后要切换模型，只需要把 `LLM_MODEL` 改成 `deepseek-chat`、`gpt-4o-mini` 等在 `backend/litellm_config.example.yaml` 里配置过的名字。

#### 前端

```bash
cd frontend
npm install
npm run dev
```

## 部署到服务器 (CentOS 7.9)

如果您使用的是 CentOS 7.9 服务器，可以使用我们提供的初始化脚本快速搭建环境：

### 1. 初始化环境

```bash
# 下载并运行脚本
chmod +x scripts/setup_centos.sh
./scripts/setup_centos.sh
```

该脚本会自动完成：
- 更新系统软件。
- 安装 Docker 引擎。
- 安装 Docker Compose (V2)。
- 开放防火墙端口 (80, 8000, 5432)。

### 2. 部署应用

```bash
# 进入项目目录
docker-compose up -d --build
```

## GitHub 上传指南

1. 在 GitHub 上创建一个新的仓库。
2. 在本地执行以下命令：

```bash
git init
git add .
git commit -m "Initial commit: ChatGPT clone project structure"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

3. 在 GitHub 仓库设置中配置 `Settings -> Environments`，分别创建 `dev` 和 `prod` 环境，并添加必要的 Secrets (如 `DATABASE_URL`, `OPENAI_API_KEY` 等)。
