# CodeSage — Claude Code 项目指令

> 完整规范: [AGENTS.md](../AGENTS.md)

## 快速摘要

- **后端**: FastAPI + SQLAlchemy (async) + PostgreSQL + Redis + LightRAG 1.5.3
- **前端**: Vue 3 + TypeScript + Element Plus + Tailwind CSS 4 + Pinia
- **部署**: Docker Compose（4 个容器: backend / frontend / db / redis）
- **语言**: 中文注释和文档

## 核心规则

1. RAG 代码全部在 `backend/rag/` 目录，分片交给 LightRAG 原生 ainsert()
2. 提示词全部在 `backend/sys_prompts/*.md`，禁止硬编码在 .py 中
3. 分层: endpoints → services → models，禁止跨层调用
4. Python 用 snake_case，TS/Vue 用 camelCase/PascalCase
5. Vue 3 el-form ref 必须用函数式绑定 `:ref="(el) => { formRef = el }"`
6. LightRAG 懒加载单例，不在启动时同步初始化
