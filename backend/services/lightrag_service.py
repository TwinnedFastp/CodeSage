import asyncio
from pathlib import Path
from typing import Any, Optional

import numpy as np

from backend.core.config import settings


class LightRAGService:
    """
    LightRAG 的项目级封装。

    这样写的好处：
    1. API 层不需要关心 LightRAG 如何初始化。
    2. 整个后端复用同一个 LightRAG 实例，避免每次请求都重新加载索引。
    3. 初始化使用“懒加载”，只有第一次真正使用 RAG 时才会加载依赖和读取配置。
    """

    def __init__(self) -> None:
        self._rag: Optional[Any] = None
        self._lock = asyncio.Lock()

    async def _ensure_ready(self) -> Any:
        """
        确保 LightRAG 已初始化，并返回可用的 rag 实例。

        注意：LightRAG 初始化会创建本地存储目录、加载索引，并准备图谱/向量相关状态。
        这里用 asyncio.Lock 防止并发请求同时初始化多个实例。
        """
        if self._rag is not None:
            return self._rag

        async with self._lock:
            if self._rag is not None:
                return self._rag

            if not settings.LIGHTRAG_ENABLED:
                raise RuntimeError("LightRAG 当前未启用，请检查 LIGHTRAG_ENABLED 配置。")

            if not settings.lightrag_api_key:
                raise RuntimeError("缺少 LLM_API_KEY 或 DASHSCOPE_API_KEY，无法调用百炼/OpenAI 兼容模型。")

            # LightRAG 是可选重依赖，放在函数内导入可以让普通后端启动更稳。
            try:
                from lightrag import LightRAG
                from lightrag.kg.shared_storage import initialize_pipeline_status
                from lightrag.llm.openai import openai_complete_if_cache, openai_embed
                from lightrag.utils import EmbeddingFunc
            except ImportError as exc:
                raise RuntimeError("未安装 LightRAG，请先执行 pip install -r backend/requirements.txt。") from exc

            working_dir = Path(settings.LIGHTRAG_WORKING_DIR)
            working_dir.mkdir(parents=True, exist_ok=True)

            async def llm_model_func(
                prompt: str,
                system_prompt: Optional[str] = None,
                history_messages: Optional[list[dict[str, str]]] = None,
                **kwargs: Any,
            ) -> str:
                """
                LightRAG 调用大语言模型的入口。

                这里使用 openai_complete_if_cache，但传入的是百炼的 base_url、api_key 和模型名。
                因为百炼兼容 OpenAI Chat Completions 协议，所以 LightRAG 不需要知道背后是谁。
                """
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
                """
                LightRAG 调用向量模型的入口。

                默认使用百炼 text-embedding-v4。官方文档说明它默认输出 1024 维，
                所以 EMBEDDING_DIM 也默认配置为 1024，二者必须保持一致。
                """
                return await openai_embed(
                    texts,
                    model=settings.EMBEDDING_MODEL,
                    api_key=settings.lightrag_api_key,
                    base_url=settings.lightrag_base_url,
                )

            rag = LightRAG(
                working_dir=str(working_dir),
                llm_model_func=llm_model_func,
                embedding_func=EmbeddingFunc(
                    embedding_dim=settings.EMBEDDING_DIM,
                    func=embedding_func,
                ),
            )

            # 官方推荐：先初始化存储，再初始化 pipeline 状态。
            await rag.initialize_storages()
            await initialize_pipeline_status()

            self._rag = rag
            return self._rag

    async def insert_text(self, text: str) -> None:
        """
        将原始文本写入 LightRAG 知识库。

        LightRAG 会在内部完成分块、实体关系抽取、向量化和图谱更新。
        """
        rag = await self._ensure_ready()

        # 新版 LightRAG 提供异步 ainsert；如果当前版本没有，就退回到线程中执行同步 insert。
        if hasattr(rag, "ainsert"):
            await rag.ainsert(text)
        else:
            await asyncio.to_thread(rag.insert, text)

    async def query(self, question: str, mode: str = "hybrid") -> str:
        """
        查询 LightRAG 知识库。

        mode 常用取值：
        - naive：普通向量检索，适合简单问答
        - local：偏向局部实体关系
        - global：偏向全局图谱关系
        - hybrid：混合模式，通常作为默认选择
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


# 全局单例：FastAPI 路由直接复用它。
lightrag_service = LightRAGService()
