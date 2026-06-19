<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ChatDotRound, Operation, Plus, User as UserIcon, Monitor, Setting,
  Fold, Expand, Promotion, SwitchButton, Edit,
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useResponsive } from '@/composables/useResponsive'
import { useSessions } from '@/composables/useSessions'
import { useChat } from '@/composables/useChat'

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

// ---- 初始化 ----
;(async () => {
  await loadSessions()
  if (sessions.value.length > 0) {
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

const maskedEmail = computed(() => {
  const e = auth.user?.email || ''
  if (!e) return ''
  const [name, domain] = e.split('@')
  return domain ? `${name[0]}***@${domain}` : e
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
  await doSend(async () => await createSession())
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

      <div class="px-5 mb-6 mt-2">
        <button class="w-full h-11 bg-[#111111] hover:bg-[#333333] text-white rounded-full flex items-center justify-center gap-2 transition-all duration-300 shadow-sm" @click="newConversation">
          <el-icon><Plus /></el-icon>
          <span v-if="!isSidebarCollapse" class="text-sm font-medium">New Conversation</span>
        </button>
      </div>

      <nav class="flex-1 overflow-y-auto px-3 py-2 space-y-1 custom-scrollbar">
        <div v-if="loadingSessions" class="px-3 py-2 text-[12px] text-[#999999]">加载中…</div>
        <div
          v-for="chat in sessions"
          :key="chat.id"
          :class="['group flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors', chat.id === currentSessionId ? 'bg-[#E8E6E1]' : 'hover:bg-[#E8E6E1]', editingSessionId === chat.id ? 'ring-1 ring-[#111111]/20' : '']"
        >
          <div :class="['w-1.5 h-1.5 rounded-full shrink-0', chat.id === currentSessionId ? 'bg-[#111111]' : 'bg-[#D1CFCA]']"></div>
          <template v-if="editingSessionId === chat.id">
            <input
              v-model="editingTitle"
              class="session-title-input flex-1 min-w-0 bg-white border border-[#D1CFCA] rounded-lg px-2.5 py-1.5 text-[13px] font-medium text-[#111111] outline-none focus:border-[#111111] transition-colors"
              maxlength="60"
              @keydown="(e: KeyboardEvent) => handleTitleKeydown(e, chat.id)"
              @blur="confirmEditTitle(chat.id)"
            />
          </template>
          <template v-else>
            <span
              v-if="!isSidebarCollapse"
              class="flex-1 min-w-0 truncate text-[13px] font-medium cursor-pointer"
              :class="chat.id === currentSessionId ? 'text-[#111111]' : 'text-[#444444] group-hover:text-[#111111]'"
              @click="onSelectSession(chat.id)"
              @dblclick.stop="startEditTitle(chat.id, chat.title || '')"
            >{{ chat.title || '未命名会话' }}</span>
            <button
              v-if="!isSidebarCollapse"
              class="shrink-0 p-1 rounded-md opacity-0 group-hover:opacity-100 hover:bg-[#EAE8E0] transition-all text-[#999999] hover:text-[#111111]"
              @click.stop="startEditTitle(chat.id, chat.title || '')"
              title="重命名"
            ><el-icon :size="12"><Edit /></el-icon></button>
            <div v-if="isSidebarCollapse" class="cursor-pointer flex-1" @click="onSelectSession(chat.id)"></div>
          </template>
        </div>
        <div v-if="!loadingSessions && sessions.length === 0 && !isSidebarCollapse" class="px-3 py-4 text-[12px] text-[#999999] text-center">暂无会话</div>
      </nav>

      <div class="p-5 border-t border-[#E8E6E1]/50 relative">
        <div class="flex items-center gap-3 cursor-pointer group" @click="userMenuVisible = !userMenuVisible">
          <div class="w-9 h-9 rounded-full bg-[#E8E6E1] flex items-center justify-center text-[#555555] group-hover:bg-[#111111] group-hover:text-white transition-colors">
            <el-icon><UserIcon /></el-icon>
          </div>
          <div v-if="!isSidebarCollapse" class="flex flex-col flex-1 min-w-0">
            <span class="text-[13px] font-semibold truncate">{{ maskedEmail }}</span>
            <span class="text-[11px] text-[#777777]">{{ auth.user?.email_verified ? '已验证' : '未验证' }}</span>
          </div>
        </div>
        <transition enter-active-class="transition duration-200 ease-out" enter-from-class="opacity-0 translate-y-1" enter-to-class="opacity-100 translate-y-0" leave-active-class="transition duration-150 ease-in" leave-from-class="opacity-100" leave-to-class="opacity-0">
          <div v-if="userMenuVisible" class="absolute bottom-full left-5 right-5 mb-2 bg-white rounded-2xl border border-[#E8E6E1] shadow-[0_8px_30px_rgb(0,0,0,0.08)] py-2 overflow-hidden">
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
          <div
            v-for="chat in sessions"
            :key="chat.id"
            :class="['flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors group', chat.id === currentSessionId ? 'bg-[#E8E6E1]' : 'hover:bg-[#E8E6E1]', editingSessionId === chat.id ? 'ring-1 ring-[#111111]/20' : '']"
          >
            <div :class="['w-1.5 h-1.5 rounded-full shrink-0', chat.id === currentSessionId ? 'bg-[#111111]' : 'bg-[#D1CFCA]']"></div>
            <template v-if="editingSessionId === chat.id">
              <input v-model="editingTitle" class="session-title-input flex-1 min-w-0 bg-white border border-[#D1CFCA] rounded-lg px-2.5 py-1.5 text-[13px] font-medium text-[#111111] outline-none focus:border-[#111111]" maxlength="60" @keydown="(e: KeyboardEvent) => handleTitleKeydown(e, chat.id)" @blur="confirmEditTitle(chat.id)" />
            </template>
            <template v-else>
              <span class="flex-1 min-w-0 truncate text-[13px] font-medium cursor-pointer" :class="chat.id === currentSessionId ? 'text-[#111111]' : 'text-[#444444]'" @click="onSelectSession(chat.id)" @dblclick.stop="startEditTitle(chat.id, chat.title || '')">{{ chat.title || '未命名会话' }}</span>
              <button class="shrink-0 p-1 rounded-md opacity-0 group-hover:opacity-100 hover:bg-[#EAE8E0] transition-all text-[#999999] hover:text-[#111111]" @click.stop="startEditTitle(chat.id, chat.title || '')" title="重命名"><el-icon :size="12"><Edit /></el-icon></button>
            </template>
          </div>
        </div>
        <div class="pt-4 border-t border-[#E8E6E1]/50">
          <button class="w-full flex items-center gap-3 px-2 py-2 text-[13px] text-[#444444] hover:text-[#111111]" @click="onLogout">
            <el-icon :size="16"><SwitchButton /></el-icon><span>退出登录 ({{ maskedEmail }})</span>
          </button>
        </div>
      </div>
    </el-drawer>

    <!-- 主聊天区域 -->
    <main class="flex-1 flex flex-col relative min-w-0 bg-[#FAFAFA]">
      <header class="h-20 flex items-center px-6 justify-between absolute top-0 left-0 right-0 z-10 bg-gradient-to-b from-[#FAFAFA] to-transparent">
        <div class="flex items-center gap-4 min-w-0">
          <button v-if="isMobile" @click="drawerVisible = true" class="p-2 -ml-2 text-[#555555]"><el-icon :size="22"><Operation /></el-icon></button>
          <h2 class="font-serif text-xl tracking-tight text-[#111111]/80 truncate">{{ currentSession?.title || 'Current Session' }}</h2>
        </div>
        <div class="flex items-center gap-3 text-[#777777]">
          <button v-if="currentSessionId" class="hover:text-[#111111] transition-colors text-[12px] px-3 py-1.5 rounded-full hover:bg-[#F3F2EE]" @click="onDeleteCurrent">删除会话</button>
          <button class="hover:text-[#111111] transition-colors"><el-icon :size="18"><Monitor /></el-icon></button>
          <button class="hover:text-[#111111] transition-colors"><el-icon :size="18"><Setting /></el-icon></button>
        </div>
      </header>

      <div ref="chatContainer" class="flex-1 overflow-y-auto pt-24 pb-44 px-4 md:px-12 scroll-smooth custom-scrollbar">
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
          <div class="bg-white rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-[#E8E6E1] p-2 pr-14 relative transition-all duration-300 focus-within:shadow-[0_8px_30px_rgb(0,0,0,0.08)] focus-within:border-[#D1CFCA]">
            <textarea
              v-model="userInput"
              rows="1"
              :placeholder="currentSessionId ? 'Ask anything...' : '点击 New Conversation 开始对话...'"
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
    </main>
  </div>
</template>
