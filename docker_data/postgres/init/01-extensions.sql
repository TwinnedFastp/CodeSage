-- CodeSage 数据库初始化脚本
-- 由 pgvector/pgvector:pg15 镜像在首次启动时自动执行

-- 启用 pgvector 向量扩展（LightRAG 的 PGVectorStorage 依赖此扩展）
CREATE EXTENSION IF NOT EXISTS vector;

-- 启用 pgcrypto 扩展（项目 users 表的 gen_random_uuid 依赖此扩展）
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 注意：LightRAG 的图谱存储使用 NetworkXStorage（文件存储），不依赖 Apache AGE 扩展。
-- 如果未来需要切换到 PGGraphStorage，需要改用预装 AGE 的 Postgres 镜像
-- （如 age/pg15 或自定义镜像从源码编译 AGE），并在此添加：CREATE EXTENSION IF NOT EXISTS age;
