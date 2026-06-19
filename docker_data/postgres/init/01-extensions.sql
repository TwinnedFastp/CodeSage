-- CodeSage 数据库初始化脚本
-- 由 pgvector/pgvector:pg15 镜像在首次启动时自动执行

-- 启用 pgvector 向量扩展（LightRAG 的 PGVectorStorage 依赖此扩展）
CREATE EXTENSION IF NOT EXISTS vector;

-- 启用 pgcrypto 扩展（项目 users 表的 gen_random_uuid 依赖此扩展）
CREATE EXTENSION IF NOT EXISTS pgcrypto;
