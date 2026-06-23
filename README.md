# CodeSage

> 集成 LightRAG 知识图谱的 AI 对话与生成式交互平台

CodeSage 是一个基于 FastAPI + Vue 3 构建的智能对话应用，不仅支持常规文本对话，还内置**生成式 UI**能力——AI 回复不再是纯文本，而是动态渲染为卡片、流程图、代码块、表格等富组件。同时深度集成 LightRAG，提供知识图谱检索增强生成（RAG），支持多轮对话上下文、流式输出和多种检索模式。

## 核心功能

### 对话与生成式 UI
- **双模式对话**：文本对话 + 生成式页面（AI 回复动态渲染为结构化组件）
- **流式输出**：SSE 实时流式响应，生成式页面支持边生成边显示
- **多轮对话**：会话历史管理，切换会话自动加载历史记录
- **生成式组件库**：8 种内置组件（摘要卡片、文本块、流程图、列表、代码块、引用、表格、未知兜底），支持节点版本管理与版本切换
- **函数调用**：内置沙箱化的函数调用系统，支持 AI 主动触发再生、扩展等操作

### 知识库（LightRAG）
- **5 种检索模式**：naive（朴素向量）、local（局部实体）、global（全局图谱）、hybrid（混合）、mix（知识图谱+向量）
- **知识图谱**：自动抽取实体与关系，构建知识图谱辅助检索
- **多轮对话上下文**：`conversation_history` 传入 LightRAG，提升追问场景的检索质量
- **文档管理**：上传 MD/TXT 文档，实时查看处理状态（解析→抽取→分块→索引）
- **按用户隔离**：每个用户独立的知识库工作空间（PG_WORKSPACE）

### 用户系统
- **JWT 认证**：双 Token（访问+刷新），Redis 黑名单管理
- **登录安全**：失败次数限制 + 自动锁定，拼图验证码
- **邮箱验证**：可选的邮箱验证流程
- **头像上传**：MinIO 预签名 URL 直传，浏览器→MinIO 无需经后端中转
- **多模型供应商**：每个用户可配置多个 AI 供应商，前端切换

### 管理后台
- **数据库管理**：可视化查看/编辑所有数据表（Django-admin 风格）
- **模型供应商管理**：直接在数据库管理页配置 AI 供应商

## 技术栈

| 层 | 技术 |
|---|---|
| **后端** | FastAPI, SQLAlchemy (async), asyncpg, Pydantic v2 |
| **前端** | Vue 3, TypeScript, Vite, Element Plus, Tailwind CSS |
| **数据库** | PostgreSQL (pgvector), Redis |
| **对象存储** | MinIO (S3 兼容) |
| **AI/RAG** | LightRAG, OpenAI 兼容接口（默认阿里百炼） |
| **部署** | Docker, Docker Compose |

## 项目结构

```
CodeSage/
├── backend/
│   ├── api/v1/endpoints/     # API 端点
│   │   ├── auth.py            #   认证/注册/头像
│   │   ├── chat.py            #   对话流式接口（文本+生成式）
│   │   ├── conversations.py   #   会话与消息管理
│   │   ├── knowledge.py       #   知识库查询/状态
│   │   ├── nodes.py           #   生成式 UI 节点
│   │   ├── providers.py       #   AI 模型供应商
│   │   ├── functions.py       #   函数调用
│   │   ├── database_admin.py  #   数据库管理后台
│   │   └── admin/             #   管理员接口
│   ├── core/                  # 配置、安全、依赖注入
│   ├── db/                    # 数据库会话
│   ├── minio/                 # MinIO/S3 存储模块（独立）
│   │   ├── client.py          #   S3 客户端工厂
│   │   └── storage.py         #   头像上传/预签名 URL
│   ├── models/                # SQLAlchemy 模型
│   ├── schemas/               # Pydantic 模型
│   ├── services/              # 业务逻辑层
│   │   ├── auth_service.py    #   认证/用户资料
│   │   ├── conversation_service.py  # 会话/消息
│   │   ├── node_service.py    #   生成式节点
│   │   └── component_service.py    # 组件协议生成
│   ├── rag/                   # LightRAG 集成
│   │   ├── service.py         #   LightRAG 初始化/查询
│   │   └── endpoints.py       #   知识库上传/文档管理
│   ├── function_calling/      # 函数调用沙箱
│   ├── sys_prompts/           # 系统提示词
│   │   ├── chat_system.md     #   对话系统提示
│   │   ├── component_protocol.md  # 生成式组件协议
│   │   └── title_generator.md #   标题生成提示
│   └── init_db.py             # 数据库初始化与迁移
├── frontend/src/
│   ├── views/                 # 页面视图
│   │   ├── ChatView.vue       #   对话主界面（文本+生成式切换）
│   │   ├── LoginView.vue      #   登录
│   │   ├── RegisterView.vue   #   注册
│   │   ├── SettingsView.vue   #   设置（资料/模型/知识库）
│   │   └── VerifyEmailView.vue#   邮箱验证
│   ├── features/
│   │   ├── generative-ui/     # 生成式 UI 模块
│   │   │   ├── components/    #   8 种渲染组件
│   │   │   ├── GenerativePanel.vue  # 生成式面板
│   │   │   ├── useGenerativeUi.ts   # 生成式逻辑 composable
│   │   │   ├── componentRegistry.ts # 组件注册表
│   │   │   └── api.ts         #   生成式 API
│   │   └── database-admin/    # 数据库管理前端
│   ├── composables/           # Vue composables
│   ├── stores/                # Pinia 状态管理
│   ├── api/                   # Axios API 封装
│   └── types/                 # TypeScript 类型
├── docker-compose.yml         # 一键部署
├── .env                       # 环境变量配置
└── scripts/setup_centos.sh    # CentOS 服务器初始化脚本
```

## 快速开始

### Docker 部署（推荐）

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env，至少配置 DASHSCOPE_API_KEY 或其他模型 API Key

# 2. 一键启动所有服务
docker-compose up -d --build

# 3. 访问
# 前端：http://localhost
# 后端 API 文档：http://localhost:8000/docs
```

首次启动后：
1. 访问 `http://localhost` 注册账号
2. 登录后进入「设置 → 模型供应商」配置 AI 模型
3. 开始对话或在「设置 → 知识库」上传文档

### 本地开发

**后端**：
```bash
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload
```

**前端**：
```bash
cd frontend
npm install
npm run dev
```

> 本地开发时需本地运行 PostgreSQL、Redis、MinIO，或修改 `.env` 指向 Docker 容器。

## 服务端口

| 服务 | 端口 | 地址 |
|------|------|------|
| 前端 | 80 | http://localhost |
| 后端 API | 8000 | http://localhost:8000 |
| API 文档 | 8000 | http://localhost:8000/docs |
| PostgreSQL | 5432 | localhost:5432 |
| Redis | 6379 | localhost:6379 |
| MinIO API | 9000 | http://localhost:9000 |
| MinIO 控制台 | 9001 | http://localhost:9001 |

## 配置说明

所有配置通过 `.env` 文件管理。核心配置项：

### AI 模型配置

模型配置已迁移至数据库（`ai_providers` 表），通过前端「设置 → 模型供应商」页面管理。每个用户可配置多个供应商并启用其一。

默认使用阿里云百炼 OpenAI 兼容接口：

```bash
DASHSCOPE_API_KEY=你的百炼APIKey
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus
EMBEDDING_MODEL=text-embedding-v4
EMBEDDING_DIM=1024
```

**切换其他模型**（通过 LiteLLM Proxy 统一管理）：
```bash
pip install -r backend/requirements.txt
litellm --config backend/litellm_config.example.yaml --port 4000
# 然后将 LLM_BASE_URL 改为 http://localhost:4000/v1
```

### MinIO 对象存储

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `S3_ENABLED` | 启用 MinIO 存储 | `true` |
| `S3_ENDPOINT_URL` | MinIO API 端点（后端访问） | `http://localhost:9000` |
| `S3_PUBLIC_BASE_URL` | MinIO 公开地址（浏览器访问） | `http://localhost:9000` |
| `S3_ACCESS_KEY_ID` | MinIO 用户名 | `codesage_minio` |
| `S3_SECRET_ACCESS_KEY` | MinIO 密码 | `codesage_minio_change_me_32_chars` |
| `S3_BUCKET_AVATARS` | 头像存储桶名 | `codesage-avatars` |

> Docker 部署时 `S3_ENDPOINT_URL` 应改为 `http://minio:9000`（容器内通信）。
> **生产环境务必修改默认密码**，且 `.env` 和 `docker-compose.yml` 中的 `MINIO_ROOT_USER`/`MINIO_ROOT_PASSWORD` 必须保持一致。

MinIO 控制台：http://localhost:9001，使用 `.env` 中的用户名密码登录。

### LightRAG 知识库

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `LIGHTRAG_ENABLED` | 启用知识库 | `true` |
| `LIGHTRAG_WORKING_DIR` | 索引/缓存目录 | `data/lightrag` |
| `POSTGRES_HOST` | LightRAG PG 后端地址 | `localhost` |
| `POSTGRES_WORKSPACE` | 用户工作空间前缀 | `codesage_rag` |

> Docker 部署时 `POSTGRES_HOST` 会被 docker-compose 覆盖为 `db`。

### 认证与安全

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `JWT_SECRET` | JWT 签名密钥 | `dev-secret-...`（生产必改） |
| `ACCESS_TOKEN_EXPIRE_DAYS` | 访问令牌有效期 | 7 天 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 刷新令牌有效期 | 30 天 |
| `LOGIN_MAX_FAIL_ATTEMPTS` | 最大登录失败次数 | 5 |
| `LOGIN_LOCK_MINUTES` | 锁定时长 | 15 分钟 |
| `SKIP_EMAIL_VERIFICATION` | 跳过邮箱验证（开发模式） | `true` |

## 生成式 UI 组件库

组件位于 `frontend/src/features/generative-ui/components/`：

| 组件 | 文件 | 说明 |
|------|------|------|
| 摘要卡片 | `SummaryCard.vue` | 带标题的内容摘要 |
| 文本块 | `TextBlock.vue` | 普通段落文本 |
| 流程图 | `Flowchart.vue` | 节点+边的流程可视化 |
| 列表 | `ListBlock.vue` | 有序/无序列表 |
| 代码块 | `CodeBlock.vue` | 语法高亮代码 |
| 引用 | `QuoteBlock.vue` | 引用/提示框 |
| 表格 | `TableBlock.vue` | 结构化表格 |
| 未知兜底 | `UnknownBlock.vue` | 未知组件类型的降级渲染 |

组件注册表：`frontend/src/features/generative-ui/componentRegistry.ts`

AI 生成的组件协议格式：
```json
{
  "page_type": "explain",
  "title": "标题",
  "components": [
    { "type": "summary_card", "props": { "title": "...", "content": "..." }, "id": "sum_1" }
  ],
  "actions": [],
  "meta": { "source": "CodeSage 知识库", "version": 1 }
}
```

## API 速览

### 对话
```bash
# 文本对话（流式）
curl -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"message":"你好","use_rag":false}'

# 生成式对话（流式，带 RAG）
curl -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"message":"解释一下Docker","use_rag":true,"mode":"mix","render_mode":"component"}'
```

### 知识库
```bash
# 上传文档
curl -X POST http://localhost:8000/api/v1/rag/upload-file \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"filename":"notes.md","content":"文档内容...","source":"学习笔记"}'

# 查询知识库
curl -X POST http://localhost:8000/api/v1/rag/query \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"question":"什么是Docker？","mode":"hybrid"}'

# 查看文档列表
curl http://localhost:8000/api/v1/rag/documents \
  -H "Authorization: Bearer <token>"
```

## 服务器部署（CentOS 7.9）

```bash
# 1. 初始化服务器环境（安装 Docker + 开放端口）
chmod +x scripts/setup_centos.sh
./scripts/setup_centos.sh

# 2. 部署应用
docker-compose up -d --build
```

脚本自动完成：系统更新、Docker 引擎安装、Docker Compose V2 安装、防火墙端口开放（80/8000/5432）。

## 开发指南

### 数据库迁移

`backend/init_db.py` 在应用启动时自动执行，使用 `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` 实现幂等迁移。新增字段只需在模型中添加，然后在 `init_db.py` 补充对应的 ALTER 语句。

### 新增生成式组件

1. 在 `frontend/src/features/generative-ui/components/` 创建 `MyComponent.vue`
2. 在 `componentRegistry.ts` 注册组件映射
3. 在 `backend/schemas/component.py` 添加组件类型定义
4. 在 `backend/sys_prompts/component_protocol.md` 更新 AI 提示词

### 新增函数调用

1. 在 `backend/function_calling/tools/` 创建工具函数
2. 在 `registry.py` 注册
3. AI 会根据组件协议中的 `actions` 自动调用

## License

MIT
