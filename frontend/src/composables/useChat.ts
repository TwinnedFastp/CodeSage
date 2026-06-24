/**
 * 聊天消息管理：加载历史 / 流式发送 / 滚动控制
 *
 * 会话持久化能力（防刷新/断连丢失）：
 * 1. 流式接收中刷新页面 → 通过 SSE 断点续传从 Redis Stream 恢复剩余消息（实时推送，非轮询）
 * 2. beforeunload / visibilitychange(hidden) → 将输入框草稿 + 流式断点保存到 localStorage
 * 3. 重新进入页面 → 自动恢复上次未发送的输入草稿 + 建立断点续传连接
 * 4. 流式中断 → 后端继续生成并写 Stream，前端刷新后通过 XREAD BLOCK 实时续接
 */
import { ref, nextTick, watch, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import * as convApi from '@/api/conversations'
import { getActiveStreaming, continueStream, getStreamResumePoint, setStreamResumePoint, clearStreamResumePoint } from '@/api/chat'
import type { StreamMessage } from '@/api/chat'
import type { DisplayMessage, MessageAttachment, PendingImage, PendingDocument } from '@/types'

// 草稿节流间隔：500ms，避免高频写入 localStorage
const DRAFT_SAVE_DEBOUNCE = 500
const DRAFT_PREFIX = 'codesage_draft:'
// ---- 智能滚动：用户向上翻阅时暂停自动跟随 ----
const SCROLL_THRESHOLD = 120 // 距离底部多少 px 内视为"在底部"
let _shouldAutoScroll = true // 是否应自动跟随新内容滚动

export function useChat(
  currentSessionId: () => string | null,
  chatContainer: import('vue').Ref<HTMLElement | null>,
  onSessionCreated?: (id: string) => void,
  onStreamEnd?: (sessionId: string) => void,
  onTitleGenerated?: (sessionId: string, title: string) => void,
) {
  const auth = useAuthStore()
  const messages = ref<DisplayMessage[]>([])
  const userInput = ref('')
  const isTyping = ref(false)
  const loadingMessages = ref(false)
  const pendingImages = ref<PendingImage[]>([])
  const pendingDocuments = ref<PendingDocument[]>([])

  const WELCOME_MSG: DisplayMessage = {
    id: 'welcome',
    role: 'assistant',
    content: '你好。我是 CodeSage，你的代码工程师。有什么我可以帮你的吗？',
  }

// ---- 流式断点续传（SSE 长连接，替代旧版轮询）----
let continueController: AbortController | null = null

function _stopContinueStream() {
  if (continueController) {
    continueController.abort()
    continueController = null
  }
}

/** 判断某条消息是否为"进行中流式"占位（id 以 streaming- 开头） */
function _isStreamingPlaceholder(m: DisplayMessage): boolean {
  return m.id.startsWith('streaming-')
}

/** 移除所有流式占位消息（流式结束、切换会话、发送新消息时调用） */
function _clearStreamingPlaceholders() {
  messages.value = messages.value.filter(m => !_isStreamingPlaceholder(m))
}

/**
 * 通过 SSE 断点续传恢复进行中的流式消息（替代旧版轮询）。
 *
 * 用户刷新页面 / 重新进入时调用，建立长连接从 Redis Stream 实时接收剩余消息。
 * 行为：
 * 1. 先尝试快速恢复：GET /chat/streaming/{sid} 获取当前缓存快照（兜底）
 * 2. 然后建立 SSE 续传连接：GET /chat/stream/continue?last_msg_id=...
 * 3. 实时接收新 chunk 并渲染，直到收到 [DONE]
 */
async function _restoreActiveStreaming(sessionId: string) {
  _stopContinueStream()
  _stopStreamingPoll() // 兼容旧逻辑

  // 快速检查是否有活跃流式消息（兼容旧 String 缓存方案）
  try {
    const snapshot = await getActiveStreaming(sessionId)
    if (snapshot.count > 0) {
      for (const item of snapshot.items) {
        const exists = messages.value.find(m => m.id === `streaming-${item.stream_token}`)
        if (exists) {
          exists.content = item.content
          continue
        }
        messages.value.push({
          id: `streaming-${item.stream_token}`,
          role: 'assistant',
          content: item.content,
          pending: true,
        })
      }
      await scrollToBottom()
    }
  } catch {
    // 忽略快照查询失败，继续尝试 SSE 续传
  }

  // 建立 SSE 断点续传连接
  const lastMsgId = getStreamResumePoint(sessionId) || '0-0'
  const assistantId = `streaming-resume-${Date.now()}`

  // 添加恢复状态提示（如果还没有内容）
  const existingContent = messages.value.filter(_isStreamingPlaceholder).some(m => m.content.length > 0)
  if (!existingContent && messages.value.find(m => m.id === assistantId)?.content === undefined) {
    messages.value.push({
      id: assistantId,
      role: 'assistant',
      content: '',
      pending: true,
      _isResuming: true, // 标记为"恢复中"状态
    })
    await scrollToBottom()
  }

  continueController = continueStream(
    sessionId,
    lastMsgId,
    // onMessage: 收到新 chunk
    async (msg: StreamMessage) => {
      // 更新断点位置到 localStorage
      setStreamResumePoint(sessionId, msg.msgId)

      if (msg.type === 'error') {
        const target = messages.value.find(m => m.id === assistantId)
        if (target) {
          target.content = msg.content || '生成过程中发生错误'
          target.pending = false
          delete target._isResuming
        }
        return
      }

      if (msg.type !== 'content') return

      // 找到或创建目标消息气泡
      let target = messages.value.find(m => m.id === assistantId)
      if (!target) {
        target = { id: assistantId, role: 'assistant', content: '', pending: true }
        messages.value.push(target)
      }

      // 移除"恢复中"标记，开始显示实际内容
      delete target._isResuming
      target.content += msg.content
      await scrollToBottom()
    },
    // onDone: 流式结束
    async () => {
      _stopContinueStream()
      clearStreamResumePoint(sessionId)

      // 移除占位，重新从 PG 加载最终态（保证数据一致性）
      _clearStreamingPlaceholders()
      await loadMessages(sessionId)

      if (onStreamEnd) onStreamEnd(sessionId)
    },
    // onError: 连接错误
    async (err: string) => {
      console.debug('断点续传连接异常', err)
      _stopContinueStream()

      // 降级：移除恢复占位，让用户看到已加载的历史消息
      _clearStreamingPlaceholders()
    }
  )
}

// ---- 旧版轮询兼容层（已废弃，保留用于降级兜底）----
let streamingPollTimer: ReturnType<typeof setTimeout> | null = null

function _stopStreamingPoll() {
  if (streamingPollTimer) {
    clearTimeout(streamingPollTimer)
    streamingPollTimer = null
  }
}

  // ---- 输入草稿持久化（防刷新丢失输入）----
  let draftSaveTimer: ReturnType<typeof setTimeout> | null = null

  function _draftKey(sessionId: string): string {
    return `${DRAFT_PREFIX}${sessionId}`
  }

  function _saveDraft(sessionId: string) {
    if (!sessionId) return
    try {
      localStorage.setItem(_draftKey(sessionId), userInput.value)
    } catch { /* localStorage 配额满等，静默忽略 */ }
  }

  function _scheduleDraftSave(sessionId: string) {
    if (!sessionId) return
    if (draftSaveTimer) clearTimeout(draftSaveTimer)
    draftSaveTimer = setTimeout(() => _saveDraft(sessionId), DRAFT_SAVE_DEBOUNCE)
  }

  function _loadDraft(sessionId: string) {
    try {
      userInput.value = localStorage.getItem(_draftKey(sessionId)) || ''
    } catch {
      userInput.value = ''
    }
  }

  function _clearDraft(sessionId: string) {
    try {
      localStorage.removeItem(_draftKey(sessionId))
    } catch { /* */ }
  }

  // ---- 生命周期 + 页面卸载保护 ----
  function _handleBeforeUnload() {
    // 页面关闭/刷新前同步保存草稿（同步 localStorage 写入在 beforeunload 中可靠）
    const sid = currentSessionId()
    if (sid) _saveDraft(sid)
  }

  function _handleVisibilityChange() {
    // 页面切到后台（切标签页/最小化）时保存草稿
    if (document.visibilityState === 'hidden') {
      const sid = currentSessionId()
      if (sid) _saveDraft(sid)
    }
  }

  // 监听输入变化，节流保存草稿（绑定当前会话）
  watch(userInput, () => {
    const sid = currentSessionId()
    if (sid) _scheduleDraftSave(sid)
  })

  onMounted(() => {
    window.addEventListener('beforeunload', _handleBeforeUnload)
    document.addEventListener('visibilitychange', _handleVisibilityChange)
    // 监听用户手动滚动：向上翻时暂停自动跟随，滚回底部附近时恢复
    chatContainer.value?.addEventListener('scroll', () => {
      _shouldAutoScroll = _isNearBottom()
    }, { passive: true })
  })

  onUnmounted(() => {
    window.removeEventListener('beforeunload', _handleBeforeUnload)
    document.removeEventListener('visibilitychange', _handleVisibilityChange)
    _stopStreamingPoll()
    _stopContinueStream()
    const sid = currentSessionId()
    if (sid) _saveDraft(sid)
  })

  async function loadMessages(sessionId: string) {
    loadingMessages.value = true
    _stopStreamingPoll()
    try {
      const list = await convApi.listMessages(sessionId, 100, 0)
      messages.value = list.map(m => {
        const role: 'user' | 'assistant' = m.role === 'user' ? 'user' : 'assistant'
        const base = {
          id: m.message_id,
          role,
        }

        if (m.render_mode === 'component' && m.content) {
          try {
            const parsed = JSON.parse(m.content)
            const title = parsed.title || ''
            const firstText = parsed.components?.find((c: any) => c.type === 'text_block')
            const textContent = firstText?.props?.content || ''
            const summary = (title || textContent || '[生成式界面内容]') as string
            return { ...base, content: summary, _isComponent: true, _rawContent: m.content }
          } catch {
            return { ...base, content: m.content.slice(0, 200), _isComponent: true }
          }
        }

        const msg: DisplayMessage = { ...base, content: m.content }
        if (m.reasoning) {
          msg.thinkingRaw = m.reasoning
          msg.thinkingDone = true
        }
        if (m.attachments && m.attachments.length > 0) {
          msg.attachments = m.attachments
        }
        return msg
      })

      // 恢复进行中的流式消息（断连/刷新后，从 Redis 读取未完成的内容）
      await _restoreActiveStreaming(sessionId)

      if (messages.value.length === 0) messages.value = [{ ...WELCOME_MSG }]
      await forceScrollToBottom() // 切换会话/加载历史 → 强制到底

      // 恢复上次未发送的输入草稿
      _loadDraft(sessionId)
    } catch (err: any) {
      ElMessage.error(err.response?.data?.message || '加载消息失败')
    } finally {
      loadingMessages.value = false
    }
  }

  function clearMessages() {
    _stopStreamingPoll()
    _stopContinueStream()
    messages.value = []
  }

  function showWelcome(text?: string) {
    messages.value = [{ ...WELCOME_MSG, content: text || WELCOME_MSG.content }]
  }

  /** 判断滚动容器是否在底部附近 */
  function _isNearBottom(): boolean {
    const el = chatContainer.value
    if (!el) return true
    return el.scrollHeight - el.scrollTop - el.clientHeight < SCROLL_THRESHOLD
  }

  /**
   * 智能滚动：
   * - force=true → 强制滚到底部（用户发消息、切换会话）
   * - force=false → 仅在底部附近时才跟随新内容（用户往上翻时不受打扰）
   */
  async function scrollToBottom(force = false) {
    await nextTick()
    if (!chatContainer.value) return
    if (force || _shouldAutoScroll) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  }

  /** 强制滚到底 + 恢复自动跟随（用户主动操作后调用） */
  async function forceScrollToBottom() {
    _shouldAutoScroll = true
    await scrollToBottom(true)
  }

  function adjustTextareaHeight(e: Event) {
    const target = e.target as HTMLTextAreaElement
    target.style.height = 'auto'
    target.style.height = Math.min(target.scrollHeight, 200) + 'px'
  }

  async function sendMessage(ensureSession: () => Promise<string | null>, useRag: boolean = false, mode: string = 'hybrid', preferredProviderId?: number | null) {
    if (!userInput.value.trim() && pendingImages.value.length === 0 && pendingDocuments.value.length === 0) return
    if (isTyping.value) return

    let sessionId = currentSessionId()
    if (!sessionId) {
      sessionId = await ensureSession()
      if (!sessionId) return
    }

    const userText = userInput.value.trim()

    const attachments: MessageAttachment[] = []
    const imagesBase64: string[] = []
    for (const img of pendingImages.value) {
      imagesBase64.push(img.dataUrl)
      attachments.push({ type: 'image', data: img.dataUrl })
    }
    const docsPayload: { filename: string; content: string }[] = []
    for (const doc of pendingDocuments.value) {
      docsPayload.push({ filename: doc.filename, content: doc.content })
      attachments.push({ type: 'document', filename: doc.filename })
    }

    messages.value.push({
      id: `u-${Date.now()}`,
      role: 'user',
      content: userText,
      attachments: attachments.length > 0 ? attachments : undefined,
    })
    userInput.value = ''
    // 发送后清除草稿和旧的续传断点（已发出，无需恢复）
    _clearDraft(sessionId)
    clearStreamResumePoint(sessionId)
    const textarea = document.querySelector('textarea')
    if (textarea) textarea.style.height = 'auto'

    pendingImages.value = []
    pendingDocuments.value = []

    // 停止旧的恢复连接/轮询，移除旧流式占位（避免与新流式混淆）
    _stopContinueStream()
    _stopStreamingPoll()
    _clearStreamingPlaceholders()

    const assistantId = `a-${Date.now()}`
    messages.value.push({ id: assistantId, role: 'assistant', content: '', pending: true })
    isTyping.value = true
    await forceScrollToBottom() // 发消息后强制到底

    try {
      const token = auth.accessToken
      const response = await fetch('/api/v1/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          message: userText,
          session_id: sessionId,
          use_rag: useRag,
          mode,
          images: imagesBase64.length > 0 ? imagesBase64 : undefined,
          documents: docsPayload.length > 0 ? docsPayload : undefined,
          preferred_provider_id: preferredProviderId || undefined,
        }),
      })
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      if (!response.body) throw new Error('无响应流')

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      const target = messages.value.find(m => m.id === assistantId)
      if (target) target.pending = false

      let backendSessionId: string | null = null
      // 跨 chunk 的行缓冲：SSE 事件可能被拆到多次 read，必须累积后按 \n 切行
      let lineBuffer = ''
      let ragNotified = false  // 避免重复弹 rag_error 提示
      // 占位文本：RAG 检索期间显示，收到真正的 content 后清空
      const RAG_SEARCHING_PLACEHOLDER = '正在检索知识库…'

      while (true) {
        const { value, done } = await reader.read()
        if (done) break
        // stream: true 保证 UTF-8 多字节字符（中文）跨 chunk 正确解码，不产生乱码
        lineBuffer += decoder.decode(value, { stream: true })
        const lines = lineBuffer.split('\n')
        // 最后一段可能不完整（无换行符结尾），留到下次 read 再处理
        lineBuffer = lines.pop() || ''
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const data = line.slice(6)
          if (data === '[DONE]') continue
          try {
            const parsed = JSON.parse(data)
            // 1. 首个事件：后端回传 session_id（无 session_id 时自动创建的场景）
            if (parsed.session_id && !backendSessionId) {
              backendSessionId = parsed.session_id as string
              if (backendSessionId !== sessionId && onSessionCreated) {
                onSessionCreated(backendSessionId)
              }
              continue
            }
            // 2. 后端推送的 AI 生成标题
            if (parsed.title && parsed.session_id && onTitleGenerated) {
              onTitleGenerated(parsed.session_id as string, parsed.title as string)
              continue
            }
            // 3. RAG 检索状态反馈：searching 时显示占位，done 时清空
            if (parsed.rag_status === 'searching') {
              const t = messages.value.find(m => m.id === assistantId)
              if (t) t.content = RAG_SEARCHING_PLACEHOLDER
              continue
            }
            if (parsed.rag_status === 'done') {
              const t = messages.value.find(m => m.id === assistantId)
              if (t && t.content === RAG_SEARCHING_PLACEHOLDER) t.content = ''
              continue
            }
            // 4. RAG 错误透传：提示用户但不中断对话（降级为纯对话）
            if (parsed.rag_error && !ragNotified) {
              ragNotified = true
              ElMessage.warning(parsed.rag_error)
              const t = messages.value.find(m => m.id === assistantId)
              if (t && t.content === RAG_SEARCHING_PLACEHOLDER) t.content = ''
              continue
            }
            // 5. LLM 流式内容：累加到 assistant 气泡
            const t = messages.value.find(m => m.id === assistantId)
            if (t) {
              if (parsed.content) {
                if (t.content === RAG_SEARCHING_PLACEHOLDER) t.content = ''
                t.content += parsed.content
                await scrollToBottom()
              }
              // 推理模型的思考过程：单独折叠显示
              if (parsed.reasoning) {
                t.thinkingRaw = (t.thinkingRaw || '') + parsed.reasoning
                t.thinkingDone = false
                await scrollToBottom()
              }
            }
          } catch { /* 忽略非 JSON 帧（如不完整的行） */ }
        }
      }

      // 流式结束：标记思考过程已完成（如果本次存在 thinkingRaw）
      const finalAssistant = messages.value.find(m => m.id === assistantId)
      if (finalAssistant && finalAssistant.thinkingRaw) {
        finalAssistant.thinkingDone = true
      }

      if (onStreamEnd) onStreamEnd(backendSessionId || sessionId)
    } catch (err: any) {
      const t = messages.value.find(m => m.id === assistantId)
      if (t) {
        t.pending = false
        t.content = '抱歉，连接到 CodeSage 服务器时发生了错误。请确保后端服务正在运行。'
      }
      console.error('发送请求失败', err)
    } finally {
      isTyping.value = false
    }
  }

  function addPendingImage(dataUrl: string) {
    pendingImages.value.push({ id: `img-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`, dataUrl })
  }

  function removePendingImage(id: string) {
    pendingImages.value = pendingImages.value.filter(img => img.id !== id)
  }

  function addPendingDocument(filename: string, content: string) {
    pendingDocuments.value.push({ id: `doc-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`, filename, content })
  }

  function removePendingDocument(id: string) {
    pendingDocuments.value = pendingDocuments.value.filter(doc => doc.id !== id)
  }

  return {
    messages, userInput, isTyping, loadingMessages,
    loadMessages, clearMessages, showWelcome,
    sendMessage, adjustTextareaHeight, scrollToBottom, forceScrollToBottom,
    pendingImages, pendingDocuments,
    addPendingImage, removePendingImage,
    addPendingDocument, removePendingDocument,
  }
}
