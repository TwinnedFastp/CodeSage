"""
LightRAG 服务封装（Postgres + pgvector + NetworkX 混合存储后端）

设计要点：
1. 按用户缓存多实例：每个用户根据其供应商配置初始化独立的 LightRAG 实例
   - 每个用户有独立的 workspace（codesage_rag_user_{uid}）隔离知识库
   - 每个用户有独立的 working_dir（data/lightrag/user_{uid}）存放图谱文件
   - LLM / Embedding 函数绑定用户的供应商配置（API Key / Base URL / 模型名）
2. 懒加载：首次调用 insert/query 时才初始化，避免启动卡住
3. 混合存储架构（避免依赖 Apache AGE 扩展）：
   - kv_storage = PGKVStorage          → Postgres（事务安全）
   - vector_storage = PGVectorStorage  → Postgres + pgvector（HNSW 高性能检索）
   - graph_storage = NetworkXStorage   → 本地文件（.pkl，无需 AGE 扩展）
   - doc_status_storage = PGDocStatusStorage → Postgres
4. Postgres 连接通过环境变量配置（POSTGRES_HOST / POSTGRES_PORT / 等）
5. 供应商配置来源：DB（用户在设置页配置）优先，.env 环境变量兜底
6. 缓存失效：用户增删改供应商配置后，调用 invalidate_user(uid) 清除缓存
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
    LightRAG 项目级封装（按用户缓存多实例 + 混合存储后端）。

    每个 user_id 对应一个独立的 LightRAG 实例，使用该用户的供应商配置
    （API Key / Base URL / LLM 模型 / Embedding 模型 / 维度）初始化。
    知识库通过 workspace 和 working_dir 实现用户级隔离。
    """

    def __init__(self) -> None:
        # user_id -> LightRAG 实例
        self._rag_instances: dict[int, Any] = {}
        # user_id -> asyncio.Lock（防止并发重复初始化）
        self._locks: dict[int, asyncio.Lock] = {}
        # 保护 _locks 字典本身的全局锁
        self._global_lock = asyncio.Lock()

    async def _get_user_lock(self, user_id: int) -> asyncio.Lock:
        """获取指定用户的初始化锁（按需创建）。"""
        async with self._global_lock:
            if user_id not in self._locks:
                self._locks[user_id] = asyncio.Lock()
            return self._locks[user_id]

    async def invalidate_user(self, user_id: int) -> None:
        """
        失效指定用户的 LightRAG 缓存实例。

        在用户增删改供应商配置后调用，确保下次请求时用新配置重建实例。
        """
        async with self._global_lock:
            rag = self._rag_instances.pop(user_id, None)
            self._locks.pop(user_id, None)
        if rag is not None:
            # 尝试清理资源（LightRAG 没有 aclose，这里只移除引用让 GC 回收）
            logger.info("已失效用户 %s 的 LightRAG 实例缓存", user_id)

    async def _ensure_ready(self, user_id: int, provider_config: dict) -> Any:
        """
        确保指定用户的 LightRAG 已初始化并返回可用实例（双重检查锁）。

        provider_config 结构：
        {
            "llm_api_key": str,
            "llm_base_url": str,
            "llm_model": str,
            "embedding_model": str,
            "embedding_dim": int,
        }
        """
        if user_id in self._rag_instances:
            return self._rag_instances[user_id]

        lock = await self._get_user_lock(user_id)
        async with lock:
            if user_id in self._rag_instances:
                return self._rag_instances[user_id]

            if not settings.LIGHTRAG_ENABLED:
                raise RuntimeError("LightRAG 当前未启用，请检查 LIGHTRAG_ENABLED 配置。")

            api_key = provider_config.get("llm_api_key", "")
            if not api_key:
                raise RuntimeError("缺少 LLM_API_KEY，无法调用大语言模型。")

            base_url = provider_config.get("llm_base_url", "")
            llm_model = provider_config.get("llm_model", "")
            embedding_model = provider_config.get("embedding_model", "")
            embedding_dim = provider_config.get("embedding_dim", 1024)

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
            # 每个用户独立 workspace，隔离知识库数据
            workspace = f"codesage_rag_user_{user_id}"
            os.environ["POSTGRES_WORKSPACE"] = workspace

            logger.info(
                "初始化用户 %s 的 LightRAG Postgres 后端：host=%s db=%s workspace=%s model=%s",
                user_id,
                os.environ.get("POSTGRES_HOST"),
                os.environ.get("POSTGRES_DATABASE"),
                workspace,
                llm_model,
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

            # 每个用户独立 working_dir，存放图谱文件
            working_dir = Path(settings.LIGHTRAG_WORKING_DIR) / f"user_{user_id}"
            working_dir.mkdir(parents=True, exist_ok=True)

            async def llm_model_func(
                prompt: str,
                system_prompt: Optional[str] = None,
                history_messages: Optional[list[dict[str, str]]] = None,
                **kwargs: Any,
            ) -> str:
                """LightRAG 调用大语言模型的入口（OpenAI 兼容协议）。"""
                return await openai_complete_if_cache(
                    llm_model,
                    prompt,
                    system_prompt=system_prompt,
                    history_messages=history_messages or [],
                    api_key=api_key,
                    base_url=base_url,
                    **kwargs,
                )

            async def embedding_func(texts: list[str]) -> np.ndarray:
                """LightRAG 调用向量模型的入口。"""
                return await openai_embed(
                    texts,
                    model=embedding_model,
                    api_key=api_key,
                    base_url=base_url,
                )

            # 混合存储后端：KV/向量/文档状态走 Postgres，图谱走 NetworkX 文件存储
            rag = LightRAG(
                working_dir=str(working_dir),
                kv_storage="PGKVStorage",
                vector_storage="PGVectorStorage",
                graph_storage="NetworkXStorage",
                doc_status_storage="PGDocStatusStorage",
                llm_model_func=llm_model_func,
                embedding_func=EmbeddingFunc(
                    embedding_dim=embedding_dim,
                    func=embedding_func,
                ),
            )

            # 初始化存储和 pipeline 状态
            await rag.initialize_storages()
            await initialize_pipeline_status()

            self._rag_instances[user_id] = rag
            logger.info("用户 %s 的 LightRAG Postgres 后端初始化完成", user_id)
            return self._rag_instances[user_id]

    async def insert_text(self, user_id: int, provider_config: dict, text: str) -> None:
        """将原始文本写入 LightRAG 知识库（分块 + 实体关系抽取 + 向量化 + 图谱更新）。"""
        rag = await self._ensure_ready(user_id, provider_config)
        if hasattr(rag, "ainsert"):
            await rag.ainsert(text)
        else:
            await asyncio.to_thread(rag.insert, text)

    async def insert_file(
        self, user_id: int, provider_config: dict,
        content: str, filename: str, source: str | None = None,
    ) -> None:
        """
        将文件内容写入知识库。

        解析 → 拼接标题头/来源头 → 调用 LightRAG ainsert（自带分片+向量化+图谱构建）。
        """
        parsed = extract_text_from_content(content, filename)
        text = f"# {filename}\n\n{parsed}"
        if source:
            text = f"资料来源：{source}\n\n{text}"
        await self.insert_text(user_id, provider_config, text)

    async def query(
        self, user_id: int, provider_config: dict,
        question: str, mode: str = "hybrid",
    ) -> str:
        """
        查询 LightRAG 知识库。

        mode 取值：
        - naive：普通向量检索
        - local：局部实体关系
        - global：全局图谱关系
        - hybrid：混合模式（默认，效果最好）
        """
        rag = await self._ensure_ready(user_id, provider_config)
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

    async def list_documents(self, user_id: int, provider_config: dict) -> list[dict]:
        """列出知识库中已处理的文档（用于前端知识库管理面板）。"""
        rag = await self._ensure_ready(user_id, provider_config)
        try:
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
            logger.exception("列出文档失败 user_id=%s", user_id)
        return []

    async def delete_document(self, user_id: int, provider_config: dict, doc_id: str) -> bool:
        """删除知识库中的某个文档及其相关实体/关系/向量。"""
        rag = await self._ensure_ready(user_id, provider_config)
        try:
            if hasattr(rag, "adelete_by_doc_id"):
                await rag.adelete_by_doc_id(doc_id)
                return True
            elif hasattr(rag, "delete_by_doc_id"):
                await asyncio.to_thread(rag.delete_by_doc_id, doc_id)
                return True
        except Exception:
            logger.exception("删除文档失败 user_id=%s doc_id=%s", user_id, doc_id)
        return False


# 全局单例：FastAPI 路由直接复用（内部按 user_id 缓存多实例）
lightrag_service = LightRAGService()
