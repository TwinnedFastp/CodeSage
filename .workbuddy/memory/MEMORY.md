# CodeSage 项目长期记忆

## 项目概览
- 类型：ChatGPT Clone（FastAPI + Vue3 + PostgreSQL + LightRAG）
- 后端：FastAPI (async) + SQLAlchemy 2.0 async + asyncpg + PostgreSQL 15
- 容器：docker-compose（db / redis / backend / frontend）
- 分支策略：develop 开发，main 主干

## 技术栈与约定
- 密码哈希：直接用 `bcrypt` 库（不要用 passlib，passlib 1.7.4 与 bcrypt>=4.1 不兼容，详见 .learnings/LEARNINGS.md LRN-20250619-001）
- JWT：access(7d) + refresh(30d)，jti 防重放；黑名单与 refresh 白名单存 Redis
- 邮箱认证：唯一身份标识，注册后发 24h 验证链接，未验证不可登录
- 登录安全：连续 5 次密码错误锁定 15 分钟，记录异常登录 IP（加密存储）
- 字段级加密：Fernet（utils/crypto.py），敏感字段（IP、user_facts.fact_value）加密入库，带 `enc::` 前缀做幂等
- DB 连接：echo=False（生产），pool_pre_ping=True
- Redis 配置：docker_data/redis/redis.conf（已纳入版本控制），AOF+RDB 持久化，挂载 docker_data/redis/data

## 数据模型（PostgreSQL，7 张表）
- users：邮箱用户（含验证/锁定/上次登录IP加密）
- login_logs：登录审计日志
- chat_sessions：会话（含自动摘要）
- chat_messages：原始聊天记录（message_id UUID 唯一，user_id 冗余隔离）
- user_preferences：用户长期偏好（JSONB，|| 操作符合并更新）
- user_facts：重要事实记忆（fact_value 加密，(user_id,fact_key) 唯一）
- user_tasks：任务状态（pending→in_progress→completed|cancelled）

## API 路由前缀
- /api/v1/auth : 注册/登录/登出/邮箱验证/刷新/当前用户
- /api/v1/conversations : 会话/消息/偏好/事实记忆/任务 CRUD（均需登录，按 user_id 隔离）
- /api/v1/chat : 流式对话（需登录，自动存消息到会话）
- /api/v1/rag : LightRAG 知识库

## 前端
- Vue3 + Vite + TS + Element Plus + Tailwind v4 + vue-router(hash) + pinia
- 极简杂志风：#FAFAFA / #111111 / #F3F2EE / DM Serif Display + Inter
- src/api/request.ts : axios + JWT 拦截器 + 401 跳登录
- src/stores/auth.ts : pinia 认证状态
- src/views : Login/Register/VerifyEmail/Chat
- nginx.conf : /api 反代 backend:8000，SSE 关闭 buffering

## 测试
- pytest，asyncio_mode=auto，session 级事件循环（解决 redis/asyncpg 跨测试循环问题）
- conftest 每个测试前后 flushdb Redis + TRUNCATE 全表
- 压测：10 万条 chat_messages，P95 < 200ms（实测分页 8ms / 计数 11ms / 点查 1ms）

## 关键文件
- backend/core/security.py : bcrypt + JWT + 邮箱/密码校验
- backend/core/redis_client.py : JWT 黑名单 / refresh 白名单 / 登录失败计数
- backend/utils/crypto.py : Fernet 字段加密
- backend/services/auth_service.py : 认证业务
- backend/services/conversation_service.py : 会话存储业务
- backend/init_db.py : 建表脚本（python -m backend.init_db）

## 环境变量（.env，已 gitignore）
- REDIS_URL / JWT_SECRET / FIELD_ENCRYPTION_KEY / SMTP_* / LOGIN_MAX_FAIL_ATTEMPTS 等
- 生产部署前必须改 JWT_SECRET、配 FIELD_ENCRYPTION_KEY、配 SMTP
