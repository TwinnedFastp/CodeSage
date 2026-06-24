"""
聊天流式接口（LightRAG 知识增强 + 多轮历史记忆 + 动态供应商配置）

设计要点：
1. 需要登录（依赖 get_current_user）
2. 每轮对话会读取会话历史消息，拼成 messages 数组传给 LLM —— 让 AI 真正"记住"上下文
3. 集成 LightRAG：用户显式开启 RAG 模式时检索知识库，作为 system prompt 的知识背景
4. 供应商配置动态化：从 DB 读取用户启用的供应商配置（API Key / Base URL / 模型），
   无 DB 配置时返回 400
5. 用户消息先落库，流式输出 LLM 回复，流结束后 assistant 回复落库
6. 流结束后保底触发标题生成（前端也会调，二者去重）
7. 无 session_id 时自动创建会话
8. RAG 错误透传：检索失败/超时时通过 SSE 推 rag_error 给前端，不再静默吞异常
9. RAG 检索前先推 rag_status=searching，避免前端在等待期完全无反馈
10. 兼容推理模型：同时处理 delta.content 和 delta.reasoning_content
"""
import asyncio
import json
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse, JSONResponse
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, get_db
from backend.models.user import User
from backend.rag.service import lightrag_service
from backend.services import conversation_service, node_service
from backend.services.provider_service import resolve_provider_config
from backend.sys_prompts import CHAT_SYSTEM_PROMPT
from backend.utils.document_extractor import extract_text_from_base64

logger = logging.getLogger(__name__)
router = APIRouter()

# 历史消息上限：取最近 N 条喂给 LLM，避免 token 爆炸
MAX_HISTORY_MESSAGES = 20


async def _persist_message(
    db: AsyncSession, user_id: int, session_id: str, role: str, content: str,
    render_mode: str = "text", attachments: list[dict] | None = None,
):
    """落库一条消息，失败不阻断主流程但记录日志。"""
    try:
        await conversation_service.add_message(
            db, user_id, session_id, role, content, render_mode=render_mode,
            attachments=attachments,
        )
    except Exception:
        logger.exception("消息落库失败 user_id=%s session_id=%s role=%s", user_id, session_id, role)


async def _load_history_messages(db: AsyncSession, user_id: int, session_id: str) -> list[dict]:
    """
    读取会话历史消息，映射成 OpenAI messages 格式。

    注意：调用时机要在本轮 user 消息落库之后，这样历史里已包含当前问题，
    传给 LLM 时就不需要再单独 append 当前消息，避免重复。
    """
    try:
        msgs = await conversation_service.list_messages(
            db, user_id, UUID(session_id), limit=MAX_HISTORY_MESSAGES, offset=0,
        )
    except Exception:
        logger.exception("读取历史消息失败 session_id=%s", session_id)
        return []

    history = []
    for m in msgs:
        role = "user" if m.role == "user" else "assistant"
        attachments = m.attachments if hasattr(m, "attachments") and m.attachments else None
        if attachments and role == "user":
            content = _build_multimodal_content(m.content, attachments)
        else:
            content = m.content
        history.append({"role": role, "content": content})
    return history


def _build_multimodal_content(text: str, attachments: list[dict]) -> list[dict] | str:
    """
    构建多模态消息内容（OpenAI Vision API 格式）。

    如果只有文本无图片，返回字符串；否则返回 content 数组格式。
    """
    images = [a for a in attachments if a.get("type") == "image"]
    if not images:
        return text

    content_parts = [{"type": "text", "text": text}]
    for img in images:
        image_url = img.get("data", "")
        if image_url:
            content_parts.append({
                "type": "image_url",
                "image_url": {"url": image_url}
            })
    return content_parts


async def _query_knowledge(
    user_id: int, provider_config: dict, user_message: str, mode: str = "hybrid",
    conversation_history: list[dict] | None = None,
) -> tuple[str, str]:
    """
    用 LightRAG 检索知识库，返回 (knowledge, error)。

    - knowledge: 检索到的知识上下文，失败时为空串
    - error: 失败原因（超时/异常），成功时为空串

    新增 conversation_history 参数：传给 LightRAG 让它理解多轮对话上下文，
    提升检索准确率（对齐 LightRAG-main QueryParam.conversation_history）。
    """
    from backend.core.config import settings
    if not settings.LIGHTRAG_ENABLED:
        return "", ""
    try:
        knowledge = await lightrag_service.query(
            user_id, provider_config, user_message, mode=mode,
            conversation_history=conversation_history,
        )
        return knowledge, ""
    except asyncio.TimeoutError:
        logger.warning("LightRAG 知识检索超时（>60s），降级为纯对话 user_id=%s", user_id)
        return "", "知识库检索超时（超过 60 秒），已降级为普通对话。如持续超时请检查模型配置或网络。"
    except Exception as exc:
        logger.exception("LightRAG 知识检索失败，降级为纯对话 user_id=%s", user_id)
        return "", f"知识库检索失败：{exc}。已降级为普通对话。请在知识库面板查看文档状态或重建知识库。"


def _build_system_prompt(knowledge: str, use_rag: bool) -> str:
    """构建 system prompt，根据是否启用 RAG 决定是否注入知识背景。"""
    base = CHAT_SYSTEM_PROMPT
    if use_rag and knowledge and knowledge.strip():
        return (
            base
            + "\n\n**知识库检索（RAG 模式已开启）**"
            + f"\n本次从知识库检索到以下相关资料，请在回答时参考并适当引用：\n---\n{knowledge.strip()}\n---"
        )
    return base


async def ai_response_generator(
    history: list[dict],
    user_message: str,
    provider_config: dict,
    knowledge: str = "",
    use_rag: bool = False,
    attachments: list[dict] | None = None,
):
    """
    大模型流式回复生成器。

    - history: 已包含当前 user 消息的历史数组（OpenAI messages 格式）
    - provider_config: 用户的供应商配置（含 API Key / Base URL / 模型名）
    - knowledge: LightRAG 检索到的知识上下文（可空）
    - use_rag: 是否处于 RAG 模式
    - attachments: 用户消息的附件（图片/文档）
    """
    api_key = provider_config.get("llm_api_key", "")
    base_url = provider_config.get("llm_base_url", "")
    llm_model = provider_config.get("llm_model", "")

    if not api_key:
        yield f"data: {json.dumps({'content': '未配置大模型 API Key，请在设置页面添加供应商配置。'}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"
        return

    # 每次请求按用户配置创建独立的 OpenAI 客户端
    # （AsyncOpenAI 内部有连接池，轻量创建无性能问题）
    client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    system_prompt = _build_system_prompt(knowledge, use_rag)
    messages = [{"role": "system", "content": system_prompt}] + history

    if attachments:
        images = [a for a in attachments if a.get("type") == "image"]
        if images:
            user_content = _build_multimodal_content(user_message, attachments)
            for i in range(len(messages) - 1, -1, -1):
                if messages[i]["role"] == "user":
                    messages[i]["content"] = user_content
                    break

    try:
        response = await client.chat.completions.create(
            model=llm_model,
            messages=messages,
            stream=True,
        )
        async for chunk in response:
            if not (chunk.choices and chunk.choices[0].delta):
                continue
            delta = chunk.choices[0].delta
            # 优先 delta.content（普通聊天模型）；
            # 推理模型（如 GLM-4.5 / DeepSeek-R1 / QwQ）可能只在 reasoning_content 输出，
            # content 为空，此时用 reasoning_content 作为内容输出，避免"AI 不说话"。
            piece = delta.content or getattr(delta, "reasoning_content", None)
            if piece:
                yield f"data: {json.dumps({'content': piece}, ensure_ascii=False)}\n\n"
    except Exception as e:
        logger.exception("调用大模型失败 model=%s base_url=%s", llm_model, base_url)
        yield f"data: {json.dumps({'content': f'调用大模型发生错误：{str(e)}'}, ensure_ascii=False)}\n\n"

    yield "data: [DONE]\n\n"


async def _maybe_auto_title(
    db: AsyncSession, user_id: int, session_id: str,
    current_title: str | None, provider_config: dict,
) -> str | None:
    """
    流结束后保底触发标题生成。

    触发条件：标题为空 / 仍是默认 "新会话"。
    成功返回新标题，失败返回 None（前端调用作为补充，二者通过 titleGeneratedSessions 去重）。
    """
    if current_title and current_title != "新会话":
        return None
    try:
        updated = await conversation_service.generate_title(
            db, user_id, UUID(session_id), provider_config=provider_config,
        )
        return updated.title
    except Exception:
        logger.debug("保底标题生成跳过 session_id=%s", session_id)
        return None


async def _streaming_with_persistence(
    user_message: str, session_id: str, user_id: int, db: AsyncSession,
    provider_config: dict, use_rag: bool, mode: str,
    attachments: list[dict] | None = None,
):
    """
    流式生成 + 落库 + 保底标题 + 断连保护 + Redis 中间态缓存：
    1. 用户消息先落库
    2. 读取历史（已含本轮 user 消息）
    3. LightRAG 检索知识（仅当 use_rag=true 时，用户显式开启 RAG 模式）
    4. 初始化 Redis 流式缓存（刷新/断连恢复用）
    5. 流式输出 LLM 回复：每个 chunk 增量写 Redis + 推前端（带断连保护）
    6. assistant 回复落库（无论客户端是否断连都落库，保证不丢）
    7. 清理 Redis 缓存 + 保底触发标题生成

    断连保护：客户端断开时捕获 GeneratorExit，标记 client_disconnected，
    后端继续从 LLM 拉取剩余 chunk 并写入 Redis / 落库，已生成内容不丢失。
    用户刷新页面后可通过 GET /chat/streaming/{session_id} 从 Redis 恢复进行中的内容。
    """
    from backend.core.streaming_cache import (
        init_streaming, append_chunk, finalize_streaming,
    )

    # 1. 用户消息落库
    await _persist_message(db, user_id, session_id, "user", user_message, attachments=attachments)

    # 2. 读取历史（已包含本轮 user 消息）
    history = await _load_history_messages(db, user_id, session_id)

    # 3. 知识检索：只有用户显式开启 RAG 模式才检索
    # 先推 rag_status 事件，让前端知道正在检索（避免等待期无反馈）
    knowledge = ""
    if use_rag:
        yield f"data: {json.dumps({'rag_status': 'searching'}, ensure_ascii=False)}\n\n"
        # 传对话历史给 LightRAG，让它理解多轮上下文（对齐 LightRAG-main）
        knowledge, rag_error = await _query_knowledge(
            user_id, provider_config, user_message, mode,
            conversation_history=history,
        )
        if rag_error:
            # 检索失败/超时：推错误给前端，降级为纯对话（knowledge 为空）
            yield f"data: {json.dumps({'rag_error': rag_error}, ensure_ascii=False)}\n\n"
        else:
            yield f"data: {json.dumps({'rag_status': 'done'}, ensure_ascii=False)}\n\n"

    # 4. 初始化 Redis 流式缓存（用于刷新/断连恢复；Redis 不可用时退化为纯内存流）
    stream_token = None
    try:
        stream_token = await init_streaming(session_id, role="assistant", render_mode="text")
    except Exception:
        logger.warning("初始化流式缓存失败，退化为纯内存流 session_id=%s", session_id, exc_info=True)

    # 5. 流式生成：增量写 Redis + 推前端（带断连保护）
    full_reply_parts: list[str] = []
    client_disconnected = False
    async for chunk in ai_response_generator(history, user_message, provider_config, knowledge, use_rag, attachments):
        # 解析 chunk 提取 content，用于 Redis 缓存和最终落库
        if chunk.startswith("data: ") and chunk.strip() != "data: [DONE]":
            data = chunk[6:].strip()
            try:
                parsed = json.loads(data)
                piece = parsed.get("content")
                if piece:
                    full_reply_parts.append(piece)
                    # 增量写入 Redis（失败不阻断，退化为纯内存流仍能落库）
                    if stream_token:
                        await append_chunk(session_id, stream_token, piece)
            except Exception:
                pass
        # 推给前端（断连后跳过 yield，后端继续生成并缓存）
        if not client_disconnected:
            try:
                yield chunk
            except (GeneratorExit, ConnectionError, OSError):
                client_disconnected = True
                logger.info("客户端断开连接，后端继续生成并缓存 session_id=%s", session_id)

    # 6. assistant 回复落库（无论是否断连都落库，保证已生成内容不丢失）
    full_reply = "".join(full_reply_parts)
    if full_reply:
        await _persist_message(db, user_id, session_id, "assistant", full_reply)

    # 7. 清理 Redis 缓存（内容已落库 PG，临时态可释放）
    if stream_token:
        try:
            await finalize_streaming(session_id, stream_token)
        except Exception:
            logger.debug("清理流式缓存失败 session_id=%s", session_id, exc_info=True)

    # 8. 保底标题生成（客户端断开时仍执行落库，仅跳过 SSE 推送）
    try:
        session = await conversation_service.get_session(db, user_id, UUID(session_id))
        new_title = await _maybe_auto_title(
            db, user_id, session_id, session.title, provider_config,
        )
        if new_title and not client_disconnected:
            try:
                yield f"data: {json.dumps({'title': new_title, 'session_id': session_id}, ensure_ascii=False)}\n\n"
            except (GeneratorExit, ConnectionError, OSError):
                pass
    except Exception:
        logger.debug("读取会话标题失败，跳过保底生成 session_id=%s", session_id)


async def _component_streaming_with_persistence(
    user_message: str, session_id: str, user_id: int, db: AsyncSession,
    provider_config: dict, use_rag: bool, mode: str,
):
    """
    生成式组件 JSONL 流式管道（支持断线续存）：
    1. 用户消息落库
    2. 读取历史 / RAG 检索
    3. 流式生成 JSONL：每收到完整行推 partial_component 给前端
    4. 即使客户端断开，后端继续完成生成并持久化（断线不丢数据）
    """
    await _persist_message(db, user_id, session_id, "user", user_message, render_mode="component")
    history = await _load_history_messages(db, user_id, session_id)

    knowledge = ""
    if use_rag:
        yield f"data: {json.dumps({'rag_status': 'searching'}, ensure_ascii=False)}\n\n"
        knowledge, rag_error = await _query_knowledge(
            user_id, provider_config, user_message, mode,
            conversation_history=history,
        )
        if rag_error:
            yield f"data: {json.dumps({'rag_error': rag_error}, ensure_ascii=False)}\n\n"
        else:
            yield f"data: {json.dumps({'rag_status': 'done'}, ensure_ascii=False)}\n\n"

    from backend.services.component_service import stream_component_protocol_raw
    from backend.services import node_service
    from backend.schemas.component import ALLOWED_COMPONENT_TYPES

    raw_buffer = ""
    collected_components: list[dict] = []
    page_meta: dict = {}
    actions_list: list[dict] = []
    streamed_count = 0
    client_disconnected = False

    # 安全 yield：客户端断开时只打标记不丢异常
    def safe_yield(data: str):
        nonlocal client_disconnected
        if client_disconnected:
            return
        try:
            return data
        except GeneratorExit:
            client_disconnected = True

    try:
        async for piece in stream_component_protocol_raw(
            db, user_id, history, user_message, knowledge,
        ):
            if not piece:
                continue
            raw_buffer += piece
            if not client_disconnected:
                try:
                    yield f"data: {json.dumps({'streaming_raw': piece}, ensure_ascii=False)}\n\n"
                except (GeneratorExit, ConnectionError, OSError) as e:
                    client_disconnected = True
                    logger.info("客户端断开连接，后端继续生成中 session_id=%s", session_id)

            # 检测完整行（以 \n 分隔的 JSONL）
            lines = raw_buffer.split("\n")
            raw_buffer = lines.pop()

            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if obj.get("_meta_end"):
                    continue

                if "page_type" in obj and "title" in obj and "type" not in obj:
                    page_meta = obj
                    if not client_disconnected:
                        try:
                            yield f"data: {json.dumps({'partial_title': obj.get('title', ''), 'page_type': obj.get('page_type', '')}, ensure_ascii=False)}\n\n"
                        except (GeneratorExit, ConnectionError, OSError):
                            client_disconnected = True
                    continue

                comp_type = obj.get("type")
                if comp_type and comp_type in ALLOWED_COMPONENT_TYPES:
                    collected_components.append(obj)
                    streamed_count += 1
                    if not client_disconnected:
                        try:
                            yield f"data: {json.dumps({'partial_component': obj, 'index': streamed_count}, ensure_ascii=False)}\n\n"
                        except (GeneratorExit, ConnectionError, OSError):
                            client_disconnected = True
                    continue

                if "actions" in obj:
                    actions_list = obj.get("actions", [])
                    # 断线时才写 partial 结果（正常流程等全部完成再落库，避免重复）
                    if client_disconnected and collected_components:
                        partial_protocol = {
                            "page_type": page_meta.get("page_type", "analysis"),
                            "title": page_meta.get("title", ""),
                            "components": list(collected_components),
                            "actions": list(actions_list),
                            "meta": page_meta.get("meta", {}),
                            "_streaming_partial": True,
                        }
                        try:
                            await _persist_message(
                                db, user_id, session_id, "assistant",
                                json.dumps(partial_protocol, ensure_ascii=False),
                                render_mode="component",
                            )
                        except Exception:
                            logger.warning("断线 partial 落库失败 session_id=%s", session_id)

    except Exception as exc:
        logger.exception("流式生成组件协议失败 session_id=%s", session_id)
        if not client_disconnected:
            try:
                yield f"data: {json.dumps({'error': f'组件生成失败：{exc}'}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
            except (GeneratorExit, ConnectionError, OSError):
                pass
        return

    # 流结束后：持久化完整结果
    if not collected_components:
        if not client_disconnected:
            try:
                yield f"data: {json.dumps({'error': '未能解析到有效组件'}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
            except (GeneratorExit, ConnectionError, OSError):
                pass
        return

    full_protocol = {
        "page_type": page_meta.get("page_type", "analysis"),
        "title": page_meta.get("title", ""),
        "components": collected_components,
        "actions": actions_list,
        "meta": page_meta.get("meta", {}),
    }

    # 创建 UiNode
    node_id = None
    try:
        from backend.models import UiNode, UiNodeVersion
        import uuid as _uuid
        node = UiNode(
            id=_uuid.uuid4(),
            user_id=user_id,
            conversation_id=UUID(session_id),
            node_type="root",
        )
        db.add(node)
        await db.flush()

        # 查询最大版本号
        from sqlalchemy import select, func as sqlfunc
        r = await db.execute(
            select(sqlfunc.coalesce(sqlfunc.max(UiNodeVersion.version_no), 0))
            .where(UiNodeVersion.node_id == node.id)
        )
        next_version = r.scalar() + 1

        version = UiNodeVersion(
            id=_uuid.uuid4(),
            node_id=node.id,
            version_no=next_version,
            content_json=full_protocol,
            source="llm",
        )
        db.add(version)
        node.current_version_id = version.id
        await db.flush()
        await db.commit()
        node_id = str(node.id)
    except Exception as exc:
        logger.exception("创建组件节点失败 session_id=%s", session_id)
        await db.rollback()
        if not client_disconnected:
            try:
                yield f"data: {json.dumps({'error': f'节点创建失败：{exc}'}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
            except (GeneratorExit, ConnectionError, OSError):
                pass
        return

    # 落库 assistant 消息（完整结果覆盖之前的 partial）
    await _persist_message(
        db, user_id, session_id, "assistant",
        json.dumps(full_protocol, ensure_ascii=False),
        render_mode="component",
    )

    # 推最终事件（客户端断开时跳过，数据已在 DB 中）
    if not client_disconnected:
        try:
            yield f"data: {json.dumps({'node_id': node_id, 'streaming_done': True}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'component': full_protocol, 'node_id': node_id}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        except (GeneratorExit, ConnectionError, OSError):
            pass


@router.post("/stream")
async def chat_streaming(
    request: Request,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    流式对话接口（需登录）

    请求体：{ message, session_id?, use_rag?, mode?, images?, documents? }
    - 无 session_id 时自动创建会话
    - 自动读取历史消息让 AI 记住上下文
    - 供应商配置从 DB 动态读取（用户在设置页配置），无配置时兜底 .env
    - 默认集成 LightRAG 知识检索（可通过 use_rag=false 关闭）
    - 用户消息与 assistant 回复自动落库
    - images: base64 编码的图片数组（支持多模态视觉理解）
    - documents: {filename, content} 文档数组（自动提取文本作为上下文）
    """
    message = payload.get("message", "")
    use_rag = bool(payload.get("use_rag", False))
    mode = payload.get("mode", "hybrid")
    render_mode = payload.get("render_mode", "text")
    session_id = payload.get("session_id")
    images = payload.get("images", [])
    documents = payload.get("documents", [])

    if not message and not images and not documents:
        return JSONResponse(status_code=422, content={"message": "消息不能为空"})

    # 解析用户生效的供应商配置（唯一来源：数据库 ai_providers 表）
    provider_config = await resolve_provider_config(db, user.id)
    if not provider_config:
        return JSONResponse(
            status_code=400,
            content={"message": "未配置 AI 供应商，请在设置页面添加供应商配置。"},
        )

    # 处理文档：提取文本内容并追加到消息
    document_context = ""
    if documents:
        for doc in documents:
            try:
                text = extract_text_from_base64(doc["content"], doc["filename"])
                document_context += f"\n\n--- 文档: {doc['filename']} ---\n{text}\n--- 文档结束 ---"
            except Exception as exc:
                logger.warning("文档提取失败 filename=%s error=%s", doc["filename"], exc)
                document_context += f"\n\n[文档 {doc['filename']} 提取失败: {exc}]"

    if document_context:
        message = f"{message}\n\n{document_context}" if message else document_context.strip()

    # 构建附件列表（用于存储和多模态消息构建）
    attachments = []
    for img in images:
        attachments.append({
            "type": "image",
            "data": img,
        })
    for doc in documents:
        attachments.append({
            "type": "document",
            "filename": doc["filename"],
        })

    # 无会话则自动创建
    if not session_id:
        try:
            session = await conversation_service.create_session(db, user.id, message[:32])
            session_id = str(session.id)
        except Exception:
            logger.exception("创建会话失败")
            return JSONResponse(status_code=500, content={"message": "创建会话失败"})

    # 透传 session_id 给前端（通过首个 SSE 事件）
    async def wrapped():
        yield f"data: {json.dumps({'session_id': session_id}, ensure_ascii=False)}\n\n"
        if render_mode == "component":
            async for chunk in _component_streaming_with_persistence(
                message, session_id, user.id, db, provider_config, use_rag, mode,
            ):
                yield chunk
            return
        async for chunk in _streaming_with_persistence(
            message, session_id, user.id, db, provider_config, use_rag, mode,
            attachments=attachments if attachments else None,
        ):
            yield chunk

    return StreamingResponse(wrapped(), media_type="text/event-stream")


@router.get("/streaming/{session_id}")
async def get_active_streaming(
    session_id: UUID,
    user: User = Depends(get_current_user),
):
    """
    查询某会话下所有"进行中"的流式消息（从 Redis 读取）。

    使用场景：用户刷新页面 / 重新进入页面后调用，恢复未完成的 AI 回复内容。
    - 流式正常结束后后端清理 Redis key，此处返回空列表（历史已落库 PG，由 listMessages 拉取）
    - 流式仍在进行时，返回已累加的内容，前端可据此显示"生成中"状态并轮询更新
    - 流式因异常中断（key 未及时清理），30 分钟内仍可恢复，超时自动清理

    前端轮询约定：当返回的 items 数量减少（某条 stream_token 消失），说明该条流式已结束，
    应触发 listMessages 刷新历史以获取已落库的完整内容。
    """
    from backend.core.streaming_cache import list_active_streaming
    items = await list_active_streaming(str(session_id))
    return {"items": items, "count": len(items)}
