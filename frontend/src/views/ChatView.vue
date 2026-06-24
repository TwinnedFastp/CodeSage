<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ChatDotRound, Operation, Plus, User as UserIcon, Monitor, Setting,
  Fold, Expand, Promotion, SwitchButton, Collection, Files, Cpu, Coin,
  Picture, Document, Close,
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useResponsive } from '@/composables/useResponsive'
import { useSessions } from '@/composables/useSessions'
import { useChat } from '@/composables/useChat'
import { useRag } from '@/composables/useRag'
import KnowledgePanel from '@/components/KnowledgePanel.vue'
// 复用单条会话项组件，避免桌面端/移动端两处列表重复代码
import SessionListItem from '@/components/SessionListItem.vue'
import GenerativePanel from '@/features/generative-ui/GenerativePanel.vue'
import { marked } from 'marked'

// 配置 marked 渲染选项
marked.setOptions({
  breaks: true,       // 支持换行符
  gfm: true,          // GitHub 风格 Markdown（表格、任务列表等）
})

/** 将 Markdown 文本转为 HTML */
function renderMarkdown(text: string): string {
  if (!text) return ''
  try {
    const html = marked.parse(text) as string
    return typeof html === 'string' ? html : String(html)
  } catch {
    // 解析失败时转义 HTML 后原样返回
    return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  }
}

const router = useRouter()
const auth = useAuthStore()

const { isMobile, isSidebarCollapse, drawerVisible } = useResponsive()

const {
  currentSessionId, currentSession, loadingSessions,
  showArchived, visibleSessions, activeSessions, archivedSessions,
  editingSessionId, editingTitle,
  loadSessions, newConversation: createSession, selectSession, deleteSession,
  archiveSession, unarchiveSession, toggleArchived, switchToActiveView,
  startEditTitle, cancelEditTitle, confirmEditTitle,
  tryAutoGenerateTitle, applyGeneratedTitle,
} = useSessions()

const chatContainer = ref<HTMLElement | null>(null)

const {
  messages, userInput, isTyping, loadingMessages,
  loadMessages, clearMessages, showWelcome,
  sendMessage: doSend, adjustTextareaHeight,
  pendingImages, pendingDocuments,
  addPendingImage, removePendingImage,
  addPendingDocument, removePendingDocument,
} = useChat(
  () => currentSessionId.value,
  chatContainer,
  (id) => { currentSessionId.value = id; loadSessions() },
  (id) => { tryAutoGenerateTitle(id).catch(() => {}) },
  (id, title) => { applyGeneratedTitle(id, title) },
)

// ---- RAG 知识库 ----
const {
  ragReady, ragMode, ragActive,
  documents, loadingDocs, uploading, knowledgePanelVisible,
  loadDocuments, uploadDocument, uploadFile, removeDocument, resetKnowledge, openKnowledgePanel,
} = useRag()

// ---- 初始化 ----
;(async () => {
  await loadSessions()
  if (currentSessionId.value) {
    await loadMessages(currentSessionId.value)
  } else if (activeSessions.value.length > 0) {
    selectSession(activeSessions.value[0].id)
    await loadMessages(activeSessions.value[0].id)
  } else {
    showWelcome('你好。我是 CodeSage，你的代码工程师。点击「New Conversation」开始我们的第一段对话。')
  }
})()

// ---- 用户菜单 ----
const userMenuVisible = ref(false)

async function onLogout() {
  userMenuVisible.value = false
  await auth.logout()
  ElMessage.success('已登出')
  router.push('/login')
}

function goToSettings() {
  userMenuVisible.value = false
  router.push('/settings')
}

function goToDatabaseAdmin() {
  userMenuVisible.value = false
  drawerVisible.value = false
  router.push('/database-admin')
}

// ---- 用户信息显示（左下角 + 移动端抽屉底部）----
const displayUsername = computed(() => auth.user?.username || auth.user?.email || 'CodeSage 用户')
const displayAvatarUrl = computed(() => {
  const url = auth.user?.avatar_url
  // 加时间戳破浏览器缓存，确保头像更新后立即刷新
  return url ? (url.includes('?') ? `${url}&_t=${Date.now()}` : `${url}?_t=${Date.now()}`) : ''
})

// ---- 包装函数：供模板调用 ----
async function newConversation() {
  const id = await createSession()
  if (id) { clearMessages(); await loadMessages(id) }
}

async function onSelectSession(id: string) {
  if (!selectSession(id)) return
  drawerVisible.value = false
  clearMessages()
  await loadMessages(id)
}

async function onDeleteCurrent() {
  if (!currentSessionId.value) return
  const ok = await deleteSession(currentSessionId.value)
  if (ok) {
    if (visibleSessions.value.length > 0) {
      await onSelectSession(visibleSessions.value[0].id)
    } else {
      clearMessages()
      showWelcome('你好。我是 CodeSage，你的代码工程师。点击「New Conversation」开始新的对话。')
    }
  }
}

async function onArchive(id: string) {
  await archiveSession(id)
}

async function onUnarchive(id: string) {
  await unarchiveSession(id)
  // 取消归档后，loadMessages 当前会话
  await loadMessages(id)
}

async function onDeleteSession(id: string) {
  const ok = await deleteSession(id)
  if (ok && currentSessionId.value === id) {
    if (visibleSessions.value.length > 0) {
      await onSelectSession(visibleSessions.value[0].id)
    } else {
      clearMessages()
      showWelcome('你好。我是 CodeSage，你的代码工程师。点击「New Conversation」开始新的对话。')
    }
  }
}

function handleTitleKeydown(e: KeyboardEvent, sessionId: string) {
  if (e.key === 'Enter') { e.preventDefault(); confirmEditTitle(sessionId) }
  else if (e.key === 'Escape') { e.preventDefault(); cancelEditTitle() }
}

async function onSend() {
  await doSend(async () => await createSession(), ragActive.value, ragMode.value === 'off' ? 'hybrid' : ragMode.value)
}

// RAG 模式切换选项（对齐 LightRAG-main 原生支持的查询模式）
// value 类型与 useRag.ts 中 ragMode 的非 'off' 子集对齐，避免 as any 强转
const ragModeOptions: Array<{ value: 'naive' | 'local' | 'global' | 'hybrid' | 'mix'; label: string }> = [
  { value: 'mix', label: '混合+' },
  { value: 'hybrid', label: '混合' },
  { value: 'local', label: '局部' },
  { value: 'global', label: '全局' },
  { value: 'naive', label: '朴素' },
]

// ---- 生成式 UI 模式切换 ----
const renderMode = ref<'text' | 'component'>('text')

function onGenSessionCreated(id: string) {
  currentSessionId.value = id
  loadSessions()
}

// ---- 图片/文档附件上传 ----
const imagePreviewVisible = ref(false)
const imagePreviewUrl = ref('')
const imageInputRef = ref<HTMLInputElement | null>(null)
const documentInputRef = ref<HTMLInputElement | null>(null)

const ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
const ALLOWED_DOC_TYPES = ['.pdf', '.docx', '.txt', '.md']
const MAX_IMAGE_SIZE = 10 * 1024 * 1024
const MAX_DOC_SIZE = 20 * 1024 * 1024

function previewImage(dataUrl: string) {
  imagePreviewUrl.value = dataUrl
  imagePreviewVisible.value = true
}

function triggerImageSelect() {
  imageInputRef.value?.click()
}

function triggerDocSelect() {
  documentInputRef.value?.click()
}

function onImageFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  const files = input.files
  if (!files) return
  for (const file of Array.from(files)) {
    if (!ALLOWED_IMAGE_TYPES.includes(file.type)) {
      ElMessage.warning(`不支持的图片格式: ${file.name}`)
      continue
    }
    if (file.size > MAX_IMAGE_SIZE) {
      ElMessage.warning(`图片过大: ${file.name}（最大 10MB）`)
      continue
    }
    const reader = new FileReader()
    reader.onload = () => {
      addPendingImage(reader.result as string)
    }
    reader.readAsDataURL(file)
  }
  input.value = ''
}

function onDocFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  const files = input.files
  if (!files) return
  for (const file of Array.from(files)) {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase()
    if (!ALLOWED_DOC_TYPES.includes(ext)) {
      ElMessage.warning(`不支持的文档格式: ${file.name}（支持 PDF/DOCX/TXT/MD）`)
      continue
    }
    if (file.size > MAX_DOC_SIZE) {
      ElMessage.warning(`文档过大: ${file.name}（最大 20MB）`)
      continue
    }
    const reader = new FileReader()
    reader.onload = () => {
      addPendingDocument(file.name, reader.result as string)
    }
    reader.readAsDataURL(file)
  }
  input.value = ''
}

// 粘贴图片：支持在输入框直接 Ctrl+V 粘贴剪贴板图片，自动添加为待发送附件
function onPasteImage(e: ClipboardEvent) {
  const items = e.clipboardData?.items
  if (!items) return
  let hasImage = false
  for (const item of Array.from(items)) {
    if (item.type.startsWith('image/')) {
      const file = item.getAsFile()
      if (!file) continue
      if (!ALLOWED_IMAGE_TYPES.includes(file.type)) {
        ElMessage.warning(`不支持的图片格式: ${file.type}（支持 JPG/PNG/GIF/WebP）`)
        continue
      }
      if (file.size > MAX_IMAGE_SIZE) {
        ElMessage.warning(`图片过大（最大 10MB）`)
        continue
      }
      hasImage = true
      const reader = new FileReader()
      reader.onload = () => {
        addPendingImage(reader.result as string)
      }
      reader.readAsDataURL(file)
    }
  }
  // 含图片时阻止默认行为，避免图片被当作二进制文本粘贴到输入框
  if (hasImage) e.preventDefault()
}

const canSend = computed(() => {
  return (userInput.value.trim() || pendingImages.value.length > 0 || pendingDocuments.value.length > 0) && !isTyping.value
})
</script>

<template>
  <div class="flex h-screen w-screen bg-[#FAFAFA] text-[#111111] overflow-hidden antialiased font-sans selection:bg-[#EAE8E0]">

    <!-- 桌面端侧边栏 -->
    <aside
      v-if="!isMobile"
      :class="['bg-[#F3F2EE] transition-all duration-500 ease-[cubic-bezier(0.16,1,0.3,1)] flex flex-col', isSidebarCollapse ? 'w-[80px]' : 'w-[280px]']"
    >
      <div class="p-6 flex items-center justify-between h-20">
        <div v-if="!isSidebarCollapse" class="flex items-center gap-3 font-semibold text-lg tracking-tight">
          <div class="w-6 h-6 bg-[#111111] rounded-full flex items-center justify-center text-[#F3F2EE]">
            <el-icon :size="14"><ChatDotRound /></el-icon>
          </div>
          <span>CodeSage</span>
        </div>
        <button @click="isSidebarCollapse = !isSidebarCollapse" class="p-2 rounded-full hover:bg-[#E8E6E1] transition-colors text-[#555555] mx-auto">
          <el-icon :size="18"><component :is="isSidebarCollapse ? Expand : Fold" /></el-icon>
        </button>
      </div>

      <div class="px-5 mb-3 mt-1">
        <!-- 顶部小图标目录：快速进入聊天 / 归档 / 数据库 / 设置 -->
        <div class="grid grid-cols-4 gap-1.5 p-1.5 rounded-xl bg-white border border-[#E8E6E1] shadow-[0_2px_12px_rgb(0,0,0,0.03)]">
          <button
            @click="switchToActiveView"
            :class="['flex flex-col items-center justify-center gap-0.5 py-1.5 rounded-lg transition-colors', !showArchived ? 'bg-[#111] text-white' : 'text-[#666] hover:bg-[#F3F2EE] hover:text-[#111]']"
            title="当前聊天"
          >
            <el-icon :size="13"><ChatDotRound /></el-icon>
            <span v-if="!isSidebarCollapse" class="text-[9px] leading-tight">聊天</span>
          </button>
          <button
            @click="toggleArchived"
            :class="['flex flex-col items-center justify-center gap-0.5 py-1.5 rounded-lg transition-colors', showArchived ? 'bg-[#111] text-white' : 'text-[#666] hover:bg-[#F3F2EE] hover:text-[#111]']"
            title="已归档会话"
          >
            <el-icon :size="13"><Files /></el-icon>
            <span v-if="!isSidebarCollapse" class="text-[9px] leading-tight">归档</span>
          </button>
          <button @click="goToDatabaseAdmin" class="flex flex-col items-center justify-center gap-0.5 py-1.5 rounded-lg text-[#666] hover:bg-[#F3F2EE] hover:text-[#111] transition-colors" title="数据库管理">
            <el-icon :size="13"><Coin /></el-icon>
            <span v-if="!isSidebarCollapse" class="text-[9px] leading-tight">数据库</span>
          </button>
          <button @click="goToSettings" class="flex flex-col items-center justify-center gap-0.5 py-1.5 rounded-lg text-[#666] hover:bg-[#F3F2EE] hover:text-[#111] transition-colors" title="系统设置">
            <el-icon :size="13"><Setting /></el-icon>
            <span v-if="!isSidebarCollapse" class="text-[9px] leading-tight">设置</span>
          </button>
        </div>
      </div>

      <div class="px-5 mb-6">
        <button
          v-if="!showArchived"
          class="w-full h-11 bg-[#111111] hover:bg-[#333333] text-white rounded-full flex items-center justify-center gap-2 transition-all duration-300 shadow-sm"
          @click="newConversation"
        >
          <el-icon><Plus /></el-icon>
          <span v-if="!isSidebarCollapse" class="text-sm font-medium">New Conversation</span>
        </button>
        <button
          v-else
          class="w-full h-11 bg-[#F3F2EE] hover:bg-[#E8E6E1] text-[#111111] border border-[#E8E6E1] rounded-full flex items-center justify-center gap-2 transition-all duration-300"
          @click="switchToActiveView"
        >
          <el-icon><ChatDotRound /></el-icon>
          <span v-if="!isSidebarCollapse" class="text-sm font-medium">返回活跃会话</span>
        </button>
      </div>

      <nav class="flex-1 overflow-y-auto px-3 py-2 space-y-1 custom-scrollbar">
        <div class="flex items-center justify-between px-3 mb-2">
          <span class="text-[11px] font-semibold text-[#999999] uppercase tracking-wider">{{ showArchived ? '已归档' : '会话' }}</span>
          <span v-if="showArchived" class="text-[11px] text-[#999999]">{{ archivedSessions.length }} 个</span>
        </div>
        <div v-if="loadingSessions" class="px-3 py-2 text-[12px] text-[#999999]">加载中…</div>
        <!-- 桌面端会话列表：复用 SessionListItem 组件 -->
        <!-- 点击热区为整行，操作按钮平时不拦截指针事件，解决"点空白处无反应" -->
        <SessionListItem
          v-for="chat in visibleSessions"
          :key="chat.id"
          :session="chat"
          :active="chat.id === currentSessionId"
          :editing="editingSessionId === chat.id"
          v-model="editingTitle"
          :collapsed="isSidebarCollapse"
          :archived="showArchived"
          @select="onSelectSession"
          @start-edit="(id: string, title: string) => startEditTitle(id, title)"
          @confirm-edit="confirmEditTitle"
          @cancel-edit="cancelEditTitle"
          @title-keydown="(ev: KeyboardEvent, id: string) => handleTitleKeydown(ev, id)"
          @archive="onArchive"
          @unarchive="onUnarchive"
          @delete="onDeleteSession"
        />
        <div v-if="!loadingSessions && visibleSessions.length === 0 && !isSidebarCollapse" class="px-3 py-4 text-[12px] text-[#999999] text-center">
          {{ showArchived ? '暂无归档会话' : '暂无会话' }}
        </div>
      </nav>

      <div class="p-5 border-t border-[#E8E6E1]/50 relative">
        <div class="flex items-center gap-3 cursor-pointer group" @click="userMenuVisible = !userMenuVisible">
          <el-avatar
            :size="36"
            :src="displayAvatarUrl"
            class="shrink-0 transition-transform duration-300 group-hover:scale-105"
            :style="{ backgroundColor: displayAvatarUrl ? 'transparent' : '#E8E6E1', color: '#555', fontSize: '14px', fontWeight: 600 }"
          >
            {{ displayUsername.slice(0, 1).toUpperCase() }}
          </el-avatar>
          <div v-if="!isSidebarCollapse" class="flex flex-col flex-1 min-w-0">
            <span class="text-[13px] font-semibold truncate">{{ displayUsername }}</span>
            <span class="text-[11px] text-[#777777]">{{ auth.user?.email_verified ? '已验证' : '未验证' }}</span>
          </div>
        </div>
        <transition enter-active-class="transition duration-200 ease-out" enter-from-class="opacity-0 translate-y-1" enter-to-class="opacity-100 translate-y-0" leave-active-class="transition duration-150 ease-in" leave-from-class="opacity-100" leave-to-class="opacity-0">
          <div v-if="userMenuVisible" class="absolute bottom-full left-5 right-5 mb-2 bg-white rounded-2xl border border-[#E8E6E1] shadow-[0_8px_30px_rgb(0,0,0,0.08)] py-2 overflow-hidden">
            <button class="w-full px-4 py-2.5 text-left text-[13px] text-[#444444] hover:bg-[#F3F2EE] flex items-center gap-2.5 transition-colors" @click="goToSettings">
              <el-icon :size="15"><Cpu /></el-icon><span>模型供应商设置</span>
            </button>
            <button class="w-full px-4 py-2.5 text-left text-[13px] text-[#444444] hover:bg-[#F3F2EE] flex items-center gap-2.5 transition-colors" @click="onLogout">
              <el-icon :size="15"><SwitchButton /></el-icon><span>退出登录</span>
            </button>
          </div>
        </transition>
      </div>
    </aside>

    <!-- 移动端侧边栏抽屉 -->
    <el-drawer v-model="drawerVisible" direction="ltr" size="280px" :with-header="false" class="!bg-[#F3F2EE]">
      <div class="flex flex-col h-full p-6">
        <div class="flex items-center gap-3 font-semibold text-lg tracking-tight mb-8">
          <div class="w-6 h-6 bg-[#111111] rounded-full flex items-center justify-center text-[#F3F2EE]">
            <el-icon :size="14"><ChatDotRound /></el-icon>
          </div><span>CodeSage</span>
        </div>
        <div class="grid grid-cols-2 gap-2 mb-6">
          <button
            :class="['h-10 rounded-full text-sm font-medium transition-colors flex items-center justify-center gap-1.5', !showArchived ? 'bg-[#111111] text-white' : 'bg-[#F3F2EE] text-[#111111] border border-[#E8E6E1]']"
            @click="switchToActiveView"
          >
            <el-icon><ChatDotRound /></el-icon>活跃
          </button>
          <button
            :class="['h-10 rounded-full text-sm font-medium transition-colors flex items-center justify-center gap-1.5', showArchived ? 'bg-[#111111] text-white' : 'bg-[#F3F2EE] text-[#111111] border border-[#E8E6E1]']"
            @click="toggleArchived"
          >
            <el-icon><Files /></el-icon>归档
          </button>
        </div>
        <button
          v-if="!showArchived"
          class="w-full h-11 bg-[#111111] hover:bg-[#333333] text-white rounded-full flex items-center justify-center gap-2 mb-8"
          @click="newConversation"
        >
          <el-icon><Plus /></el-icon><span class="text-sm font-medium">New Conversation</span>
        </button>
        <button
          v-else
          class="w-full h-11 bg-[#F3F2EE] hover:bg-[#E8E6E1] text-[#111111] border border-[#E8E6E1] rounded-full flex items-center justify-center gap-2 mb-8"
          @click="switchToActiveView"
        >
          <el-icon><ChatDotRound /></el-icon><span class="text-sm font-medium">返回活跃会话</span>
        </button>
        <div class="flex-1 overflow-y-auto space-y-1 custom-scrollbar">
          <div class="flex items-center justify-between px-2 mb-2">
            <span class="text-[11px] font-semibold text-[#999999] uppercase tracking-wider">{{ showArchived ? '已归档' : '会话' }}</span>
            <span v-if="showArchived" class="text-[11px] text-[#999999]">{{ archivedSessions.length }} 个</span>
          </div>
          <!-- 移动端抽屉会话列表：复用 SessionListItem 组件（不传 collapsed） -->
          <SessionListItem
            v-for="chat in visibleSessions"
            :key="chat.id"
            :session="chat"
            :active="chat.id === currentSessionId"
            :editing="editingSessionId === chat.id"
            v-model="editingTitle"
            :archived="showArchived"
            @select="onSelectSession"
            @start-edit="(id: string, title: string) => startEditTitle(id, title)"
            @confirm-edit="confirmEditTitle"
            @cancel-edit="cancelEditTitle"
            @title-keydown="(ev: KeyboardEvent, id: string) => handleTitleKeydown(ev, id)"
            @archive="onArchive"
            @unarchive="onUnarchive"
            @delete="onDeleteSession"
          />
          <div v-if="!loadingSessions && visibleSessions.length === 0" class="px-3 py-4 text-[12px] text-[#999999] text-center">
            {{ showArchived ? '暂无归档会话' : '暂无会话' }}
          </div>
        </div>
        <div class="pt-4 border-t border-[#E8E6E1]/50 space-y-1">
          <button class="w-full flex items-center gap-3 px-2 py-2 text-[13px] text-[#444444] hover:text-[#111111]" @click="router.push('/settings')">
            <el-icon :size="16"><Cpu /></el-icon><span>模型供应商设置</span>
          </button>
          <button class="w-full flex items-center gap-3 px-2 py-2 text-[13px] text-[#444444] hover:text-[#111111]" @click="goToDatabaseAdmin">
            <el-icon :size="16"><Coin /></el-icon><span>数据库管理</span>
          </button>
          <button class="w-full flex items-center gap-3 px-2 py-2 text-[13px] text-[#444444] hover:text-[#111111]" @click="onLogout">
            <el-icon :size="16"><SwitchButton /></el-icon><span>退出登录 ({{ displayUsername }})</span>
          </button>
        </div>
      </div>
    </el-drawer>

    <!-- 主聊天区域 -->
    <main class="flex-1 flex flex-col relative min-w-0 min-h-0 overflow-hidden bg-[#FAFAFA]">
      <header class="h-20 flex items-center px-6 justify-between absolute top-0 left-0 right-0 z-10 bg-gradient-to-b from-[#FAFAFA] to-transparent">
        <div class="flex items-center gap-4 min-w-0">
          <button v-if="isMobile" @click="drawerVisible = true" class="p-2 -ml-2 text-[#555555]"><el-icon :size="22"><Operation /></el-icon></button>
          <h2 class="font-serif text-xl tracking-tight text-[#111111]/80 truncate">{{ currentSession?.title || 'Current Session' }}</h2>
          <span
            v-if="currentSession?.is_archived"
            class="shrink-0 px-2 py-0.5 rounded-full text-[10px] font-medium bg-[#E8E6E1] text-[#666666]"
          >已归档</span>
        </div>
        <div class="flex items-center gap-3 text-[#777777]">
          <div class="flex items-center bg-[#F3F2EE] rounded-full p-0.5 border border-[#E8E6E1]" title="回复渲染模式">
            <button
              @click="renderMode = 'text'"
              :class="['px-3 py-1 rounded-full text-[12px] transition-all', renderMode === 'text' ? 'bg-[#111111] text-white font-medium' : 'text-[#777777] hover:text-[#111111]']"
            >文本</button>
            <button
              @click="renderMode = 'component'"
              :class="['px-3 py-1 rounded-full text-[12px] transition-all', renderMode === 'component' ? 'bg-[#111111] text-white font-medium' : 'text-[#777777] hover:text-[#111111]']"
            >生成式</button>
          </div>
          <button
            v-if="currentSession?.is_archived"
            class="hover:text-[#111111] transition-colors text-[12px] px-3 py-1.5 rounded-full hover:bg-[#F3F2EE]"
            @click="currentSessionId && onUnarchive(currentSessionId)"
          >取消归档</button>
          <button v-if="currentSessionId" class="hover:text-[#111111] transition-colors text-[12px] px-3 py-1.5 rounded-full hover:bg-[#F3F2EE]" @click="onDeleteCurrent">删除会话</button>
          <button
            v-if="ragReady"
            class="flex items-center gap-1.5 hover:text-[#111111] transition-colors text-[12px] px-3 py-1.5 rounded-full hover:bg-[#F3F2EE]"
            :class="ragActive ? 'text-[#111111] font-medium' : ''"
            @click="openKnowledgePanel"
            title="知识库管理"
          >
            <el-icon :size="16"><Collection /></el-icon>
            <span class="hidden sm:inline">知识库</span>
            <span v-if="documents.length > 0" class="text-[10px] px-1.5 py-0.5 rounded-full bg-[#111111] text-white">{{ documents.length }}</span>
          </button>
          <button class="hover:text-[#111111] transition-colors"><el-icon :size="18"><Monitor /></el-icon></button>
          <button class="hover:text-[#111111] transition-colors"><el-icon :size="18"><Setting /></el-icon></button>
        </div>
      </header>

      <template v-if="renderMode === 'text'">
      <div ref="chatContainer" class="flex-1 min-h-0 overflow-y-auto pt-24 pb-44 px-4 md:px-12 scroll-smooth custom-scrollbar">
        <div class="max-w-3xl mx-auto space-y-10 pb-6">
          <div v-if="loadingMessages" class="text-center text-[13px] text-[#999999] py-8">加载消息中…</div>
          <div v-for="msg in messages" :key="msg.id" :class="['flex gap-5 animate-fade-in-up', msg.role === 'user' ? 'flex-row-reverse' : '']">
            <div :class="['w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-1', msg.role === 'user' ? 'bg-[#EAE8E0] text-[#111111]' : 'bg-[#111111] text-[#FAFAFA]']">
              <el-icon :size="14"><component :is="msg.role === 'user' ? UserIcon : ChatDotRound" /></el-icon>
            </div>
            <div :class="['max-w-[85%] leading-relaxed text-[15px]', msg.role === 'user' ? 'bg-[#F3F2EE] text-[#111111] px-5 py-3.5 rounded-2xl rounded-tr-sm' : 'text-[#111111] pt-1']">
              <div v-if="msg._isComponent && msg.role === 'assistant'" class="mb-2 flex items-center gap-1.5 text-[11px] text-[#3B82F6] font-medium">
                <el-icon :size="12"><Cpu /></el-icon>
                生成式界面 — 切换到「生成式」模式查看完整页面
              </div>
              <div v-if="msg.attachments && msg.attachments.length > 0" class="mb-2 flex flex-wrap gap-2">
                <template v-for="att in msg.attachments" :key="att.data || att.filename">
                  <img v-if="att.type === 'image' && att.data" :src="att.data" class="max-w-[200px] max-h-[200px] rounded-lg object-cover cursor-pointer" @click="previewImage(att.data!)" />
                  <div v-else-if="att.type === 'document'" class="flex items-center gap-1.5 px-2 py-1 bg-[#F3F2EE] rounded-lg text-xs text-[#111111]">
                    <el-icon class="w-3.5 h-3.5"><Document /></el-icon>
                    <span>{{ att.filename }}</span>
                  </div>
                </template>
              </div>
              <!-- Markdown 富文本渲染 -->
              <div class="markdown-body" v-html="renderMarkdown(msg.content)"></div>
              <div v-if="isTyping && msg.id === messages[messages.length-1].id && msg.role === 'assistant'" class="inline-block w-2 h-4 bg-[#111111] animate-pulse-cursor ml-1 align-middle"></div>
            </div>
          </div>
        </div>
      </div>

      <footer class="absolute bottom-0 left-0 right-0 p-4 md:p-8 bg-gradient-to-t from-[#FAFAFA] via-[#FAFAFA] to-transparent pointer-events-none">
        <div class="max-w-3xl mx-auto relative pointer-events-auto">
          <!-- RAG 模式切换条 -->
          <div v-if="ragReady" class="flex items-center justify-between mb-2 px-2">
            <div class="flex items-center gap-2">
              <button
                @click="ragMode = ragActive ? 'off' : 'hybrid'"
                :class="['flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[12px] font-medium transition-all', ragActive ? 'bg-[#111111] text-white' : 'bg-[#F3F2EE] text-[#777] hover:text-[#111]']"
              >
                <el-icon :size="13"><Files /></el-icon>
                <span>知识库 {{ ragActive ? '已开启' : '已关闭' }}</span>
              </button>
              <div v-if="ragActive" class="flex items-center gap-1">
                <button
                  v-for="opt in ragModeOptions"
                  :key="opt.value"
                  @click="ragMode = opt.value"
                  :class="['px-2.5 py-1 rounded-full text-[11px] transition-all', ragMode === opt.value ? 'bg-[#E8E6E1] text-[#111] font-medium' : 'text-[#999] hover:text-[#555]']"
                >{{ opt.label }}</button>
              </div>
            </div>
            <span v-if="ragActive" class="text-[11px] text-[#999]">回复将引用知识库</span>
          </div>

          <div class="bg-white rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-[#E8E6E1] p-2 pr-14 relative transition-all duration-300 focus-within:shadow-[0_8px_30px_rgb(0,0,0,0.08)] focus-within:border-[#D1CFCA]">
            <div v-if="pendingImages.length > 0 || pendingDocuments.length > 0" class="flex flex-wrap gap-2 px-3 pt-2 pb-1">
              <div v-for="img in pendingImages" :key="img.id" class="relative group">
                <img :src="img.dataUrl" class="w-14 h-14 rounded-lg object-cover border border-[#E8E6E1]" />
                <button @click="removePendingImage(img.id)" class="absolute -top-1.5 -right-1.5 w-5 h-5 bg-[#111] text-white rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                  <el-icon :size="10"><Close /></el-icon>
                </button>
              </div>
              <div v-for="doc in pendingDocuments" :key="doc.id" class="relative group flex items-center gap-1.5 px-2.5 py-1.5 bg-[#F3F2EE] rounded-lg text-[12px] text-[#555]">
                <el-icon :size="14"><Document /></el-icon>
                <span class="max-w-[100px] truncate">{{ doc.filename }}</span>
                <button @click="removePendingDocument(doc.id)" class="ml-1 text-[#999] hover:text-[#111]">
                  <el-icon :size="12"><Close /></el-icon>
                </button>
              </div>
            </div>
            <div class="flex items-center gap-1 px-2">
              <button @click="triggerImageSelect" class="p-2 rounded-full hover:bg-[#F3F2EE] text-[#999] hover:text-[#111] transition-colors" title="上传图片">
                <el-icon :size="18"><Picture /></el-icon>
              </button>
              <button @click="triggerDocSelect" class="p-2 rounded-full hover:bg-[#F3F2EE] text-[#999] hover:text-[#111] transition-colors" title="上传文档">
                <el-icon :size="18"><Document /></el-icon>
              </button>
            </div>
            <input ref="imageInputRef" type="file" accept="image/jpeg,image/png,image/gif,image/webp" multiple class="hidden" @change="onImageFileChange" />
            <input ref="documentInputRef" type="file" accept=".pdf,.docx,.txt,.md" multiple class="hidden" @change="onDocFileChange" />
            <textarea
              v-model="userInput"
              rows="1"
              :placeholder="currentSessionId ? (ragActive ? '基于知识库提问...' : 'Ask anything...') : '点击 New Conversation 开始对话...'"
              class="w-full max-h-[200px] bg-transparent border-none outline-none resize-none py-3 px-4 text-[15px] leading-relaxed text-[#111111] placeholder:text-[#AAAAAA] custom-scrollbar"
              @input="adjustTextareaHeight"
              @keydown.enter.prevent="onSend"
              @paste="onPasteImage"
            ></textarea>
            <button @click="onSend" :disabled="!canSend" class="absolute right-3 bottom-3 w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 disabled:opacity-30 disabled:cursor-not-allowed text-white" :class="canSend ? 'bg-[#111111] hover:bg-[#333333]' : 'bg-[#D1CFCA]'">
              <el-icon :size="16"><Promotion /></el-icon>
            </button>
          </div>
          <p class="text-center text-[11px] text-[#999999] mt-3 font-medium tracking-wide">CodeSage AI may produce inaccurate information. Please verify critical details.</p>
        </div>
      </footer>
      </template>

      <GenerativePanel
        v-else
        :session-id="currentSessionId"
        :use-rag="ragActive"
        :rag-mode="ragMode === 'off' ? 'hybrid' : ragMode"
        @session-created="onGenSessionCreated"
      />
    </main>

    <!-- 知识库管理抽屉 -->
    <KnowledgePanel
      v-model:visible="knowledgePanelVisible"
      :documents="documents"
      :loading-docs="loadingDocs"
      :uploading="uploading"
      @upload="uploadDocument"
      @upload-file="uploadFile"
      @remove="removeDocument"
      @refresh="loadDocuments"
      @reset="resetKnowledge"
    />

    <el-dialog v-model="imagePreviewVisible" title="图片预览" width="fit-content" append-to-body>
      <img :src="imagePreviewUrl" class="max-w-full max-h-[70vh] rounded-lg" />
    </el-dialog>
  </div>
</template>
