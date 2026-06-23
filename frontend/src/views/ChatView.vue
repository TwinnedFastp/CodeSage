<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ChatDotRound, Operation, Plus, User as UserIcon, Monitor, Setting,
  Fold, Expand, Promotion, SwitchButton, Collection, Files, Cpu, Coin,
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

const router = useRouter()
const auth = useAuthStore()

const { isMobile, isSidebarCollapse, drawerVisible } = useResponsive()

const {
  sessions, currentSessionId, currentSession, loadingSessions,
  editingSessionId, editingTitle,
  loadSessions, newConversation: createSession, selectSession, deleteSession,
  startEditTitle, cancelEditTitle, confirmEditTitle,
  tryAutoGenerateTitle, applyGeneratedTitle,
} = useSessions()

const chatContainer = ref<HTMLElement | null>(null)

const {
  messages, userInput, isTyping, loadingMessages,
  loadMessages, clearMessages, showWelcome,
  sendMessage: doSend, adjustTextareaHeight,
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
  } else if (sessions.value.length > 0) {
    selectSession(sessions.value[0].id)
    await loadMessages(sessions.value[0].id)
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
    if (sessions.value.length > 0) {
      await onSelectSession(sessions.value[0].id)
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
const ragModeOptions = [
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
        <!-- 顶部小图标目录：快速进入聊天 / 数据库 / 设置 -->
        <div class="grid grid-cols-3 gap-1.5 p-1.5 rounded-xl bg-white border border-[#E8E6E1] shadow-[0_2px_12px_rgb(0,0,0,0.03)]">
          <button class="flex flex-col items-center justify-center gap-0.5 py-1.5 rounded-lg bg-[#111] text-white" title="当前聊天">
            <el-icon :size="13"><ChatDotRound /></el-icon>
            <span v-if="!isSidebarCollapse" class="text-[9px] leading-tight">聊天</span>
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
        <button class="w-full h-11 bg-[#111111] hover:bg-[#333333] text-white rounded-full flex items-center justify-center gap-2 transition-all duration-300 shadow-sm" @click="newConversation">
          <el-icon><Plus /></el-icon>
          <span v-if="!isSidebarCollapse" class="text-sm font-medium">New Conversation</span>
        </button>
      </div>

      <nav class="flex-1 overflow-y-auto px-3 py-2 space-y-1 custom-scrollbar">
        <div v-if="loadingSessions" class="px-3 py-2 text-[12px] text-[#999999]">加载中…</div>
        <!-- 桌面端会话列表：复用 SessionListItem 组件 -->
        <!-- 点击热区为整行，重命名按钮平时不拦截指针事件，解决"点空白处无反应" -->
        <SessionListItem
          v-for="chat in sessions"
          :key="chat.id"
          :session="chat"
          :active="chat.id === currentSessionId"
          :editing="editingSessionId === chat.id"
          v-model="editingTitle"
          :collapsed="isSidebarCollapse"
          @select="onSelectSession"
          @start-edit="(id: string, title: string) => startEditTitle(id, title)"
          @confirm-edit="confirmEditTitle"
          @cancel-edit="cancelEditTitle"
          @title-keydown="(ev: KeyboardEvent, id: string) => handleTitleKeydown(ev, id)"
        />
        <div v-if="!loadingSessions && sessions.length === 0 && !isSidebarCollapse" class="px-3 py-4 text-[12px] text-[#999999] text-center">暂无会话</div>
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
        <button class="w-full h-11 bg-[#111111] hover:bg-[#333333] text-white rounded-full flex items-center justify-center gap-2 mb-8" @click="newConversation">
          <el-icon><Plus /></el-icon><span class="text-sm font-medium">New Conversation</span>
        </button>
        <div class="flex-1 overflow-y-auto space-y-1 custom-scrollbar">
          <!-- 移动端抽屉会话列表：复用 SessionListItem 组件（不传 collapsed） -->
          <SessionListItem
            v-for="chat in sessions"
            :key="chat.id"
            :session="chat"
            :active="chat.id === currentSessionId"
            :editing="editingSessionId === chat.id"
            v-model="editingTitle"
            @select="onSelectSession"
            @start-edit="(id: string, title: string) => startEditTitle(id, title)"
            @confirm-edit="confirmEditTitle"
            @cancel-edit="cancelEditTitle"
            @title-keydown="(ev: KeyboardEvent, id: string) => handleTitleKeydown(ev, id)"
          />
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
              <div class="whitespace-pre-wrap font-sans">{{ msg.content }}</div>
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
                  @click="ragMode = opt.value as any"
                  :class="['px-2.5 py-1 rounded-full text-[11px] transition-all', ragMode === opt.value ? 'bg-[#E8E6E1] text-[#111] font-medium' : 'text-[#999] hover:text-[#555]']"
                >{{ opt.label }}</button>
              </div>
            </div>
            <span v-if="ragActive" class="text-[11px] text-[#999]">回复将引用知识库</span>
          </div>

          <div class="bg-white rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-[#E8E6E1] p-2 pr-14 relative transition-all duration-300 focus-within:shadow-[0_8px_30px_rgb(0,0,0,0.08)] focus-within:border-[#D1CFCA]">
            <textarea
              v-model="userInput"
              rows="1"
              :placeholder="currentSessionId ? (ragActive ? '基于知识库提问...' : 'Ask anything...') : '点击 New Conversation 开始对话...'"
              class="w-full max-h-[200px] bg-transparent border-none outline-none resize-none py-3 px-4 text-[15px] leading-relaxed text-[#111111] placeholder:text-[#AAAAAA] custom-scrollbar"
              @input="adjustTextareaHeight"
              @keydown.enter.prevent="onSend"
            ></textarea>
            <button @click="onSend" :disabled="!userInput.trim() || isTyping" class="absolute right-3 bottom-3 w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 disabled:opacity-30 disabled:cursor-not-allowed text-white" :class="userInput.trim() && !isTyping ? 'bg-[#111111] hover:bg-[#333333]' : 'bg-[#D1CFCA]'">
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
  </div>
</template>
