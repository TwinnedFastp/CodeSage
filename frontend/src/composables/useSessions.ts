/**
 * 会话列表管理：加载 / 切换 / 新建 / 删除 / 标题编辑 / AI 自动生成标题
 */
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as convApi from '@/api/conversations'
import type { ChatSession } from '@/types'

export function useSessions() {
  const sessions = ref<ChatSession[]>([])
  const currentSessionId = ref<string | null>(null)
  const loadingSessions = ref(false)

  const currentSession = computed(() =>
    sessions.value.find(s => s.id === currentSessionId.value) || null
  )

  async function loadSessions() {
    loadingSessions.value = true
    try {
      sessions.value = await convApi.listSessions(50, 0)
    } catch (err: any) {
      ElMessage.error(err.response?.data?.message || '加载会话列表失败')
    } finally {
      loadingSessions.value = false
    }
  }

  async function newConversation(): Promise<string | null> {
    const title = `会话 · ${new Date().toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })}`
    try {
      const session = await convApi.createSession(title)
      sessions.value.unshift(session)
      currentSessionId.value = session.id
      return session.id
    } catch (err: any) {
      ElMessage.error(err.response?.data?.message || '创建会话失败')
      return null
    }
  }

  function selectSession(id: string) {
    if (currentSessionId.value === id) return false
    currentSessionId.value = id
    return true
  }

  async function deleteSession(id: string): Promise<boolean> {
    try {
      await ElMessageBox.confirm('删除该会话将同时清除所有消息，确定继续吗？', '删除会话', {
        type: 'warning',
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        confirmButtonClass: 'el-button--danger',
      })
    } catch {
      return false
    }
    try {
      await convApi.deleteSession(id)
      sessions.value = sessions.value.filter(s => s.id !== id)
      if (currentSessionId.value === id) currentSessionId.value = null
      ElMessage.success('会话已删除')
      return true
    } catch (err: any) {
      ElMessage.error(err.response?.data?.message || '删除会话失败')
      return false
    }
  }

  // ---- 标题内联编辑 ----
  const editingSessionId = ref<string | null>(null)
  const editingTitle = ref('')

  function startEditTitle(sessionId: string, currentTitle: string) {
    editingSessionId.value = sessionId
    editingTitle.value = currentTitle
  }

  function cancelEditTitle() {
    editingSessionId.value = null
    editingTitle.value = ''
  }

  async function confirmEditTitle(sessionId: string) {
    const trimmed = editingTitle.value.trim()
    if (!trimmed) {
      ElMessage.warning('标题不能为空')
      return
    }
    try {
      const updated = await convApi.updateSession(sessionId, { title: trimmed })
      const idx = sessions.value.findIndex(s => s.id === sessionId)
      if (idx !== -1) sessions.value[idx].title = updated.title
      ElMessage.success('标题已更新')
    } catch (err: any) {
      ElMessage.error(err.response?.data?.message || '更新失败')
    } finally {
      cancelEditTitle()
    }
  }

  // ---- AI 自动生成标题 ----
  const titleGeneratedSessions = ref(new Set<string>())

  async function tryAutoGenerateTitle(sessionId: string) {
    if (titleGeneratedSessions.value.has(sessionId)) return
    const session = sessions.value.find(s => s.id === sessionId)
    if (!session || !session.title?.startsWith('会话 ·')) return

    try {
      const updated = await convApi.generateSessionTitle(sessionId)
      const idx = sessions.value.findIndex(s => s.id === sessionId)
      if (idx !== -1) sessions.value[idx].title = updated.title
      titleGeneratedSessions.value.add(sessionId)
    } catch {
      // 静默忽略
    }
  }

  return {
    sessions, currentSessionId, currentSession, loadingSessions,
    editingSessionId, editingTitle,
    loadSessions, newConversation, selectSession, deleteSession,
    startEditTitle, cancelEditTitle, confirmEditTitle,
    tryAutoGenerateTitle,
  }
}
