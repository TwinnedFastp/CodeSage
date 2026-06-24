/**
 * 会话列表管理：加载 / 切换 / 新建 / 删除 / 标题编辑 / AI 自动生成标题 / 归档
 */
import { ref, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as convApi from '@/api/conversations'
import type { ChatSession } from '@/types'

const SESSION_STORAGE_KEY = 'codesage_session_id'

export function useSessions() {
  const sessions = ref<ChatSession[]>([])
  // 初始值从 localStorage 读取，保证刷新后仍停留在上次选中的会话
  const currentSessionId = ref<string | null>(localStorage.getItem(SESSION_STORAGE_KEY))
  const loadingSessions = ref(false)
  const showArchived = ref(false)

  const activeSessions = computed(() => sessions.value.filter(s => !s.is_archived))
  const archivedSessions = computed(() => sessions.value.filter(s => s.is_archived))
  const visibleSessions = computed(() => showArchived.value ? archivedSessions.value : activeSessions.value)

  const currentSession = computed(() =>
    sessions.value.find(s => s.id === currentSessionId.value) || null
  )

  // 唯一持久化源：任何路径修改 currentSessionId 都自动同步到 localStorage，
  // 避免新建会话 / 后端 SSE 自动建会话时遗漏落盘，导致刷新后回退到第一个会话
  watch(currentSessionId, (id) => {
    if (id) localStorage.setItem(SESSION_STORAGE_KEY, id)
    else localStorage.removeItem(SESSION_STORAGE_KEY)
  })

  async function loadSessions() {
    loadingSessions.value = true
    try {
      // 同时加载活跃与归档会话，前端本地切片，避免切换视图时丢失当前选中
      const [active, archived] = await Promise.all([
        convApi.listSessions(50, 0, false),
        convApi.listSessions(50, 0, true),
      ])
      sessions.value = [...active, ...archived]
      // 当前会话已不在列表中（如被他端删除）则置空，localStorage 由 watch 自动清理
      if (currentSessionId.value && !sessions.value.find(s => s.id === currentSessionId.value)) {
        currentSessionId.value = null
      }
    } catch (err: any) {
      ElMessage.error(err.response?.data?.message || '加载会话列表失败')
    } finally {
      loadingSessions.value = false
    }
  }

  async function newConversation(): Promise<string | null> {
    const title = '新会话'
    try {
      const session = await convApi.createSession(title)
      sessions.value.unshift(session)
      showArchived.value = false
      // 仅修改 ref，持久化由顶部 watch 自动完成
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
      // 删除当前会话后置空，localStorage 由 watch 自动清理
      if (currentSessionId.value === id) {
        currentSessionId.value = null
      }
      ElMessage.success('会话已删除')
      return true
    } catch (err: any) {
      ElMessage.error(err.response?.data?.message || '删除会话失败')
      return false
    }
  }

  async function archiveSession(id: string): Promise<boolean> {
    try {
      const updated = await convApi.archiveSession(id)
      const idx = sessions.value.findIndex(s => s.id === id)
      if (idx !== -1) sessions.value[idx] = updated
      // 若归档的是当前选中会话，清空选中态，避免仍停留在已归档会话
      if (currentSessionId.value === id) {
        currentSessionId.value = null
      }
      ElMessage.success('会话已归档')
      return true
    } catch (err: any) {
      ElMessage.error(err.response?.data?.message || '归档失败')
      return false
    }
  }

  async function unarchiveSession(id: string): Promise<boolean> {
    try {
      const updated = await convApi.unarchiveSession(id)
      const idx = sessions.value.findIndex(s => s.id === id)
      if (idx !== -1) sessions.value[idx] = updated
      // 取消归档后切回活跃视图并选中该会话
      showArchived.value = false
      currentSessionId.value = id
      ElMessage.success('已取消归档')
      return true
    } catch (err: any) {
      ElMessage.error(err.response?.data?.message || '取消归档失败')
      return false
    }
  }

  function toggleArchived() {
    showArchived.value = !showArchived.value
    // 切换视图时如果当前会话不在新视图里，保留选中态也无妨，主区域仍可查看历史
  }

  function switchToActiveView() {
    showArchived.value = false
  }

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
  // 记录已生成过标题的会话，避免重复调用接口
  const titleGeneratedSessions = ref(new Set<string>())

  /** 后端 SSE 推送标题时直接更新本地（优先级最高，避免重复调接口） */
  function applyGeneratedTitle(sessionId: string, title: string) {
    if (!title) return
    const idx = sessions.value.findIndex(s => s.id === sessionId)
    if (idx !== -1) sessions.value[idx].title = title
    titleGeneratedSessions.value.add(sessionId)
  }

  async function tryAutoGenerateTitle(sessionId: string) {
    if (titleGeneratedSessions.value.has(sessionId)) return
    const session = sessions.value.find(s => s.id === sessionId)
    // 仅当标题仍为默认"新会话"时才生成，确保只在首次对话时触发
    if (!session || session.title !== '新会话') return

    try {
      const updated = await convApi.generateSessionTitle(sessionId)
      const idx = sessions.value.findIndex(s => s.id === sessionId)
      if (idx !== -1) sessions.value[idx].title = updated.title
      titleGeneratedSessions.value.add(sessionId)
    } catch {
      // 静默忽略（后端保底已处理）
    }
  }

  return {
    sessions, currentSessionId, currentSession, loadingSessions,
    showArchived, visibleSessions, activeSessions, archivedSessions,
    editingSessionId, editingTitle,
    loadSessions, newConversation, selectSession, deleteSession,
    archiveSession, unarchiveSession, toggleArchived, switchToActiveView,
    startEditTitle, cancelEditTitle, confirmEditTitle,
    tryAutoGenerateTitle, applyGeneratedTitle,
  }
}
