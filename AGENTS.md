# CodeSage 项目开发规范 (AGENTS.md)

> **AI 编程助手入口文件（各平台自动识别）：**
> - Claude (Anthropic) → [.claude/CLAUDE.md](.claude/CLAUDE.md)
> - Cursor → [.cursorrules](.cursorrules)
> - GitHub Copilot → [.github/copilot-instructions.md](.github/copilot-instructions.md)
> - OpenAI Codex → [.codex/instructions.md](.codex/instructions.md)
> - WorkBuddy → 本文件
>
> 本文档是**完整权威版本**，修改代码前必须先阅读，确保符合项目约定。

---

## 一、项目概述

| 项 | 值 |
|---|---|
| **项目名** | CodeSage |
| **定位** | 类 ChatGPT 的 AI 对话系统，集成 LightRAG 知识库检索增强生成 + 生成式 UI |
| **仓库根目录** | `e:\pythoncode\CodeSage` |
| **语言环境** | 中文（注释、文档、变量命名均使用中文或英文通用术语） |

### 技术栈总览

```
┌─────────────────────────────────────────────────────┐
│                    前端 (端口 80)                     │
│   Vue 3.5 + TypeScript + Vite 8 + Element Plus 2    │
│   Tailwind CSS 4 + Pinia 3 + Vue Router 4            │
│   Axios + vue3-puzzle-vcode (拼图验证)               │
│   部署: Nginx 静态托管                               │
├──────────────┬──────────────────────────────────────┤
│ 后端(8000)   │ 基础设施                              │
│ FastAPI      │ PostgreSQL 15 (pgvector + age)        │
│ SQLAlchemy   │ Redis 7 (Alpine)                      │
│ Pydantic     │ MinIO (S3 兼容)                       │
│ asyncpg      │ Docker Compose                        │
│ LightRAG 1.5 │                                       │
└──────────────┴──────────────────────────────────────┘
```

### 核心特性

- **双模式对话**：文本对话 + 生成式页面（AI 回复动态渲染为组件）
- **AI 预生成交互网页**：AI 一次性生成 1~3 个完整 HTML 子页面（含 CSS/JS），通过 `open_webpage` action 持久化，点击全屏打开
- **5 种 RAG 检索模式**：naive / local / global / hybrid / mix
- **节点版本管理**：UiNode / UiNodeVersion，支持重生成、展开、版本切换

---

## 二、目录结构规范

```
CodeSage/
├── backend/                          # Python FastAPI 后端
│   ├── main.py                       # 应用入口：FastAPI 实例、CORS、异常处理、路由注册
│   ├── init_db.py                    # 数据库初始化脚本（幂等迁移：ALTER TABLE ADD COLUMN IF NOT EXISTS）
│   ├── requirements.txt              # Python 依赖
│   ├── Dockerfile                    # 后端容器构建
│   │
│   ├── api/v1/                       # API 路由层（只做 HTTP 协议转换，不含业务逻辑）
│   │   ├── api.py                    # 路由聚合器：include_router 汇总所有端点
│   │   ├── deps.py                   # 依赖注入：get_current_user / get_db 等
│   │   └── endpoints/                # 各业务端点文件（每个文件对应一个领域）
│   │       ├── auth.py               # 认证: 注册 / 登录 / 登出 / 邮箱验证 / 刷新令牌 / 头像上传
│   │       ├── chat.py               # 聊天: 流式对话（文本+生成式，含 render_mode 区分）
│   │       ├── conversations.py      # 会话管理: CRUD 会话 / 消息 / 偏好 / 事实记忆 / 任务
│   │       ├── providers.py          # AI 模型供应商管理
│   │       ├── nodes.py              # 生成式 UI 节点: 重生成 / 展开 / 版本切换 / 按会话查询
│   │       ├── functions.py          # 函数调用端点
│   │       ├── knowledge.py          # 知识库网关（聚合 rag/endpoints）
│   │       ├── database_admin.py     # 数据库管理后台
│   │       └── admin/                # 管理员接口
│   │
│   ├── rag/                          # RAG 知识库模块（独立目录，不散落在 services/ 中）
│   │   ├── __init__.py               # 导出 lightrag_service 单例
│   │   ├── service.py                # LightRAG 封装: insert / query（5种模式）/ list / delete
│   │   ├── schemas.py                # RAG 请求/响应 Pydantic 模型
│   │   ├── endpoints.py              # RAG REST API: status / documents / upload-file / query
│   │   └── parser.py                 # 文件解析器: MD/TXT 文本清理
│   │
│   ├── minio/                        # MinIO/S3 对象存储模块（独立，从 auth_service 抽离）
│   │   ├── __init__.py               # 导出 storage 单例
│   │   ├── client.py                 # S3 客户端工厂（boto3 session）
│   │   └── storage.py                # 头像上传 / 预签名 URL 生成
│   │
│   ├── function_calling/             # 函数调用沙箱系统
│   │   ├── __init__.py               # 导出 registry
│   │   ├── registry.py               # 工具注册表（装饰器注册）
│   │   ├── sandbox.py                # 沙箱执行环境
│   │   ├── validator.py              # 参数校验
│   │   ├── exceptions.py             # 函数调用异常
│   │   ├── schemas.py                # 函数调用 Pydantic 模型
│   │   └── tools/                    # 具体工具实现
│   │       ├── code_executor.py      #   代码执行工具
│   │       └── knowledge_query.py    #   知识库查询工具
│   │
│   ├── sys_prompts/                  # AI 提示词集中管理（全部 .md 文件）
│   │   ├── __init__.py               # 统一导出为字符串常量
│   │   ├── chat_system.md            # CodeSage 主系统提示词
│   │   ├── component_protocol.md     # 生成式组件协议（含组件白名单 + open_webpage 指南）
│   │   └── title_generator.md        # 标题生成器提示词
│   │
│   ├── services/                     # 业务逻辑层（纯函数/类，无 HTTP 概念）
│   │   ├── auth_service.py           # 认证: 密码哈希 / JWT 签发 / 邮箱发送 / 头像
│   │   ├── conversation_service.py   # 会话: CRUD / 标题生成 / 记忆管理
│   │   ├── node_service.py           # 生成式节点: 创建根节点 / 重生成 / 展开 / 版本切换
│   │   ├── component_service.py      # 组件协议生成: generate_component_protocol（非流式）+ stream_component_protocol_raw（流式）
│   │   ├── memory_service.py         # 记忆管理: 事实记忆 / 偏好 / 任务
│   │   ├── database_admin_service.py # 数据库管理后台业务逻辑
│   │   ├── email_service.py          # SMTP 邮件发送
│   │   └── provider_service.py       # AI 供应商配置的增删改查（含 API Key 加密）
│   │
│   ├── models/                       # SQLAlchemy ORM 模型（数据库表映射）
│   │   ├── base.py                   # Base 声明式基类
│   │   ├── user.py                   # users 表
│   │   ├── conversation.py           # chat_sessions / chat_messages（含 render_mode 字段）/ user_facts / user_preferences / user_tasks 表
│   │   ├── ui_node.py                # ui_node / ui_node_version / ui_node_relation 表（生成式节点版本化）
│   │   ├── provider.py               # ai_providers 表（API Key Fernet 加密）
│   │   └── audit.py                  # 审计日志表
│   │
│   ├── schemas/                      # Pydantic 请求/响应模型（API 数据校验）
│   │   ├── auth.py                   # 注册/登录/令牌请求体
│   │   ├── conversation.py           # 会话/消息/偏好/事实/任务 schema
│   │   ├── component.py              # 组件协议 ComponentProtocol schema
│   │   ├── node.py                   # 生成式节点 schema
│   │   ├── function_calling.py       # 函数调用 schema
│   │   ├── knowledge.py              # 知识库 schema
│   │   ├── user.py                   # 用户 schema
│   │   ├── provider.py               # 供应商配置 schema
│   │   └── database_admin.py         # 数据库管理 schema
│   │
│   ├── core/                         # 核心基础设施
│   │   ├── config.py                 # 全局配置 Settings 类（pydantic-settings，从 .env 读取）
│   │   ├── security.py               # JWT 工具函数 / 密码哈希
│   │   └── redis_client.py           # Redis 连接池单例
│   │
│   ├── db/                           # 数据库会话
│   │   └── session.py                # async SessionLocal / get_db 依赖
│   │
│   ├── utils/                        # 通用工具函数
│   │   └── crypto.py                 # Fernet 字段级加密/解密
│   │
│   └── tests/                        # 测试
│       ├── conftest.py               # pytest fixtures
│       ├── test_auth.py              # 认证测试
│       ├── test_conversations.py     # 会话测试
│       └── test_stress.py            # 压力测试
│
├── frontend/                         # Vue 3 前端
│   ├── src/
│   │   ├── main.ts                   # 应用入口: createApp / 挂载 ElementPlus / Pinia / Router
│   │   ├── App.vue                   # 根组件
│   │   ├── style.css                 # 全局样式 + 自定义滚动条
│   │   │
│   │   ├── api/                      # API 请求封装层（axios 实例 + 各模块接口定义）
│   │   │   ├── request.ts            # axios 实例: baseURL / 拦截器 / token 注入
│   │   │   ├── auth.ts               # 认证 API（含头像上传/提交）
│   │   │   ├── conversations.ts      # 会话 API
│   │   │   ├── providers.ts          # 供应商 API
│   │   │   └── rag.ts                # 知识库 API（180s 超时）
│   │   │
│   │   ├── features/                 # 功能模块（按领域组织）
│   │   │   ├── generative-ui/        # 生成式 UI 模块
│   │   │   │   ├── GenerativePanel.vue   # 生成式面板（容器）
│   │   │   │   ├── ComponentRenderer.vue # 组件渲染器（含全屏 iframe 沙箱查看器）
│   │   │   │   ├── NodeDetailView.vue    # 节点详情视图
│   │   │   │   ├── useGenerativeUi.ts    # 生成式逻辑 composable（流式/重生成/展开/版本）
│   │   │   │   ├── componentRegistry.ts  # 组件注册表
│   │   │   │   ├── api.ts                # 生成式 API
│   │   │   │   ├── types.ts              # 类型定义（含 open_webpage action）
│   │   │   │   └── components/           # 9 种渲染组件
│   │   │   │       ├── SummaryCard.vue   #   摘要卡片
│   │   │   │       ├── TextBlock.vue     #   文本块
│   │   │   │       ├── Flowchart.vue     #   流程图
│   │   │   │       ├── ListBlock.vue     #   列表
│   │   │   │       ├── CodeBlock.vue     #   代码块
│   │   │   │       ├── QuoteBlock.vue    #   引用
│   │   │   │       ├── TableBlock.vue    #   表格
│   │   │   │       ├── WebPageBlock.vue  #   网页入口卡片（点击全屏打开）
│   │   │   │       └── UnknownBlock.vue  #   未知兜底
│   │   │   └── database-admin/       # 数据库管理前端
│   │   │
│   │   ├── composables/              # Vue 组合式函数（业务状态与操作）
│   │   │   ├── useChat.ts            # 聊天逻辑: 发送消息 / SSE 流式接收 / RAG 模式 / render_mode 切换
│   │   │   ├── useLoginForm.ts       # 登录表单: 校验 / 提交 / 拼图验证联动
│   │   │   ├── useRegisterForm.ts    # 注册表单
│   │   │   ├── useRag.ts             # 知识库: 状态检查 / 上传文本 / 上传文件 / 列表 / 删除
│   │   │   ├── useSessions.ts        # 会话列表管理
│   │   │   ├── useProviders.ts       # AI 供应商管理
│   │   │   └── useResponsive.ts      # 响应式布局检测
│   │   │
│   │   ├── components/               # 可复用组件
│   │   │   ├── KnowledgePanel.vue    # 知识库抽屉面板（上传区 + 文档列表）
│   │   │   └── PuzzleVerify.vue      # 拼图滑块验证组件
│   │   │
│   │   ├── views/                    # 页面级组件（路由对应）
│   │   │   ├── LoginView.vue         # 登录页
│   │   │   ├── RegisterView.vue      # 注册页
│   │   │   ├── VerifyEmailView.vue   # 邮箱验证页
│   │   │   ├── ChatView.vue          # 主聊天页面（文本+生成式切换，核心页面）
│   │   │   └── SettingsView.vue      # 设置页（资料/模型/知识库，头像用 el-avatar）
│   │   │
│   │   ├── stores/                   # Pinia 状态管理
│   │   │   └── auth.ts               # 用户认证状态（token / 用户信息 / 持久化）
│   │   │
│   │   ├── router/                   # 路由配置
│   │   │   └── index.ts              # 路由表 + 导航守卫（未登录跳转登录页）
│   │   │
│   │   ├── types/                    # TypeScript 类型声明
│   │   │   ├── index.ts              # 全局类型
│   │   │   └── shims-*.d.ts          # 第三方库类型补丁
│   │   │
│   │   └── assets/                   # 静态资源
│   │
│   ├── package.json                  # 前端依赖
│   ├── vite.config.ts                # Vite 配置
│   ├── tsconfig.json                 # TypeScript 配置（严格模式）
│   ├── tailwind.config.js            # Tailwind 配置
│   └── index.html                    # HTML 入口
│
├── docker-compose.yml                # Docker 编排: db / redis / minio / backend / frontend
├── docker_data/                      # 运行时数据持久化
│   ├── postgres/init/01-extensions.sql  # PG 扩展初始化: vector / pgcrypto / age
│   ├── redis/redis.conf              # Redis 配置
│   └── lightrag/                     # LightRAG 本地缓存数据
│
├── .env                              # 环境变量（不入 Git）
├── .env.example                      # 环境变量模板
├── README.md                         # 项目说明文档
└── AGENTS.md                         # 本文件（AI 助手开发规范）
```

---

## 三、编码规范

### 3.1 命名约定

| 层级 | 语言 | 规范 | 示例 |
|------|------|------|------|
| **Python 文件** | Python | `snake_case` | `auth_service.py`, `node_service.py` |
| **Python 类** | Python | `PascalCase` | `LightRAGService`, `UiNode`, `UserCreate` |
| **Python 函数/变量** | Python | `snake_case` | `insert_text()`, `lightrag_api_key` |
| **Python 常量** | Python | `UPPER_SNAKE_CASE` | `CHAT_SYSTEM_PROMPT`, `LIGHTRAG_ENABLED` |
| **TypeScript 文件** | TS | `camelCase` | `useChat.ts`, `useRag.ts` |
| **TS/Vue 组件** | TS | `PascalCase` | `KnowledgePanel.vue`, `ChatView.vue`, `WebPageBlock.vue` |
| **TS 函数/变量** | TS | `camelCase` | `uploadDocument()`, `ragMode` |
| **TS 常量** | TS | `UPPER_SNAKE_CASE` 或 `camelCase` | 视上下文而定 |
| **目录名** | - | `snake_case` | `sys_prompts/`, `endpoints/` |
| **API 路由路径** | - | `kebab-case` | `/rag/upload-file`, `/auth/register` |

### 3.2 分层职责（严格遵循）

```
请求流向:
  前端 composables → api/*.ts → [HTTP] → endpoints/*.py → services/*.py → models/ + db/

禁止事项:
  ❌ endpoints 里写复杂业务逻辑 → 移入 services
  ❌ services 里直接操作 HTTP request/response → 只返回纯 Python 对象
  ❌ 前端 views 直接调用 axios → 必须经过 composables + api 层
  ❌ 在多个地方重复同一份逻辑 → 抽到 composable / service
  ❌ 在 Python 代码中硬编码 prompt 字符串 → 放入 sys_prompts/*.md
```

### 3.3 RAG 模块特殊规则

- **所有 RAG 相关代码必须在 `backend/rag/` 目录内**，不允许散落到 `services/`、`schemas/`、`endpoints/`
- **分片/向量化/图谱构建全部交给 LightRAG 原生 `ainsert()`**，不自研重复逻辑
- **文件传输方式**: 前端 FileReader 读文本 → POST JSON 到 `/rag/upload-file`（不用 FormData/multipart）
- **LightRAG 采用懒加载单例模式**: 首次调用 insert/query 时才初始化
- **按用户隔离**: 每个用户独立工作空间（PG_WORKSPACE 前缀）
- **5 种查询模式**: naive / local / global / hybrid / mix（mix = 知识图谱+向量，最慢）
- **查询超时**: mix/hybrid 图谱推理慢，超时 60s
- **多轮对话**: `conversation_history` 传给 LightRAG 提升检索准确率

### 3.3.1 知识库数据库存储结构（LightRAG 管理，非 CodeSage ORM）

> CodeSage **自身没有定义知识库文档/分块的 ORM 模型**。以下 11 张表全部由 LightRAG 库自动创建和管理。CodeSage 仅保留 `ai_providers` 表作为配置源。

| 表名 | 存储后端 | 关键字段 | 用途 |
|------|----------|---------|------|
| **`lightrag_vdb_chunks`** | PGVectorStorage | `content`, `content_vector` (vector), `workspace` | **核心表**：分块文本 + pgvector HNSW 索引 |
| `lightrag_vdb_entity` | PGVectorStorage | `entity_name`, `content_vector`, `workspace` | 实体向量存储 |
| `lightrag_vdb_relation` | PGVectorStorage | `content_vector`, `workspace` | 关系向量存储 |
| `lightrag_doc_chunks` | PGKVStorage | `id`, `doc_id`, `content`, `chunk_order_index`, `workspace` | 文档分块元数据 |
| `lightrag_doc_full` | PGKVStorage | `id`, `content`, `workspace` | 完整文档原文 |
| `lightrag_doc_status` | PGDocStatusStorage | `id`, `status` (pending/success/failed), `content_summary`, `content_length`, `workspace` | 文档处理生命周期 |
| `lightrag_full_entities` | PGKVStorage | 结构化 JSON | 完整实体数据 |
| `lightrag_full_relations` | PGKVStorage | 结构化 JSON | 完整关系数据 |
| `lightrag_entity_chunks` | PGKVStorage | `entity_id` ↔ `chunk_id` | 实体-分块关联 |
| `lightrag_relation_chunks` | PGKVStorage | `relation_id` ↔ `chunk_id` | 关系-分块关联 |
| `lightrag_llm_cache` | PGKVStorage | Key-Value | LLM 调用去重缓存 |

**知识图谱文件**：`docker_data/lightrag/user_{uid}/graph_chunk_entity_relation.graphml`（NetworkX GraphML）

**PG 扩展依赖**：`pgvector/pgvector:pg15` 镜像，`CREATE EXTENSION vector;`

**数据流**：`用户上传 → parser.py 文本提取 → service.py → LightRAG.ainsert() → 分块+向量化+实体抽取+图谱构建 → 11张PG表 + .graphml`

> 原始文件**未**通过 MinIO 持久化（MinIO 仅用于头像），文本提取后存入 LightRAG 的 PG 表。

### 3.4 MinIO 模块特殊规则

- **所有 S3/MinIO 相关代码必须在 `backend/minio/` 目录内**，从 `auth_service` 抽离
- **头像上传流程**: 前端获取预签名 URL → 浏览器直接 PUT 到 MinIO → 调 commit 保存引用
- **配置位置**: `.env` 的 `S3_ACCESS_KEY_ID`/`S3_SECRET_ACCESS_KEY` 必须与 `docker-compose.yml` 的 `MINIO_ROOT_USER`/`MINIO_ROOT_PASSWORD` 一致
- **改密码**: 同步两边 + 重启 minio 容器 + 清 `docker_data/minio/` 旧数据

### 3.5 生成式 UI 模块特殊规则

- **组件目录**: `frontend/src/features/generative-ui/components/`，每个组件接收 `props` 属性
- **注册表**: 新增组件必须在 `componentRegistry.ts` 登记，否则前端无法识别
- **后端协议**: `backend/schemas/component.py` 定义 ComponentProtocol，`backend/sys_prompts/component_protocol.md` 指导 AI 生成
- **节点版本**: 生成/重生成/展开都写入新的 `ui_node_version`，支持回溯
- **render_mode**: `chat_messages.render_mode` 区分 `text`/`component`，前端 `useChat` 过滤 component 消息
- **open_webpage action**: HTML 子页面通过 `iframe srcdoc` + sandbox 隔离渲染，内容持久化在 `ui_node_version.content_json.actions[].params.html_content`
- **WebPageBlock 组件**: 可点击入口卡片，emit `open` 事件触发全屏查看器

### 3.6 提示词管理规则

- **所有 AI system prompt 必须存放在 `backend/sys_prompts/*.md`**
- **禁止在 Python 代码中硬编码 prompt 字符串**
- 动态部分（如 `{knowledge}` 变量注入）由代码在运行时拼接
- 通过 `from backend.sys_prompts import XXX_PROMPT` 引入使用
- **修改 prompt 后必须重建 backend 镜像**（除非挂载了 volume）

### 3.7 前端 UI 规范

- **UI 框架**: Element Plus 2.x（全局注册）
- **CSS 方案**: Tailwind CSS 4.x（原子类优先），Element Plus 内置样式作为补充
- **设计风格**: 杂志风（Magazine Style）
  - 主色调: `#111111`（近黑）/ 辅色 `#FAFAFA`（暖白灰）/ 边框 `#E8E6E1`
  - 字体: 标题用 `font-serif`（衬线），正文用系统默认无衬线
  - 圆角: 大元素 `rounded-2xl` / 按钮 `rounded-full` / 卡片 `rounded-xl`
- **自定义滚动条**: 全局 `.custom-scrollbar` 样式（细窄、透明）
- **图标**: 使用 `@element-plus/icons-vue`，不引入额外图标库
- **头像组件**: 统一使用 `el-avatar`，URL 加时间戳破缓存
- **flex 滚动**: flex 子项 `overflow-y-auto` 必须同时加 `min-h-0`（否则无法收缩触发滚动），且父级避免 `overflow-hidden` 覆盖

---

## 四、API 设计规范

### 4.1 URL 结构

```
基础路径: /api/v1
认证前缀: 所有需要登录的接口使用 Depends(get_current_user)

路由分组:
  /api/v1/auth/*              ← auth.py            (无需认证)
  /api/v1/chat/*              ← chat.py            (需认证)
  /api/v1/conversations/*     ← conversations.py   (需认证)
  /api/v1/providers/*         ← providers.py       (需认证)
  /api/v1/rag/*               ← rag/endpoints.py   (需认证)
  /api/v1/nodes/*             ← nodes.py           (需认证，生成式交互节点)
  /api/v1/knowledge/*         ← knowledge.py       (需认证，知识库网关)
  /api/v1/functions/*         ← functions.py       (需认证，Function Calling)
  /api/v1/database-admin/*    ← database_admin.py  (需认证，数据库管理)
```

### 4.2 响应格式

```python
# 成功 — 直接返回 Pydantic 模型（FastAPI 自动序列化为 JSON）
return RagWriteOut(success=True, message="写入成功")

# 错误 — 统一使用 HTTPException
raise HTTPException(status_code=401, detail="未登录")
raise HTTPException(status_code=503, detail="LightRAG 未启用")

# 流式响应 — 使用 StreamingResponse + Server-Sent Events
StreamingResponse(generate_stream(), media_type="text/event-stream")
```

### 4.3 错误映射（生成式节点专用）

`backend/api/v1/endpoints/nodes.py` 的 `_map_gen_error` 函数将 OpenAI 异常映射为 HTTP 错误：

| 异常 | HTTP 状态码 | 说明 |
|------|-------------|------|
| `APIConnectionError` | 502 | 模型服务不可达 |
| `AuthenticationError` | 401 | API Key 无效 |
| `APIStatusError` | 502 | 模型返回错误（含模型名提示） |
| `RuntimeError` | 400 | 运行时错误 |
| `ValueError` | 404 | 资源不存在 |

### 4.4 前端 API 封装模式

```typescript
// api/xxx.ts — 统一使用 request 实例（已含 baseURL + token 拦截器）
import { request } from './request'

export function someAction(payload: SomeIn): Promise<SomeOut> {
  return request.post<SomeOut>('/some/path', payload).then(r => r.data)
}
```

**长任务接口超时**：知识库上传等大任务接口单独设 180s 超时（默认 30s 不够）。

---

## 五、配置管理规范

### 5.1 配置来源优先级

1. **`.env` 文件**（开发默认值）
2. **环境变量**（Docker / 生产覆盖）
3. **数据库 `ai_providers` 表**（用户运行时配置，仅限 LLM 相关）

### 5.2 关键配置项

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `POSTGRES_SERVER` | DB 地址（Docker 内用服务名 `db`） | `localhost` |
| `REDIS_URL` | Redis 连接串 | `redis://localhost:6379/0` |
| `JWT_SECRET` | JWT 签名密钥（生产必改！） | `please-change-this-secret-in-production` |
| `LIGHTRAG_ENABLED` | 是否启用知识库功能 | `true` |
| `SKIP_EMAIL_VERIFICATION` | 开发模式跳过邮箱验证 | `false` |
| `S3_ENABLED` | 是否启用 MinIO 对象存储（头像等） | `true` |
| `S3_ENDPOINT_URL` | MinIO API 端点（Docker 内部使用） | `http://minio:9000` |
| `S3_PUBLIC_BASE_URL` | MinIO API 公开地址（浏览器使用） | `http://localhost:9000` |
| `S3_ACCESS_KEY_ID` | MinIO 用户名（须与 MINIO_ROOT_USER 一致） | `codesage_minio` |
| `S3_SECRET_ACCESS_KEY` | MinIO 密码（须与 MINIO_ROOT_PASSWORD 一致） | `codesage_minio_change_me_32_chars` |
| `S3_BUCKET_AVATARS` | 头像存储桶名 | `codesage-avatars` |
| `FIELD_ENCRYPTION_KEY` | Fernet 字段加密密钥（空则临时生成，重启丢数据） | 空 |

> **LLM 相关配置（API Key / Model / Embedding）不在 .env 中管理**，而是通过前端「设置 → 模型供应商」页面写入 `ai_providers` 数据库表。API Key 用 Fernet 加密存储。
> ⚠️ 阿里百炼的 `qwen3.7-max` 模型不存在，请使用 `qwen-plus` 或 `qwen-max`。

### 5.3 MinIO 对象存储

项目使用 MinIO（S3 兼容）存储用户头像等文件资源：

| 端口 | 用途 | 访问地址 |
|------|------|----------|
| 9000 | S3 API | `http://localhost:9000` |
| 9001 | Web 控制台 | `http://localhost:9001` |

**MinIO 控制台登录**：打开浏览器访问 `http://localhost:9001`，使用以下凭据：

- 用户名: `codesage_minio`（默认，可修改 `MINIO_ROOT_USER` 环境变量）
- 密码: `codesage_minio_change_me_32_chars`（默认，**生产环境必须修改** `MINIO_ROOT_PASSWORD`）

头像上传流程：
1. 前端调 `POST /api/v1/auth/me/avatar/upload` 获取 MinIO 预签名上传 URL
2. 浏览器直接 `PUT` 上传文件到 MinIO（不经后端中转）
3. 调 `POST /api/v1/auth/me/avatar/commit` 保存引用
4. 前端展示用 `el-avatar` 组件，URL 加时间戳破缓存

### 5.3 MinIO 对象存储

项目使用 MinIO（S3 兼容）存储用户头像等文件资源：

| 端口 | 用途 | 访问地址 |
|------|------|----------|
| 9000 | S3 API | `http://localhost:9000` |
| 9001 | Web 控制台 | `http://localhost:9001` |

**MinIO 控制台登录**：打开浏览器访问 `http://localhost:9001`，使用以下凭据：

- 用户名: `codesage_minio`（默认，可修改 `MINIO_ROOT_USER` 环境变量）
- 密码: `codesage_minio_change_me_32_chars`（默认，**生产环境必须修改** `MINIO_ROOT_PASSWORD`）

头像上传流程：前端调用 `POST /api/v1/auth/me/avatar/upload` 获取 MinIO 预签名上传 URL → 浏览器直接 `PUT` 上传文件到 MinIO → 调用 `POST /api/v1/auth/me/avatar/commit` 保存引用。

---

## 六、Docker 开发工作流

### 6.1 启动项目

```bash
docker-compose up -d --build backend frontend
```

### 6.2 开发热重载

- **后端**: 代码挂载到容器 (`./backend:/app/backend`)，uvicorn 以 `--reload` 模式运行，修改 `.py` 自动重启
- **前端**: 修改后需重新 build frontend 容器（或本地 `npm run dev`）
- **prompt 文件**: `sys_prompts/*.md` 若未挂载 volume，需重建 backend 镜像

### 6.3 重建命令

```bash
# 仅重建后端
docker-compose up -d --build backend

# 仅重建前端
docker-compose up -d --build frontend

# 全部重建（修改 prompt 后必做）
docker-compose up -d --build
```

### 6.4 查看日志

```bash
docker logs codesage-backend -f --tail 100
docker logs codesage-db -f --tail 50
docker logs codesage-minio -f --tail 50
```

---

## 七、Git 提交规范

提交信息格式: `<type>(<scope>): <description>`

| type | 适用场景 |
|------|---------|
| `feat` | 新功能（新接口、新页面、新组件） |
| `fix` | Bug 修复 |
| `refactor` | 重构（不改行为） |
| `style` | 代码格式调整 |
| `docs` | 文档更新 |
| `perf` | 性能优化 |
| `chore` | 构建/依赖/配置变更 |

常见 scope: `rag` / `auth` / `chat` / `generative-ui` / `minio` / `nodes` / `providers` / `docs`

示例:
- `feat(generative-ui): 新增 AI 预生成交互网页功能`
- `fix(auth): 修复登录按钮点击无反应问题`
- `refactor(minio): 将 S3 逻辑从 auth_service 抽离为独立模块`
- `chore(deps): 升级 LightRAG 至 1.5.3`

---

## 八、生成式 UI 开发指南

### 8.1 新增渲染组件

1. 在 `frontend/src/features/generative-ui/components/` 创建 `MyComponent.vue`，接收 `props` 属性
2. 在 `componentRegistry.ts` 导入并注册组件映射
3. 在 `backend/schemas/component.py` 添加组件类型定义
4. 在 `backend/sys_prompts/component_protocol.md` 更新组件白名单与 props 说明
5. 重建 backend 镜像（让新 prompt 生效）

### 8.2 组件协议 ComponentProtocol

```json
{
  "page_type": "analysis",
  "title": "页面标题",
  "components": [
    { "id": "sum_1", "type": "summary_card", "props": { "title": "...", "content": "..." } },
    { "id": "wp_1", "type": "webpage", "props": { "title": "详情", "description": "...", "html_content": "<!DOCTYPE html>..." } }
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

### 8.3 action 类型白名单

| type | 说明 | 必填字段 |
|------|------|----------|
| `regenerate` | 重新生成某组件 | `target_id` |
| `expand` | 展开某组件更多内容 | `target_id` |
| `function_call` | 调用后端函数 | `function_name`，可选 `params`/`target_id` |
| `open_webpage` | 打开预生成的全屏 HTML 子页面 | `params.title` + `params.html_content` |

### 8.4 节点版本管理

- **UiNode**: 卡片节点，支持父子树结构，关联会话与用户
- **UiNodeVersion**: 节点版本，每次生成/重生成/展开写入新版本，`content_json` 存 ComponentProtocol
- **UiNodeRelation**: 节点间关系（引用/展开等有向三元组）
- **current_version_id**: 不建外键（避免循环 DDL），由服务层维护一致性

### 8.5 新增函数调用工具

1. 在 `backend/function_calling/tools/` 创建工具函数
2. 在 `registry.py` 用装饰器注册
3. AI 会根据组件协议中的 `actions` 自动调用

---

## 九、常见陷阱与注意事项

1. **Vue 3 ref 绑定**: `<el-form :ref="formRef">` 这种动态绑定无法正确获取组件实例，必须使用函数式绑定 `:ref="(el) => { formRef = el }"`
2. **LightRAG 懒加载**: 不要在 `main.py` 启动时同步初始化 LightRAG，会导致启动超时。使用 `_ensure_ready()` 异步懒加载
3. **PostgreSQL 扩展**: PGGraphStorage 需要 Apache AGE 扩展（`CREATE EXTENSION IF NOT EXISTS age`），PGVectorStorage 需要 pgvector
4. **字段加密**: 用户敏感字段用 Fernet 加密存储，`FIELD_ENCRYPTION_KEY` 为空时会生成临时密钥（重启后无法解密历史数据）
5. **Redis 用途**: JWT 黑名单 / 刷新令牌 / 登录限流计数器，不是纯缓存
6. **前端 token 持久化**: 存在 localStorage，axios 请求拦截器自动注入 Authorization header
7. **长任务超时**: 知识库上传等大任务接口前端必须设 180s 超时（默认 30s 不够后端 60s+ 处理）
8. **模型名验证**: 阿里百炼 `qwen3.7-max` 不存在，用 `qwen-plus`/`qwen-max`；其他供应商同理先查文档
9. **flex 滚动**: flex 子项 `overflow-y-auto` 必须同时加 `min-h-0`（否则无法收缩触发滚动），且父级避免 `overflow-hidden` 覆盖
10. **头像缓存**: 浏览器会缓存图片，URL 加 `?_t=时间戳` 破缓存；统一用 `el-avatar` 组件
11. **render_mode 区分**: `chat_messages.render_mode` 为 `component` 时前端 `useChat` 过滤，由 `useGenerativeUi` 单独加载
12. **prompt 重建**: 修改 `sys_prompts/*.md` 后必须重建 backend 镜像（除非挂载了 volume）
13. **MinIO 密码同步**: 改 MinIO 密码需同步 `.env` 和 `docker-compose.yml` + 重启容器 + 清旧数据
14. **open_webpage 沙箱**: HTML 子页面通过 `iframe srcdoc` + `sandbox="allow-scripts allow-same-origin"` 渲染，避免 XSS 影响主应用
15. **TS 严格模式**: `vue-tsc --noEmit` 会检查未使用变量（TS6133），构建前必须清理
