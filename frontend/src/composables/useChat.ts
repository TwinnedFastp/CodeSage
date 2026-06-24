/**
 * 聊天消息管理：加载历史 / 流式发送 / 滚动控制
 *
 * 会话持久化能力（防刷新/断连丢失）：
 * 1. 流式接收中刷新页面 → 从后端 Redis 恢复"进行中"的消息内容，并轮询续看生成
 * 2. beforeunload / visibilitychange(hidden) → 将输入框草稿保存到 localStorage
 * 3. 重新进入页面 → 自动恢复上次未发送的输入草稿
 * 4. 流式中断 → 后端继续生成并落库 PG，前端刷新后通过历史 + streaming 恢复完整内容
 */
import { ref, nextTick, watch, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import * as convApi from '@/api/conversations'
import { getActiveStreaming } from '@/api/chat'
import type { DisplayMessage, MessageAttachment, PendingImage, PendingDocument } from '@/types'

// 进行中流式消息的轮询间隔：1.5s 平衡实时性与请求量
const STREAMING_POLL_INTERVAL = 1500
// 草稿节流间隔：500ms，避免高频写入 localStorage
const DRAFT_SAVE_DEBOUNCE = 500
const DRAFT_PREFIX = 'codesage_draft:'

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

  // ---- 进行中流式消息轮询（刷新恢复用）----
  let streamingPollTimer: ReturnType<typeof setTimeout> | null = null

  function _stopStreamingPoll() {
    if (streamingPollTimer) {
      clearTimeout(streamingPollTimer)
      streamingPollTimer = null
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
   * 恢复进行中的流式消息：从后端 Redis 读取并追加到消息列表末尾。
   * 用户刷新页面 / 重新进入时调用，让"生成中"的内容不丢失。
   */
  async function _restoreActiveStreaming(sessionId: string) {
    _stopStreamingPoll()
    try {
      const res = await getActiveStreaming(sessionId)
      if (res.count === 0) return
      for (const item of res.items) {
        // 避免重复追加（loadMessages 刷新时可能残留）
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
      _startStreamingPoll(sessionId)
    } catch (err) {
      // 静默忽略（Redis 未启用 / 网络异常），不影响正常聊天
      console.debug('恢复流式消息失败', err)
    }
  }

  /**
   * 轮询进行中的流式消息，实时更新内容。
   * 当某条流式消失（后端已落库并清理 Redis），触发 loadMessages 刷新历史获取完整内容。
   */
  function _startStreamingPoll(sessionId: string) {
    _stopStreamingPoll()
    streamingPollTimer = setTimeout(async () => {
      try {
        const res = await getActiveStreaming(sessionId)
        const currentTokens = new Set(res.items.map(i => i.stream_token))
        // 更新已存在占位的内容
        for (const item of res.items) {
          const target = messages.value.find(m => m.id === `streaming-${item.stream_token}`)
          if (target) target.content = item.content
        }
        // 检测是否有流式结束：当前占位里有不在最新返回中的 token
        const placeholders = messages.value.filter(_isStreamingPlaceholder)
        const finished = placeholders.some(m => !currentTokens.has(m.id.replace('streaming-', '')))
        if (finished || res.count === 0) {
          // 有流式结束 → 移除占位 → 重新加载历史（含已落库的完整内容）
          _clearStreamingPlaceholders()
          await loadMessages(sessionId)
          return // loadMessages 末尾会重新触发 _restoreActiveStreaming
        }
        await scrollToBottom()
        _startStreamingPoll(sessionId)
      } catch (err) {
        console.debug('轮询流式消息失败', err)
        // 出错时继续轮询，避免恢复流程卡死
        _startStreamingPoll(sessionId)
      }
    }, STREAMING_POLL_INTERVAL)
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
  })

  onUnmounted(() => {
    window.removeEventListener('beforeunload', _handleBeforeUnload)
    document.removeEventListener('visibilitychange', _handleVisibilityChange)
    _stopStreamingPoll()
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
        if (m.attachments && m.attachments.length > 0) {
          msg.attachments = m.attachments
        }
        return msg
      })

      // 恢复进行中的流式消息（断连/刷新后，从 Redis 读取未完成的内容）
      await _restoreActiveStreaming(sessionId)

      if (messages.value.length === 0) messages.value = [{ ...WELCOME_MSG }]
      await scrollToBottom()

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
    messages.value = []
  }

  function showWelcome(text?: string) {
    messages.value = [{ ...WELCOME_MSG, content: text || WELCOME_MSG.content }]
  }

  async function scrollToBottom() {
    await nextTick()
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  }

  function adjustTextareaHeight(e: Event) {
    const target = e.target as HTMLTextAreaElement
    target.style.height = 'auto'
    target.style.height = Math.min(target.scrollHeight, 200) + 'px'
  }

  async function sendMessage(ensureSession: () => Promise<string | null>, useRag: boolean = false, mode: string = 'hybrid') {
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
    // 发送后清除草稿（已发出，无需恢复）
    _clearDraft(sessionId)
    const textarea = document.querySelector('textarea')
    if (textarea) textarea.style.height = 'auto'

    pendingImages.value = []
    pendingDocuments.value = []

    // 停止旧的恢复轮询，移除旧流式占位（避免与新流式混淆）
    _stopStreamingPoll()
    _clearStreamingPlaceholders()

    const assistantId = `a-${Date.now()}`
    messages.value.push({ id: assistantId, role: 'assistant', content: '', pending: true })
    isTyping.value = true
    await scrollToBottom()

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
            if (t && parsed.content) {
              if (t.content === RAG_SEARCHING_PLACEHOLDER) t.content = ''
              t.content += parsed.content
              await scrollToBottom()
            }
          } catch { /* 忽略非 JSON 帧（如不完整的行） */ }
        }
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
    sendMessage, adjustTextareaHeight, scrollToBottom,
    pendingImages, pendingDocuments,
    addPendingImage, removePendingImage,
    addPendingDocument, removePendingDocument,
  }
}
