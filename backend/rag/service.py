"""
LightRAG 服务封装（Postgres + pgvector + NetworkX 混合存储后端）

设计要点：
1. 懒加载单例：首次真正调用 insert/query 时才初始化，避免普通后端启动卡住
2. 混合存储架构（避免依赖 Apache AGE 扩展）：
   - kv_storage = PGKVStorage          → Postgres（事务安全）
   - vector_storage = PGVectorStorage  → Postgres + pgvector（HNSW 高性能检索）
   - graph_storage = NetworkXStorage   → 本地文件（.pkl，无需 AGE 扩展）
   - doc_status_storage = PGDocStatusStorage → Postgres
   说明：PGGraphStorage 依赖 Apache AGE 图数据库扩展，而 pgvector/pgvector:pg15
         镜像未预装 AGE，CREATE EXTENSION age 会失败，create_graph() 函数不存在。
         NetworkXStorage 功能等价（实体/关系图谱完整），只是图谱数据存文件而非 DB。
3. Postgres 连接通过环境变量配置（POSTGRES_HOST / POSTGRES_PORT / 等）
4. 与项目主数据库共用同一个 PostgreSQL 实例，通过 POSTGRES_WORKSPACE 隔离 RAG 数据
5. LLM / Embedding 走 OpenAI 兼容接口（智谱 GLM / 百炼 / OpenAI 均可）
"""
import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Optional

import numpy as np

from backend.core.config import settings
from backend.rag.parser import extract_text_from_content

logger = logging.getLogger(__name__)


class LightRAGService:
    """
    LightRAG 项目级封装（混合存储后端）。

    优势：
    1. API 层不关心 LightRAG 如何初始化
    2. 整个后端复用同一个 LightRAG 实例
    3. KV/向量/文档状态存入 Postgres，天然支持多实例并发、备份、事务一致性
    4. 向量检索走 pgvector 的 HNSW 索引，性能稳定
    5. 图谱用 NetworkX 文件存储，无需 Apache AGE 扩展，部署更简单
    """

    def __init__(self) -> None:
        self._rag: Optional[Any] = None
        self._lock = asyncio.Lock()

    async def _ensure_ready(self) -> Any:
        """确保 LightRAG 已初始化并返回可用实例（双重检查锁）。"""
        if self._rag is not None:
            return self._rag

        async with self._lock:
            if self._rag is not None:
                return self._rag

            if not settings.LIGHTRAG_ENABLED:
                raise RuntimeError("LightRAG 当前未启用，请检查 LIGHTRAG_ENABLED 配置。")

            if not settings.lightrag_api_key:
                raise RuntimeError("缺少 LLM_API_KEY，无法调用大语言模型。")

            # 确保 LightRAG Postgres 连接环境变量已设置
            # 项目主库用 POSTGRES_SERVER，LightRAG 用 POSTGRES_HOST，这里做兼容
            if not os.environ.get("POSTGRES_HOST"):
                os.environ["POSTGRES_HOST"] = settings.POSTGRES_SERVER
            if not os.environ.get("POSTGRES_PORT"):
                os.environ["POSTGRES_PORT"] = "5432"
            if not os.environ.get("POSTGRES_USER"):
                os.environ["POSTGRES_USER"] = settings.POSTGRES_USER
            if not os.environ.get("POSTGRES_PASSWORD"):
                os.environ["POSTGRES_PASSWORD"] = settings.POSTGRES_PASSWORD
            if not os.environ.get("POSTGRES_DATABASE"):
                os.environ["POSTGRES_DATABASE"] = settings.POSTGRES_DB
            if not os.environ.get("POSTGRES_WORKSPACE"):
                os.environ["POSTGRES_WORKSPACE"] = "codesage_rag"

            logger.info(
                "初始化 LightRAG Postgres 后端：host=%s db=%s workspace=%s",
                os.environ.get("POSTGRES_HOST"),
                os.environ.get("POSTGRES_DATABASE"),
                os.environ.get("POSTGRES_WORKSPACE"),
            )

            # LightRAG 是可选重依赖，放在函数内导入
            try:
                from lightrag import LightRAG
                from lightrag.kg.shared_storage import initialize_pipeline_status
                from lightrag.llm.openai import openai_complete_if_cache, openai_embed
                from lightrag.utils import EmbeddingFunc
            except ImportError as exc:
                raise RuntimeError(
                    "未安装 LightRAG，请先执行 pip install lightrag-hku pgvector asyncpg。"
                ) from exc

            working_dir = Path(settings.LIGHTRAG_WORKING_DIR)
            working_dir.mkdir(parents=True, exist_ok=True)

            async def llm_model_func(
                prompt: str,
                system_prompt: Optional[str] = None,
                history_messages: Optional[list[dict[str, str]]] = None,
                **kwargs: Any,
            ) -> str:
                """LightRAG 调用大语言模型的入口（OpenAI 兼容协议）。"""
                return await openai_complete_if_cache(
                    settings.LLM_MODEL,
                    prompt,
                    system_prompt=system_prompt,
                    history_messages=history_messages or [],
                    api_key=settings.lightrag_api_key,
                    base_url=settings.lightrag_base_url,
                    **kwargs,
                )

            async def embedding_func(texts: list[str]) -> np.ndarray:
                """LightRAG 调用向量模型的入口。"""
                return await openai_embed(
                    texts,
                    model=settings.EMBEDDING_MODEL,
                    api_key=settings.lightrag_api_key,
                    base_url=settings.lightrag_base_url,
                )

            # 混合存储后端：KV/向量/文档状态走 Postgres，图谱走 NetworkX 文件存储
            # 不使用 PGGraphStorage，因为它依赖 Apache AGE 扩展，
            # 而 pgvector/pgvector:pg15 镜像未预装 AGE，会导致 create_graph() 报错
            rag = LightRAG(
                working_dir=str(working_dir),
                kv_storage="PGKVStorage",
                vector_storage="PGVectorStorage",
                graph_storage="NetworkXStorage",
                doc_status_storage="PGDocStatusStorage",
                llm_model_func=llm_model_func,
                embedding_func=EmbeddingFunc(
                    embedding_dim=settings.EMBEDDING_DIM,
                    func=embedding_func,
                ),
            )

            # 初始化存储和 pipeline 状态
            await rag.initialize_storages()
            await initialize_pipeline_status()

            self._rag = rag
            logger.info("LightRAG Postgres 后端初始化完成")
            return self._rag

    async def insert_text(self, text: str) -> None:
        """将原始文本写入 LightRAG 知识库（分块 + 实体关系抽取 + 向量化 + 图谱更新）。"""
        rag = await self._ensure_ready()
        if hasattr(rag, "ainsert"):
            await rag.ainsert(text)
        else:
            await asyncio.to_thread(rag.insert, text)

    async def insert_file(self, content: str, filename: str, source: str | None = None) -> None:
        """
        将文件内容写入知识库。

        解析 → 拼接标题头/来源头 → 调用 LightRAG ainsert（自带分片+向量化+图谱构建）。
        """
        parsed = extract_text_from_content(content, filename)
        text = f"# {filename}\n\n{parsed}"
        if source:
            text = f"资料来源：{source}\n\n{text}"
        await self.insert_text(text)

    async def query(self, question: str, mode: str = "hybrid") -> str:
        """
        查询 LightRAG 知识库。

        mode 取值：
        - naive：普通向量检索
        - local：局部实体关系
        - global：全局图谱关系
        - hybrid：混合模式（默认，效果最好）
        """
        rag = await self._ensure_ready()
        try:
            from lightrag import QueryParam
        except ImportError as exc:
            raise RuntimeError("未安装 LightRAG，无法导入 QueryParam。") from exc

        query_param = QueryParam(mode=mode)

        if hasattr(rag, "aquery"):
            answer = await rag.aquery(question, param=query_param)
        else:
            answer = await asyncio.to_thread(rag.query, question, param=query_param)

        return str(answer)

    async def list_documents(self) -> list[dict]:
        """列出知识库中已处理的文档（用于前端知识库管理面板）。"""
        rag = await self._ensure_ready()
        try:
            # LightRAG 1.5+ 提供 document_status 存储
            doc_status_storage = rag.doc_status_storage
            if hasattr(doc_status_storage, "get_all"):
                docs = await doc_status_storage.get_all()
                return [
                    {
                        "id": doc.get("id", ""),
                        "content_summary": doc.get("content_summary", "")[:100],
                        "content_length": doc.get("content_length", 0),
                        "status": doc.get("status", "unknown"),
                        "created_at": str(doc.get("created_at", "")),
                        "updated_at": str(doc.get("updated_at", "")),
                    }
                    for doc in (docs or [])
                ]
        except Exception:
            logger.exception("列出文档失败")
        return []

    async def delete_document(self, doc_id: str) -> bool:
        """删除知识库中的某个文档及其相关实体/关系/向量。"""
        rag = await self._ensure_ready()
        try:
            if hasattr(rag, "adelete_by_doc_id"):
                await rag.adelete_by_doc_id(doc_id)
                return True
            elif hasattr(rag, "delete_by_doc_id"):
                await asyncio.to_thread(rag.delete_by_doc_id, doc_id)
                return True
        except Exception:
            logger.exception("删除文档失败 doc_id=%s", doc_id)
        return False


# 全局单例：FastAPI 路由直接复用
lightrag_service = LightRAGService()
