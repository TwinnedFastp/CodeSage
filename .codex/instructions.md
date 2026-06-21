# CodeSage — Codex Instructions

Read `AGENTS.md` for the complete project specification.

## Architecture
- **Backend**: FastAPI + async SQLAlchemy + PostgreSQL (pgvector) + Redis 7 + LightRAG 1.5.3
- **Frontend**: Vue 3.5 + TypeScript + Vite 8 + Element Plus 2 + Tailwind CSS 4 + Pinia 3
- **Deploy**: Docker Compose (backend:8000 / frontend:80 / db:5432 / redis:6379)

## Must-Follow Rules
1. RAG code → `backend/rag/` only (service.py / schemas.py / endpoints.py / parser.py)
2. AI prompts → `backend/sys_prompts/*.md` only, import via `from backend.sys_prompts import XXX_PROMPT`
3. Layering: `api/endpoints` → `services` → `models` (no skipping)
4. LightRAG chunking/vectorization → use native `ainsert()`, never implement custom splitting
5. Vue 3 el-form ref binding → use function form `:ref="(el) => { ref = el }"`
6. LightRAG → lazy singleton (`_ensure_ready()`), not init at startup
7. Python naming: snake_case; TS naming: camelCase/PascalCase; API routes: kebab-case
8. UI style: Magazine style with #111111 / #FAFAFA / #E8E6E1 palette, font-serif for headings
