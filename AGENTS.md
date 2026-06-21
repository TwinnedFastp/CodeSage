# CodeSage 项目开发规范 (AGENTS.md)

> **AI 编程助手入口文件（各平台自动识别）：**
> - Claude (Anthropic) → [.claude/CLAUDE.md](.claude/CLAUDE.md)
> - Cursor → [.cursorrules](.cursorrules)
> - GitHub Copilot → [.github/copilot-instructions.md](.github/copilot-instructions.md)
> - OpenAI Codex → [.codex/instructions.md](.codex/instructions.md)
>
> 本文档是**完整权威版本**，修改代码前必须先阅读，确保符合项目约定。

---

## 一、项目概述

| 项 | 值 |
|---|---|
| **项目名** | CodeSage |
| **定位** | 类 ChatGPT 的 AI 对话系统，集成 LightRAG 知识库检索增强生成 |
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
│ FastAPI      │ PostgreSQL 15 (pgvector)              │
│ SQLAlchemy   │ Redis 7 (Alpine)                      │
│ Pydantic     │ Docker Compose                        │
│ asyncpg      │                                       │
│ LightRAG 1.5 │                                       │
└──────────────┴──────────────────────────────────────┘
```

---

## 二、目录结构规范

```
CodeSage/
├── backend/                          # Python FastAPI 后端
│   ├── main.py                       # 应用入口：FastAPI 实例、CORS、异常处理、路由注册
│   ├── init_db.py                    # 数据库初始化脚本（建表）
│   ├── requirements.txt              # Python 依赖
│   ├── Dockerfile                    # 后端容器构建
│   │
│   ├── api/v1/                       # API 路由层（只做 HTTP 协议转换，不含业务逻辑）
│   │   ├── api.py                    # 路由聚合器：include_router 汇总所有端点
│   │   ├── deps.py                   # 依赖注入：get_current_user / get_db 等
│   │   └── endpoints/                # 各业务端点文件（每个文件对应一个领域）
│   │       ├── auth.py               # 认证: 注册 / 登录 / 登出 / 邮箱验证 / 刷新令牌 / 当前用户
│   │       ├── chat.py               # 聊天: 流式对话 / 非流式对话
│   │       ├── conversations.py      # 会话管理: CRUD 会话 / 消息 / 偏好 / 事实记忆 / 任务
│   │       └── providers.py          # AI 模型供应商管理
│   │
│   ├── rag/                          # RAG 知识库模块（独立目录，不散落在 services/ 中）
│   │   ├── __init__.py               # 导出 lightrag_service 单例
│   │   ├── service.py                # LightRAG 封装: insert / query / list / delete / insert_file
│   │   ├── schemas.py                # RAG 请求/响应 Pydantic 模型
│   │   ├── endpoints.py              # RAG REST API: status / documents / upload-file / query
│   │   └── parser.py                 # 文件解析器: MD/TXT 文本清理
│   │
│   ├── sys_prompts/                  # AI 提示词集中管理（全部 .md 文件）
│   │   ├── __init__.py               # 统一导出为字符串常量
│   │   ├── chat_system.md            # CodeSage 主系统提示词
│   │   └── title_generator.md        # 标题生成器提示词
│   │
│   ├── services/                     # 业务逻辑层（纯函数/类，无 HTTP 概念）
│   │   ├── auth_service.py           # 认证: 密码哈希 / JWT 签发 / 邮箱发送
│   │   ├── conversation_service.py   # 会话: CRUD / 标题生成 / 记忆管理
│   │   ├── email_service.py          # SMTP 邮件发送
│   │   └── provider_service.py       # AI 供应商配置的增删改查
│   │
│   ├── models/                       # SQLAlchemy ORM 模型（数据库表映射）
│   │   ├── base.py                   # Base 声明式基类
│   │   ├── user.py                   # users 表
│   │   ├── conversation.py           # chat_sessions / chat_messages / user_facts / user_preferences / user_tasks 表
│   │   └── provider.py               # ai_providers 表
│   │
│   ├── schemas/                      # Pydantic 请求/响应模型（API 数据校验）
│   │   ├── auth.py                   # 注册/登录/令牌请求体
│   │   ├── conversation.py           # 会话/消息/偏好/事实/任务 schema
│   │   └── provider.py               # 供应商配置 schema
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
│   │   │   ├── auth.ts               # 认证 API
│   │   │   ├── conversations.ts      # 会话 API
│   │   │   ├── providers.ts          # 供应商 API
│   │   │   └── rag.ts               # 知识库 API
│   │   │
│   │   ├── composables/              # Vue 组合式函数（业务状态与操作）
│   │   │   ├── useChat.ts            # 聊天逻辑: 发送消息 / SSE 流式接收 / RAG 模式
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
│   │   │   ├── ChatView.vue          # 主聊天页面（核心页面）
│   │   │   └── SettingsView.vue      # 设置页（供应商配置等）
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
│   │       ├── hero.png              # 登录页主视觉图
│   │       └── vite.svg / vue.svg    # 图标
│   │
│   ├── package.json                  # 前端依赖
│   ├── vite.config.ts                # Vite 配置
│   ├── tsconfig.json                 # TypeScript 配置
│   ├── tailwind.config.js            # Tailwind 配置（如有）
│   └── index.html                    # HTML 入口
│
├── docker-compose.yml                # Docker 编排: db / redis / backend / frontend
├── docker_data/                      # 运行时数据持久化
│   ├── postgres/init/01-extensions.sql  # PG 扩展初始化: vector / pgcrypto / age
│   ├── redis/redis.conf              # Redis 配置
│   └── lightrag/                     # LightRAG 本地缓存数据
│
├── .env                              # 环境变量（不入 Git）
├── .env.example                      # 环境变量模板
└── README.md                         # 项目说明文档
```

---

## 三、编码规范

### 3.1 命名约定

| 层级 | 语言 | 规范 | 示例 |
|------|------|------|------|
| **Python 文件** | Python | `snake_case` | `auth_service.py`, `lightrag_service.py` |
| **Python 类** | Python | `PascalCase` | `LightRAGService`, `UserCreate` |
| **Python 函数/变量** | Python | `snake_case` | `insert_text()`, `lightrag_api_key` |
| **Python 常量** | Python | `UPPER_SNAKE_CASE` | `CHAT_SYSTEM_PROMPT`, `LIGHTRAG_ENABLED` |
| **TypeScript 文件** | TS | `camelCase` | `useChat.ts`, `useRag.ts` |
| **TS/Vue 组件** | TS | `PascalCase` | `KnowledgePanel.vue`, `ChatView.vue` |
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
```

### 3.3 RAG 模块特殊规则

- **所有 RAG 相关代码必须在 `backend/rag/` 目录内**，不允许散落到 `services/`、`schemas/`、`endpoints/`
- **分片/向量化/图谱构建全部交给 LightRAG 原生 `ainsert()`**，不自研重复逻辑
- **文件传输方式**: 前端 FileReader 读文本 → POST JSON 到 `/rag/upload-file`（不用 FormData/multipart）
- **LightRAG 采用懒加载单例模式**: 首次调用 insert/query 时才初始化

### 3.4 提示词管理规则

- **所有 AI system prompt 必须存放在 `backend/sys_prompts/*.md`**
- **禁止在 Python 代码中硬编码 prompt 字符串**
- 动态部分（如 `{knowledge}` 变量注入）由代码在运行时拼接
- 通过 `from backend.sys_prompts import XXX_PROMPT` 引入使用

### 3.5 前端 UI 规范

- **UI 框架**: Element Plus 2.x（全局注册）
- **CSS 方案**: Tailwind CSS 4.x（原子类优先），Element Plus 内置样式作为补充
- **设计风格**: 杂志风（Magazine Style）
  - 主色调: `#111111`（近黑）/ 辅色 `#FAFAFA`（暖白灰）/ 边框 `#E8E6E1`
  - 字体: 标题用 `font-serif`（衬线），正文用系统默认无衬线
  - 圆角: 大元素 `rounded-2xl` / 按钮 `rounded-full` / 卡片 `rounded-xl`
- **自定义滚动条**: 全局 `.custom-scrollbar` 样式（细窄、透明）
- **图标**: 使用 `@element-plus/icons-vue`，不引入额外图标库

---

## 四、API 设计规范

### 4.1 URL 结构

```
基础路径: /api/v1
认证前缀: 所有需要登录的接口使用 Depends(get_current_user)

路由分组:
  /api/v1/auth/*        ← auth.py       (无需认证)
  /api/v1/chat/*        ← chat.py       (需认证)
  /api/v1/conversations/* ← conversations.py (需认证)
  /api/v1/providers/*   ← providers.py  (需认证)
  /api/v1/rag/*         ← rag/endpoints.py (需认证)
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

### 4.3 前端 API 封装模式

```typescript
// api/xxx.ts — 统一使用 request 实例（已含 baseURL + token 拦截器）
import { request } from './request'

export function someAction(payload: SomeIn): Promise<SomeOut> {
  return request.post<SomeOut>('/some/path', payload).then(r => r.data)
}
```

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

> **LLM 相关配置（API Key / Model / Embedding）不在 .env 中管理**，而是通过前端「设置 → 模型供应商」页面写入 `ai_providers` 数据库表。

---

## 六、Docker 开发工作流

### 6.1 启动项目

```bash
docker-compose up -d --build backend frontend
```

### 6.2 开发热重载

- **后端**: 代码挂载到容器 (`./backend:/app/backend`)，uvicorn 以 `--reload` 模式运行，修改 `.py` 自动重启
- **前端**: 修改后需重新 build frontend 容器（或本地 `npm run dev`）

### 6.3 重建命令

```bash
# 仅重建后端
docker-compose up -d --build backend

# 仅重建前端
docker-compose up -d --build frontend

# 全部重建
docker-compose up -d --build
```

### 6.4 查看日志

```bash
docker logs codesage-backend -f --tail 100
docker logs codesage-db -f --tail 50
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

示例:
- `feat(rag): 新增 Markdown 文件上传功能`
- `fix(auth): 修复登录按钮点击无反应问题`
- `refactor: 将 RAG 代码归拢到 rag/ 目录`
- `chore(deps): 升级 LightRAG 至 1.5.3`

---

## 八、常见陷阱与注意事项

1. **Vue 3 ref 绑定**: `<el-form :ref="formRef">` 这种动态绑定无法正确获取组件实例，必须使用函数式绑定 `:ref="(el) => { formRef = el }"`
2. **LightRAG 懒加载**: 不要在 `main.py` 启动时同步初始化 LightRAG，会导致启动超时。使用 `_ensure_ready()` 异步懒加载
3. **PostgreSQL 扩展**: PGGraphStorage 需要 Apache AGE 扩展（`CREATE EXTENSION IF NOT EXISTS age`），PGVectorStorage 需要 pgvector
4. **字段加密**: 用户敏感字段用 Fernet 加密存储，`FIELD_ENCRYPTION_KEY` 为空时会生成临时密钥（重启后无法解密历史数据）
5. **Redis 用途**: JWT 黑名单 / 刷新令牌 / 登录限流计数器，不是纯缓存
6. **前端 token 持久化**: 存在 localStorage，axios 请求拦截器自动注入 Authorization header
