/**
 * 聊天消息管理：加载历史 / 流式发送 / 滚动控制
 */
import { ref, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import * as convApi from '@/api/conversations'
import type { DisplayMessage } from '@/types'

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

  const WELCOME_MSG: DisplayMessage = {
    id: 'welcome',
    role: 'assistant',
    content: '你好。我是 CodeSage，你的代码工程师。有什么我可以帮你的吗？',
  }

  async function loadMessages(sessionId: string) {
    loadingMessages.value = true
    try {
      const list = await convApi.listMessages(sessionId, 100, 0)
      messages.value = list.map(m => {
        const role: 'user' | 'assistant' = m.role === 'user' ? 'user' : 'assistant'
        const base = {
          id: m.message_id,
          role,
        }

        // component 模式的消息：从 JSON 中提取可读文本作为 content 显示
        if (m.render_mode === 'component' && m.content) {
          try {
            const parsed = JSON.parse(m.content)
            // 提取标题或第一个 text_block 的内容
            const title = parsed.title || ''
            const firstText = parsed.components?.find((c: any) => c.type === 'text_block')
            const textContent = firstText?.props?.content || ''
            const summary = (title || textContent || '[生成式界面内容]') as string
            return { ...base, content: summary, _isComponent: true, _rawContent: m.content }
          } catch {
            // JSON 解析失败，截取前 200 字符显示
            return { ...base, content: m.content.slice(0, 200), _isComponent: true }
          }
        }

        // 普通 text 模式消息直接显示
        return { ...base, content: m.content }
      })

      if (messages.value.length === 0) messages.value = [{ ...WELCOME_MSG }]
      await scrollToBottom()
    } catch (err: any) {
      ElMessage.error(err.response?.data?.message || '加载消息失败')
    } finally {
      loadingMessages.value = false
    }
  }

  function clearMessages() {
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
    if (!userInput.value.trim() || isTyping.value) return

    let sessionId = currentSessionId()
    if (!sessionId) {
      sessionId = await ensureSession()
      if (!sessionId) return
    }

    const userText = userInput.value.trim()
    messages.value.push({ id: `u-${Date.now()}`, role: 'user', content: userText })
    userInput.value = ''
    const textarea = document.querySelector('textarea')
    if (textarea) textarea.style.height = 'auto'

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
        body: JSON.stringify({ message: userText, session_id: sessionId, use_rag: useRag, mode }),
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

  return {
    messages, userInput, isTyping, loadingMessages,
    loadMessages, clearMessages, showWelcome,
    sendMessage, adjustTextareaHeight, scrollToBottom,
  }
}
