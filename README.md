# CodeSage

> 集成 LightRAG 知识图谱的 AI 对话与生成式交互平台

CodeSage 是一个基于 FastAPI + Vue 3 构建的智能对话应用，不仅支持常规文本对话，还内置**生成式 UI**能力——AI 回复不再是纯文本，而是动态渲染为卡片、流程图、代码块、表格等富组件。同时深度集成 LightRAG，提供知识图谱检索增强生成（RAG），支持多轮对话上下文、流式输出和多种检索模式。

## 核心功能

### 对话与生成式 UI

- **双模式对话**：文本对话 + 生成式页面（AI 回复动态渲染为结构化组件）
- **流式输出**：SSE 实时流式响应，生成式页面支持边生成边显示
- **多轮对话**：会话历史管理，切换会话自动加载历史记录
- **`render_mode` 字段**：`chat_messages` 表新增 `render_mode` 列（`text`/`component`），区分文本消息与生成式组件消息
- **生成式组件库**：9 种内置组件（摘要卡片、文本块、流程图、列表、代码块、引用、表格、网页入口卡片、未知兜底）
- **节点版本管理**：UiNode / UiNodeVersion 模型，支持生成、重生成、展开、版本切换、版本回溯
- **AI 预生成交互网页**（特色功能）：
  - AI 一次性生成 1~3 个完整的 HTML 子页面（含内联 CSS / JS 交互逻辑）
  - 通过 `open_webpage` action 持久化存储在 `ComponentProtocol.actions` 中
  - 用户点击「查看详情」按钮 → 全屏 iframe 沙箱（`sandbox="allow-scripts allow-same-origin"`）打开预生成页面
  - 页面支持 Tab 切换、数据筛选、展开折叠等真实交互，**无需等待 AI 实时生成**
  - 刷新网站内容不丢失（数据持久化在 `ui_node_version.content_json` 中）
- **函数调用**：内置沙箱化的函数调用系统，支持 AI 主动触发再生、扩展等操作

### 知识库（LightRAG）

- **5 种检索模式**：naive（朴素向量）、local（局部实体）、global（全局图谱）、hybrid（混合）、mix（知识图谱+向量）
- **知识图谱**：自动抽取实体与关系，构建知识图谱辅助检索
- **多轮对话上下文**：`conversation_history` 传入 LightRAG，提升追问场景的检索质量
- **文档管理**：上传 MD/TXT 文档，实时查看处理状态（解析→抽取→分块→索引）
- **按用户隔离**：每个用户独立的知识库工作空间（PG_WORKSPACE）
- **查询超时优化**：mix/hybrid 图谱推理较慢，超时 60s

### 用户系统

- **JWT 认证**：双 Token（访问+刷新），Redis 黑名单管理
- **登录安全**：失败次数限制 + 自动锁定，拼图验证码
- **邮箱验证**：可选的邮箱验证流程
- **头像上传**：MinIO 预签名 URL 直传，浏览器 → MinIO 无需经后端中转；前端使用 `el-avatar` 组件统一展示
- **多模型供应商**：每个用户可配置多个 AI 供应商，前端切换；API Key 加密存储

### 管理后台

- **数据库管理**：可视化查看/编辑所有数据表（Django-admin 风格）
- **模型供应商管理**：直接在数据库管理页配置 AI 供应商
- **审计日志**：关键操作记录

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
│   ├── api/v1/endpoints/         # API 端点
│   │   ├── auth.py                #   认证/注册/头像
│   │   ├── chat.py                #   对话流式接口（文本+生成式）
│   │   ├── conversations.py       #   会话与消息管理
│   │   ├── knowledge.py           #   知识库查询/状态网关
│   │   ├── nodes.py               #   生成式 UI 节点（重生成/展开/版本切换）
│   │   ├── providers.py           #   AI 模型供应商
│   │   ├── functions.py           #   函数调用
│   │   ├── database_admin.py      #   数据库管理后台
│   │   └── admin/                 #   管理员接口
│   ├── core/                      # 配置、安全、依赖注入
│   ├── db/                        # 数据库会话
│   ├── minio/                     # MinIO/S3 存储模块（独立）
│   │   ├── client.py              #   S3 客户端工厂
│   │   └── storage.py             #   头像上传/预签名 URL
│   ├── models/                    # SQLAlchemy 模型
│   │   ├── conversation.py        #   含 render_mode 字段
│   │   ├── ui_node.py             #   生成式节点版本化
│   │   ├── audit.py               #   审计日志
│   │   └── provider.py            #   AI 供应商
│   ├── schemas/                   # Pydantic 模型
│   │   ├── component.py           #   组件协议
│   │   ├── node.py                #   节点 schema
│   │   └── function_calling.py    #   函数调用 schema
│   ├── services/                  # 业务逻辑层
│   │   ├── auth_service.py        #   认证/用户资料
│   │   ├── conversation_service.py#   会话/消息
│   │   ├── node_service.py        #   生成式节点（重生成/展开/版本）
│   │   ├── component_service.py   #   组件协议生成（流式+非流式）
│   │   ├── memory_service.py      #   记忆管理
│   │   ├── database_admin_service.py # 数据库管理
│   │   └── provider_service.py    #   AI 供应商配置
│   ├── rag/                       # LightRAG 集成
│   │   ├── service.py             #   LightRAG 初始化/查询（5种模式）
│   │   ├── endpoints.py           #   知识库上传/文档管理
│   │   └── parser.py              #   文件解析器
│   ├── function_calling/          # 函数调用沙箱
│   │   ├── registry.py            #   工具注册表
│   │   ├── sandbox.py             #   沙箱执行
│   │   ├── validator.py           #   参数校验
│   │   └── tools/                 #   具体工具实现
│   ├── sys_prompts/               # 系统提示词（全部 .md）
│   │   ├── chat_system.md         #   对话系统提示
│   │   ├── component_protocol.md  #   生成式组件协议（含 open_webpage 指南）
│   │   └── title_generator.md     #   标题生成提示
│   └── init_db.py                 # 数据库初始化与迁移
├── frontend/src/
│   ├── views/                     # 页面视图
│   │   ├── ChatView.vue           #   对话主界面（文本+生成式切换）
│   │   ├── LoginView.vue          #   登录
│   │   ├── RegisterView.vue       #   注册
│   │   ├── SettingsView.vue       #   设置（资料/模型/知识库）
│   │   └── VerifyEmailView.vue    #   邮箱验证
│   ├── features/
│   │   ├── generative-ui/         # 生成式 UI 模块
│   │   │   ├── components/        #   9 种渲染组件
│   │   │   │   └── WebPageBlock.vue #  可点击入口卡片→全屏 HTML 子页面
│   │   │   ├── GenerativePanel.vue  # 生成式面板
│   │   │   ├── ComponentRenderer.vue#  组件渲染器（含全屏 iframe 沙箱）
│   │   │   ├── NodeDetailView.vue   # 节点详情视图
│   │   │   ├── useGenerativeUi.ts   # 生成式逻辑 composable
│   │   │   ├── componentRegistry.ts # 组件注册表
│   │   │   ├── api.ts               # 生成式 API
│   │   │   └── types.ts             # 类型定义（含 open_webpage action）
│   │   └── database-admin/        # 数据库管理前端
│   ├── composables/               # Vue composables
│   ├── stores/                    # Pinia 状态管理
│   ├── api/                       # Axios API 封装
│   └── types/                     # TypeScript 类型
├── docker-compose.yml             # 一键部署
├── .env                           # 环境变量配置
└── scripts/setup_centos.sh        # CentOS 服务器初始化脚本
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

模型配置已迁移至数据库（`ai_providers` 表），通过前端「设置 → 模型供应商」页面管理。每个用户可配置多个供应商并启用其一。API Key 使用 Fernet 加密存储。

默认使用阿里云百炼 OpenAI 兼容接口：

```bash
DASHSCOPE_API_KEY=你的百炼APIKey
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus
EMBEDDING_MODEL=text-embedding-v4
EMBEDDING_DIM=1024
```

> ⚠️ 注意：阿里百炼的 `qwen3.7-max` 模型不存在，请使用 `qwen-plus` 或 `qwen-max`。

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
> **生产环境务必修改默认密码**，且 `.env` 的 `S3_ACCESS_KEY_ID`/`S3_SECRET_ACCESS_KEY` 必须与 `docker-compose.yml` 中的 `MINIO_ROOT_USER`/`MINIO_ROOT_PASSWORD` 保持一致。
> 修改密码需同步两边配置 + 重启 minio 容器 + 清 `docker_data/minio/` 旧数据。

MinIO 控制台：http://localhost:9001，使用 `.env` 中的用户名密码登录。

头像上传流程：
1. 前端调 `POST /api/v1/auth/me/avatar/upload` 获取 MinIO 预签名上传 URL
2. 浏览器直接 `PUT` 上传文件到 MinIO（不经后端中转）
3. 调 `POST /api/v1/auth/me/avatar/commit` 保存引用
4. 前端展示用 `el-avatar` 组件，URL 加时间戳破缓存

### LightRAG 知识库

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `LIGHTRAG_ENABLED` | 启用知识库 | `true` |
| `LIGHTRAG_WORKING_DIR` | 索引/缓存目录 | `data/lightrag` |
| `POSTGRES_HOST` | LightRAG PG 后端地址 | `localhost` |
| `POSTGRES_WORKSPACE` | 用户工作空间前缀 | `codesage_rag` |

> Docker 部署时 `POSTGRES_HOST` 会被 docker-compose 覆盖为 `db`。
> LightRAG 按用户缓存多实例（workspace 隔离），混合存储（PG + pgvector + NetworkX）。

### 认证与安全

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `JWT_SECRET` | JWT 签名密钥 | `dev-secret-...`（生产必改） |
| `ACCESS_TOKEN_EXPIRE_DAYS` | 访问令牌有效期 | 7 天 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 刷新令牌有效期 | 30 天 |
| `LOGIN_MAX_FAIL_ATTEMPTS` | 最大登录失败次数 | 5 |
| `LOGIN_LOCK_MINUTES` | 锁定时长 | 15 分钟 |
| `SKIP_EMAIL_VERIFICATION` | 跳过邮箱验证（开发模式） | `true` |
| `FIELD_ENCRYPTION_KEY` | 字段加密密钥（Fernet） | 空（重启丢失历史数据） |

## 生成式 UI 组件库

组件位于 `frontend/src/features/generative-ui/components/`：

| 组件 | 文件 | type 字段 | 说明 |
|------|------|-----------|------|
| 摘要卡片 | `SummaryCard.vue` | `summary_card` | 带标题的内容摘要 |
| 文本块 | `TextBlock.vue` | `text_block` | 普通段落文本 |
| 流程图 | `Flowchart.vue` | `flowchart` | 节点+边的流程可视化 |
| 列表 | `ListBlock.vue` | `list` | 有序/无序列表 |
| 代码块 | `CodeBlock.vue` | `code` | 语法高亮代码 |
| 引用 | `QuoteBlock.vue` | `quote` | 引用/提示框 |
| 表格 | `TableBlock.vue` | `table` | 结构化表格 |
| 网页入口卡片 | `WebPageBlock.vue` | `webpage` | **可点击卡片→全屏 HTML 子页面** |
| 未知兜底 | `UnknownBlock.vue` | — | 未知组件类型的降级渲染 |

组件注册表：`frontend/src/features/generative-ui/componentRegistry.ts`

AI 生成的组件协议格式（ComponentProtocol）：
```json
{
  "page_type": "analysis",
  "title": "页面标题",
  "components": [
    { "id": "sum_1", "type": "summary_card", "props": { "title": "...", "content": "..." } },
    { "id": "wp_1", "type": "webpage", "props": { "title": "详情页", "description": "...", "html_content": "<!DOCTYPE html>..." } }
  ],
  "actions": [
    { "type": "regenerate", "target_id": "sum_1" },
    { "type": "expand", "target_id": "sum_1" },
    { "type": "function_call", "function_name": "knowledge_query", "params": {} },
    { "type": "open_webpage", "params": { "title": "子页面", "html_content": "<!DOCTYPE html>..." } }
  ],
  "meta": { "source": "CodeSage", "version": 1 }
}
```

### action 类型白名单

| type | 说明 | 必填字段 |
|------|------|----------|
| `regenerate` | 重新生成某组件 | `target_id` |
| `expand` | 展开某组件更多内容 | `target_id` |
| `function_call` | 调用后端函数 | `function_name`，可选 `params`/`target_id` |
| `open_webpage` | 打开预生成的全屏 HTML 子页面 | `params.title` + `params.html_content` |

## 持久化机制

- **会话消息**：`chat_sessions` + `chat_messages`（含 `render_mode` 区分文本/组件）
- **生成式节点**：`ui_node`（节点树）+ `ui_node_version`（版本快照，content_json 存 ComponentProtocol）+ `ui_node_relation`（节点关系图）
- **AI 供应商配置**：`ai_providers`（API Key Fernet 加密）
- **对象存储**：MinIO（头像等文件）
- **缓存/限流**：Redis（JWT 黑名单 / 刷新令牌 / 登录限流）

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

### 生成式节点

```bash
# 重生成节点
curl -X POST http://localhost:8000/api/v1/nodes/{node_id}/regenerate \
  -H "Authorization: Bearer <token>"

# 展开节点
curl -X POST http://localhost:8000/api/v1/nodes/{node_id}/expand \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"message":"请详细展开"}'

# 切换版本
curl -X POST http://localhost:8000/api/v1/nodes/{node_id}/versions/{version_id}/activate \
  -H "Authorization: Bearer <token>"

# 按会话查询节点
curl http://localhost:8000/api/v1/nodes/by-session/{session_id} \
  -H "Authorization: Bearer <token>"
```

### 知识库

```bash
# 上传文档
curl -X POST http://localhost:8000/api/v1/rag/upload-file \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"filename":"notes.md","content":"文档内容...","source":"学习笔记"}'

# 查询知识库（mix 模式：知识图谱+向量）
curl -X POST http://localhost:8000/api/v1/rag/query \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"question":"什么是Docker？","mode":"hybrid"}'

# 查看文档列表
curl http://localhost:8000/api/v1/rag/documents \
  -H "Authorization: Bearer <token>"
```

> ⚠️ 知识库上传是大任务接口，前端已设 180s 超时；后端 `_wait_for_latest_doc_status` 超时 120s。

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

1. 在 `frontend/src/features/generative-ui/components/` 创建 `MyComponent.vue`，接收 `props` 属性
2. 在 `componentRegistry.ts` 导入并注册组件映射
3. 在 `backend/schemas/component.py` 添加组件类型定义
4. 在 `backend/sys_prompts/component_protocol.md` 更新组件白名单与 props 说明
5. 重建 backend 镜像（让新 prompt 生效）

### 新增函数调用工具

1. 在 `backend/function_calling/tools/` 创建工具函数
2. 在 `registry.py` 注册
3. AI 会根据组件协议中的 `actions` 自动调用

### 提示词管理

- 所有 AI system prompt 必须存放在 `backend/sys_prompts/*.md`
- 禁止在 Python 代码中硬编码 prompt 字符串
- 通过 `from backend.sys_prompts import XXX_PROMPT` 引入使用

## 知识库存储结构

CodeSage 的知识库存储**完全委托给 LightRAG 库管理**。CodeSage 自身没有定义"文档表"或"分块表"的 ORM 模型，只保留了 `ai_providers` 配置表作为知识库运行的配置源。

### LightRAG 自动创建的 11 张 PG 表

这些表由 LightRAG 的 `PGVectorStorage` / `PGKVStorage` / `PGDocStatusStorage` 后端自动建表和管理：

| 表名 | 存储后端 | 用途 |
|------|----------|------|
| `lightrag_vdb_chunks` | PGVectorStorage | **最重要**：文档分块的向量存储（`content_vector` 为 pgvector HNSW 索引） |
| `lightrag_vdb_entity` | PGVectorStorage | 实体的向量表示 |
| `lightrag_vdb_relation` | PGVectorStorage | 关系的向量表示 |
| `lightrag_doc_chunks` | PGKVStorage | 文档分块元数据（关联 `doc_id`、`chunk_order_index`） |
| `lightrag_doc_full` | PGKVStorage | 完整文档原文 |
| `lightrag_doc_status` | PGDocStatusStorage | 文档处理生命周期（`pending`/`success`/`failed`） |
| `lightrag_full_entities` | PGKVStorage | 完整实体数据（结构化 JSON） |
| `lightrag_full_relations` | PGKVStorage | 完整关系数据 |
| `lightrag_entity_chunks` | PGKVStorage | 实体-分块关联表 |
| `lightrag_relation_chunks` | PGKVStorage | 关系-分块关联表 |
| `lightrag_llm_cache` | PGKVStorage | LLM 调用缓存（避免重复调用） |

### 知识图谱文件存储

| 存储位置 | 格式 | 用途 |
|---------|------|------|
| `docker_data/lightrag/user_{uid}/graph_chunk_entity_relation.graphml` | GraphML XML | 知识图谱（实体-关系图，NetworkX 持久化） |

**图谱节点属性**：`entity_id` / `entity_type` / `description` / `source_id` / `file_path` / `created_at`
**图谱边属性**：`weight` / `description` / `keywords` / `source_id`

### 相关 PG 扩展

```sql
CREATE EXTENSION IF NOT EXISTS vector;    -- pgvector 向量索引
CREATE EXTENSION IF NOT EXISTS pgcrypto;  -- gen_random_uuid()
```

Docker 使用镜像：`pgvector/pgvector:pg15`（预装 pgvector 的 PostgreSQL 15）

### 数据流

```
用户上传文件 → backend/rag/endpoints.py (API)
  → backend/rag/parser.py (文本提取)
  → backend/rag/service.py (LightRAGService，按用户缓存多实例)
    → LightRAG.ainsert()
      ├── 分块 → lightrag_doc_chunks
      ├── 向量化 → lightrag_vdb_chunks (pgvector HNSW)
      ├── 实体抽取 → lightrag_vdb_entity + lightrag_full_entities
      ├── 关系抽取 → lightrag_vdb_relation + lightrag_full_relations
      └── 图谱构建 → .graphml 文件
```

> **注意**：当前版本知识库文档的原始文件**没有**通过 MinIO 持久化，仅上传时全文提取后存入 LightRAG 的 PG 表中。MinIO 目前仅用于头像存储。

## 常见问题排查

| 现象 | 根因 | 修复 |
|------|------|------|
| 知识库上传 499 | 前端 30s 超时 < 后端 60s+ 处理 | 前端 rag.ts 设 180s 超时 |
| 头像上传失败 | `.env` 缺 S3 配置 | 补全 `S3_ENABLED=true` 等配置 |
| AI 重生成 500 | 模型名不存在（如 `qwen3.7-max`） | `UPDATE ai_providers SET llm_model='qwen-plus'` |
| 生成式历史丢失 | 未调 `loadSessionHistory` | GenerativePanel 切换会话时加载 UiNode |
| 生成式面板不滚动 | flex 子项滚动需 `min-h-0`，父级避免 `overflow-hidden` | flex 子项 `overflow-y-auto` 同时加 `min-h-0` |
| 左侧用户信息不刷新 | 原生 `<img>` 缓存 | 改用 `el-avatar` + URL 加时间戳 |

## License

MIT
