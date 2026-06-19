<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ChatDotRound, Operation, Plus, User as UserIcon, Monitor, Setting,
  Fold, Expand, Promotion, SwitchButton,
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import * as convApi from '@/api/conversations'
import type { ChatSession, DisplayMessage } from '@/types'

const router = useRouter()
const auth = useAuthStore()

// ---- 响应式布局 ----
const isMobile = ref(false)
const isSidebarCollapse = ref(false)
const drawerVisible = ref(false)
const checkMobile = () => { isMobile.value = window.innerWidth < 768 }

// ---- 会话与消息 ----
const sessions = ref<ChatSession[]>([])
const currentSessionId = ref<string | null>(null)
const messages = ref<DisplayMessage[]>([])
const userInput = ref('')
const isTyping = ref(false)
const chatContainer = ref<HTMLElement | null>(null)
const loadingSessions = ref(false)
const loadingMessages = ref(false)

const currentSession = computed(() =>
  sessions.value.find(s => s.id === currentSessionId.value) || null
)

// ---- 用户菜单 ----
const userMenuVisible = ref(false)

// ---- 初始化 ----
onMounted(async () => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
  await loadSessions()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', checkMobile)
})

// ---- 会话列表 ----
async function loadSessions() {
  loadingSessions.value = true
  try {
    sessions.value = await convApi.listSessions(50, 0)
    if (sessions.value.length > 0 && !currentSessionId.value) {
      await selectSession(sessions.value[0].id)
    } else if (sessions.value.length === 0) {
      // 无会话时显示欢迎语
      messages.value = [{
        id: 'welcome',
        role: 'assistant',
        content: '你好。我是 CodeSage，你的代码工程师。点击「New Conversation」开始我们的第一段对话。'
      }]
    }
  } catch (err: any) {
    ElMessage.error(err.response?.data?.message || '加载会话列表失败')
  } finally {
    loadingSessions.value = false
  }
}

async function selectSession(id: string) {
  if (currentSessionId.value === id) return
  currentSessionId.value = id
  messages.value = []
  drawerVisible.value = false
  await loadMessages(id)
}

async function loadMessages(sessionId: string) {
  loadingMessages.value = true
  try {
    const list = await convApi.listMessages(sessionId, 100, 0)
    messages.value = list.map(m => ({
      id: m.message_id,
      role: m.role === 'user' ? 'user' : 'assistant',
      content: m.content,
    }))
    if (messages.value.length === 0) {
      messages.value = [{
        id: 'welcome',
        role: 'assistant',
        content: '你好。我是 CodeSage，你的代码工程师。有什么我可以帮你的吗？'
      }]
    }
    await scrollToBottom()
  } catch (err: any) {
    ElMessage.error(err.response?.data?.message || '加载消息失败')
  } finally {
    loadingMessages.value = false
  }
}

async function newConversation() {
  try {
    const title = `会话 · ${new Date().toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })}`
    const session = await convApi.createSession(title)
    sessions.value.unshift(session)
    await selectSession(session.id)
  } catch (err: any) {
    ElMessage.error(err.response?.data?.message || '创建会话失败')
  }
}

async function deleteCurrentSession() {
  if (!currentSessionId.value) return
  try {
    await ElMessageBox.confirm('删除该会话将同时清除所有消息，确定继续吗？', '删除会话', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      confirmButtonClass: 'el-button--danger',
    })
  } catch {
    return
  }
  const id = currentSessionId.value
  try {
    await convApi.deleteSession(id)
    sessions.value = sessions.value.filter(s => s.id !== id)
    if (sessions.value.length > 0) {
      await selectSession(sessions.value[0].id)
    } else {
      currentSessionId.value = null
      messages.value = [{
        id: 'welcome',
        role: 'assistant',
        content: '你好。我是 CodeSage，你的代码工程师。点击「New Conversation」开始新的对话。'
      }]
    }
    ElMessage.success('会话已删除')
  } catch (err: any) {
    ElMessage.error(err.response?.data?.message || '删除会话失败')
  }
}

// ---- 滚动与输入框 ----
const scrollToBottom = async () => {
  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

const adjustTextareaHeight = (e: Event) => {
  const target = e.target as HTMLTextAreaElement
  target.style.height = 'auto'
  target.style.height = Math.min(target.scrollHeight, 200) + 'px'
}

// ---- 发送消息（流式 + JWT）----
async function sendMessage() {
  if (!userInput.value.trim() || isTyping.value) return

  // 无会话时自动创建一个
  if (!currentSessionId.value) {
    await newConversation()
    if (!currentSessionId.value) return
  }

  const userText = userInput.value.trim()
  const sessionId = currentSessionId.value

  // 立即追加用户消息
  messages.value.push({
    id: `u-${Date.now()}`,
    role: 'user',
    content: userText,
  })
  userInput.value = ''
  const textarea = document.querySelector('textarea')
  if (textarea) textarea.style.height = 'auto'

  // 占位助手消息
  const assistantId = `a-${Date.now()}`
  messages.value.push({
    id: assistantId,
    role: 'assistant',
    content: '',
    pending: true,
  })
  isTyping.value = true
  await scrollToBottom()

  try {
    const token = auth.accessToken
    const response = await fetch('/api/v1/chat/chatstreaming', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ message: userText, session_id: sessionId }),
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }
    if (!response.body) throw new Error('无响应流')

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    const target = messages.value.find(m => m.id === assistantId)
    if (target) target.pending = false

    let backendSessionId: string | null = null
    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const data = line.slice(6)
        if (data === '[DONE]') continue
        try {
          const parsed = JSON.parse(data)
          // 首帧携带 session_id（后端自动创建会话时）
          if (parsed.session_id && !backendSessionId) {
            backendSessionId = parsed.session_id
            if (backendSessionId !== sessionId) {
              currentSessionId.value = backendSessionId
              // 刷新侧边栏会话列表
              loadSessions()
            }
            continue
          }
          const t = messages.value.find(m => m.id === assistantId)
          if (t && parsed.content) {
            t.content += parsed.content
            await scrollToBottom()
          }
        } catch {
          // 忽略非 JSON 帧心跳
        }
      }
    }

    // 流结束后刷新会话列表标题（若首条消息触发了标题更新）
    // 此处简单刷新列表，不强制
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

// ---- 登出 ----
async function onLogout() {
  userMenuVisible.value = false
  await auth.logout()
  ElMessage.success('已登出')
  router.push('/login')
}

// 用户邮箱脱敏展示（保留首字符 + 域名）
const maskedEmail = computed(() => {
  const e = auth.user?.email || ''
  if (!e) return ''
  const [name, domain] = e.split('@')
  if (!domain) return e
  return `${name[0]}***@${domain}`
})
</script>

<template>
  <div class="flex h-screen w-screen bg-[#FAFAFA] text-[#111111] overflow-hidden antialiased font-sans selection:bg-[#EAE8E0]">

    <!-- 桌面端侧边栏 -->
    <aside
      v-if="!isMobile"
      :class="[
        'bg-[#F3F2EE] transition-all duration-500 ease-[cubic-bezier(0.16,1,0.3,1)] flex flex-col',
        isSidebarCollapse ? 'w-[80px]' : 'w-[280px]'
      ]"
    >
      <div class="p-6 flex items-center justify-between h-20">
        <div v-if="!isSidebarCollapse" class="flex items-center gap-3 font-semibold text-lg tracking-tight">
          <div class="w-6 h-6 bg-[#111111] rounded-full flex items-center justify-center text-[#F3F2EE]">
            <el-icon :size="14"><ChatDotRound /></el-icon>
          </div>
          <span>CodeSage</span>
        </div>
        <button
          @click="isSidebarCollapse = !isSidebarCollapse"
          class="p-2 rounded-full hover:bg-[#E8E6E1] transition-colors text-[#555555] mx-auto"
        >
          <el-icon :size="18"><component :is="isSidebarCollapse ? Expand : Fold" /></el-icon>
        </button>
      </div>

      <div class="px-5 mb-6 mt-2">
        <button
          class="w-full h-11 bg-[#111111] hover:bg-[#333333] text-white rounded-full flex items-center justify-center gap-2 transition-all duration-300 shadow-sm"
          @click="newConversation"
        >
          <el-icon><Plus /></el-icon>
          <span v-if="!isSidebarCollapse" class="text-sm font-medium">New Conversation</span>
        </button>
      </div>

      <nav class="flex-1 overflow-y-auto px-3 py-2 space-y-1 custom-scrollbar">
        <div v-if="loadingSessions" class="px-3 py-2 text-[12px] text-[#999999]">加载中…</div>
        <div
          v-for="chat in sessions"
          :key="chat.id"
          :class="[
            'flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-pointer hover:bg-[#E8E6E1] transition-colors group',
            chat.id === currentSessionId ? 'bg-[#E8E6E1]' : ''
          ]"
          @click="selectSession(chat.id)"
        >
          <div :class="['w-1.5 h-1.5 rounded-full transition-colors', chat.id === currentSessionId ? 'bg-[#111111]' : 'bg-[#D1CFCA] group-hover:bg-[#111111]']"></div>
          <span v-if="!isSidebarCollapse" class="truncate text-[13px] font-medium text-[#444444] group-hover:text-[#111111]">{{ chat.title || '未命名会话' }}</span>
        </div>
        <div v-if="!loadingSessions && sessions.length === 0 && !isSidebarCollapse" class="px-3 py-4 text-[12px] text-[#999999] text-center">
          暂无会话
        </div>
      </nav>

      <!-- 用户菜单区 -->
      <div class="p-5 border-t border-[#E8E6E1]/50 relative">
        <div
          class="flex items-center gap-3 cursor-pointer group"
          @click="userMenuVisible = !userMenuVisible"
        >
          <div class="w-9 h-9 rounded-full bg-[#E8E6E1] flex items-center justify-center text-[#555555] group-hover:bg-[#111111] group-hover:text-white transition-colors">
            <el-icon><UserIcon /></el-icon>
          </div>
          <div v-if="!isSidebarCollapse" class="flex flex-col flex-1 min-w-0">
            <span class="text-[13px] font-semibold truncate">{{ maskedEmail }}</span>
            <span class="text-[11px] text-[#777777]">{{ auth.user?.email_verified ? '已验证' : '未验证' }}</span>
          </div>
        </div>

        <!-- 下拉菜单 -->
        <transition
          enter-active-class="transition duration-200 ease-out"
          enter-from-class="opacity-0 translate-y-1"
          enter-to-class="opacity-100 translate-y-0"
          leave-active-class="transition duration-150 ease-in"
          leave-from-class="opacity-100"
          leave-to-class="opacity-0"
        >
          <div
            v-if="userMenuVisible"
            class="absolute bottom-full left-5 right-5 mb-2 bg-white rounded-2xl border border-[#E8E6E1] shadow-[0_8px_30px_rgb(0,0,0,0.08)] py-2 overflow-hidden"
          >
            <button
              class="w-full px-4 py-2.5 text-left text-[13px] text-[#444444] hover:bg-[#F3F2EE] flex items-center gap-2.5 transition-colors"
              @click="onLogout"
            >
              <el-icon :size="15"><SwitchButton /></el-icon>
              <span>退出登录</span>
            </button>
          </div>
        </transition>
      </div>
    </aside>

    <!-- 移动端侧边栏抽屉 -->
    <el-drawer
      v-model="drawerVisible"
      direction="ltr"
      size="280px"
      :with-header="false"
      class="!bg-[#F3F2EE]"
    >
      <div class="flex flex-col h-full p-6">
        <div class="flex items-center gap-3 font-semibold text-lg tracking-tight mb-8">
          <div class="w-6 h-6 bg-[#111111] rounded-full flex items-center justify-center text-[#F3F2EE]">
            <el-icon :size="14"><ChatDotRound /></el-icon>
          </div>
          <span>CodeSage</span>
        </div>
        <button
          class="w-full h-11 bg-[#111111] hover:bg-[#333333] text-white rounded-full flex items-center justify-center gap-2 mb-8"
          @click="newConversation"
        >
          <el-icon><Plus /></el-icon>
          <span class="text-sm font-medium">New Conversation</span>
        </button>
        <div class="flex-1 overflow-y-auto space-y-1 custom-scrollbar">
          <div
            v-for="chat in sessions"
            :key="chat.id"
            :class="['flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-[#E8E6E1]', chat.id === currentSessionId ? 'bg-[#E8E6E1]' : '']"
            @click="selectSession(chat.id)"
          >
            <div :class="['w-1.5 h-1.5 rounded-full', chat.id === currentSessionId ? 'bg-[#111111]' : 'bg-[#D1CFCA]']"></div>
            <span class="truncate text-[13px] font-medium text-[#444444]">{{ chat.title || '未命名会话' }}</span>
          </div>
        </div>
        <div class="pt-4 border-t border-[#E8E6E1]/50">
          <button
            class="w-full flex items-center gap-3 px-2 py-2 text-[13px] text-[#444444] hover:text-[#111111]"
            @click="onLogout"
          >
            <el-icon :size="16"><SwitchButton /></el-icon>
            <span>退出登录 ({{ maskedEmail }})</span>
          </button>
        </div>
      </div>
    </el-drawer>

    <!-- 主聊天区域 -->
    <main class="flex-1 flex flex-col relative min-w-0 bg-[#FAFAFA]">
      <!-- 顶部导航 -->
      <header class="h-20 flex items-center px-6 justify-between absolute top-0 left-0 right-0 z-10 bg-gradient-to-b from-[#FAFAFA] to-transparent">
        <div class="flex items-center gap-4 min-w-0">
          <button
            v-if="isMobile"
            @click="drawerVisible = true"
            class="p-2 -ml-2 text-[#555555]"
          >
            <el-icon :size="22"><Operation /></el-icon>
          </button>
          <h2 class="font-serif text-xl tracking-tight text-[#111111]/80 truncate">
            {{ currentSession?.title || 'Current Session' }}
          </h2>
        </div>
        <div class="flex items-center gap-3 text-[#777777]">
          <button
            v-if="currentSessionId"
            class="hover:text-[#111111] transition-colors text-[12px] px-3 py-1.5 rounded-full hover:bg-[#F3F2EE]"
            @click="deleteCurrentSession"
          >
            删除会话
          </button>
          <button class="hover:text-[#111111] transition-colors"><el-icon :size="18"><Monitor /></el-icon></button>
          <button class="hover:text-[#111111] transition-colors"><el-icon :size="18"><Setting /></el-icon></button>
        </div>
      </header>

      <!-- 消息列表 -->
      <div
        ref="chatContainer"
        class="flex-1 overflow-y-auto pt-24 pb-32 px-4 md:px-12 scroll-smooth custom-scrollbar"
      >
        <div class="max-w-3xl mx-auto space-y-10">
          <div v-if="loadingMessages" class="text-center text-[13px] text-[#999999] py-8">加载消息中…</div>
          <div
            v-for="msg in messages"
            :key="msg.id"
            :class="[
              'flex gap-5 animate-fade-in-up',
              msg.role === 'user' ? 'flex-row-reverse' : ''
            ]"
          >
            <!-- 头像 -->
            <div
              :class="[
                'w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-1',
                msg.role === 'user' ? 'bg-[#EAE8E0] text-[#111111]' : 'bg-[#111111] text-[#FAFAFA]'
              ]"
            >
              <el-icon :size="14"><component :is="msg.role === 'user' ? UserIcon : ChatDotRound" /></el-icon>
            </div>

            <!-- 消息内容 -->
            <div
              :class="[
                'max-w-[85%] leading-relaxed text-[15px]',
                msg.role === 'user'
                  ? 'bg-[#F3F2EE] text-[#111111] px-5 py-3.5 rounded-2xl rounded-tr-sm'
                  : 'text-[#111111] pt-1'
              ]"
            >
              <div class="whitespace-pre-wrap font-sans">{{ msg.content }}</div>

              <!-- 闪烁光标 -->
              <div
                v-if="isTyping && msg.id === messages[messages.length-1].id && msg.role === 'assistant'"
                class="inline-block w-2 h-4 bg-[#111111] animate-pulse-cursor ml-1 align-middle"
              ></div>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入框区域 -->
      <footer class="absolute bottom-0 left-0 right-0 p-4 md:p-8 bg-gradient-to-t from-[#FAFAFA] via-[#FAFAFA] to-transparent pointer-events-none">
        <div class="max-w-3xl mx-auto relative pointer-events-auto">
          <div class="bg-white rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-[#E8E6E1] p-2 pr-14 relative transition-all duration-300 focus-within:shadow-[0_8px_30px_rgb(0,0,0,0.08)] focus-within:border-[#D1CFCA]">
            <textarea
              v-model="userInput"
              rows="1"
              :placeholder="currentSessionId ? 'Ask anything...' : '点击 New Conversation 开始对话...'"
              class="w-full max-h-[200px] bg-transparent border-none outline-none resize-none py-3 px-4 text-[15px] leading-relaxed text-[#111111] placeholder:text-[#AAAAAA] custom-scrollbar"
              @input="adjustTextareaHeight"
              @keydown.enter.prevent="sendMessage"
            ></textarea>

            <button
              @click="sendMessage"
              :disabled="!userInput.trim() || isTyping"
              class="absolute right-3 bottom-3 w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 disabled:opacity-30 disabled:cursor-not-allowed text-white"
              :class="userInput.trim() && !isTyping ? 'bg-[#111111] hover:bg-[#333333]' : 'bg-[#D1CFCA]'"
            >
              <el-icon :size="16"><Promotion /></el-icon>
            </button>
          </div>
          <p class="text-center text-[11px] text-[#999999] mt-3 font-medium tracking-wide">
            CodeSage AI may produce inaccurate information. Please verify critical details.
          </p>
        </div>
      </footer>
    </main>
  </div>
</template>
