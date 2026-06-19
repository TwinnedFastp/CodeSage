<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { 
  ChatDotRound, 
  Operation, 
  Plus, 
  User, 
  Monitor,
  Setting,
  Fold,
  Expand,
  Promotion
} from '@element-plus/icons-vue'
import axios from 'axios'

// 状态定义
const isMobile = ref(false)
const isSidebarCollapse = ref(false)
const drawerVisible = ref(false)
const userInput = ref('')
const isTyping = ref(false)
const chatContainer = ref<HTMLElement | null>(null)

interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
}

const messages = ref<Message[]>([
  { id: 1, role: 'assistant', content: '你好！我是你的 AI 助手，有什么我可以帮你的吗？' }
])

const chatHistory = ref([
  { id: 1, title: '关于 FastAPI 的讨论' },
  { id: 2, title: '如何学习 Vue 3' },
  { id: 3, title: 'Tailwind CSS 最佳实践' }
])

// 响应式处理
const checkMobile = () => {
  isMobile.value = window.innerWidth < 768
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})

// 滚动到底部
const scrollToBottom = async () => {
  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

// 发送消息
const sendMessage = async () => {
  if (!userInput.value.trim() || isTyping.value) return

  const userMsg = userInput.value
  messages.value.push({
    id: Date.now(),
    role: 'user',
    content: userMsg
  })
  
  userInput.value = ''
  isTyping.value = true
  await scrollToBottom()

  // 添加一个空的助手消息，准备流式填充
  const assistantMsgId = Date.now() + 1
  messages.value.push({
    id: assistantMsgId,
    role: 'assistant',
    content: ''
  })

  try {
    // 调用后端流式接口
    const response = await fetch('http://localhost:8000/api/v1/chat/chatstreaming', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message: userMsg }),
    })

    if (!response.body) return
    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      
      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[DONE]') break
          
          try {
            const parsed = JSON.parse(data)
            const msgIndex = messages.value.findIndex(m => m.id === assistantMsgId)
            if (msgIndex !== -1) {
              messages.value[msgIndex].content += parsed.content
              await scrollToBottom()
            }
          } catch (e) {
            console.error('解析流数据失败', e)
          }
        }
      }
    }
  } catch (error) {
    console.error('发送请求失败', error)
    const msgIndex = messages.value.findIndex(m => m.id === assistantMsgId)
    if (msgIndex !== -1) {
      messages.value[msgIndex].content = '抱歉，发生了错误，请稍后再试。'
    }
  } finally {
    isTyping.value = false
  }
}
</script>

<template>
  <div class="flex h-screen w-screen bg-[#f9fbff] text-[#2c3e50] overflow-hidden font-sans">
    
    <!-- 桌面端侧边栏 -->
    <aside 
      v-if="!isMobile"
      :class="[
        'bg-[#ffffff] border-r border-[#eef2f7] transition-all duration-300 flex flex-col shadow-sm',
        isSidebarCollapse ? 'w-20' : 'w-72'
      ]"
    >
      <div class="p-4 flex items-center justify-between">
        <div v-if="!isSidebarCollapse" class="flex items-center gap-2 font-bold text-xl text-[#409eff]">
          <el-icon :size="24"><ChatDotRound /></el-icon>
          <span>CodeSage</span>
        </div>
        <el-button 
          link 
          @click="isSidebarCollapse = !isSidebarCollapse"
          class="hover:bg-[#f0f4f8] p-2 rounded-lg"
        >
          <el-icon :size="20"><component :is="isSidebarCollapse ? Expand : Fold" /></el-icon>
        </el-button>
      </div>

      <div class="px-4 mb-4">
        <el-button 
          type="primary" 
          class="w-full !rounded-xl !h-12 shadow-md hover:shadow-lg transition-all"
          :icon="Plus"
          @click="messages = [{ id: Date.now(), role: 'assistant', content: '开启新的对话...' }]"
        >
          {{ isSidebarCollapse ? '' : '开启新对话' }}
        </el-button>
      </div>

      <nav class="flex-1 overflow-y-auto px-2 space-y-1">
        <div 
          v-for="chat in chatHistory" 
          :key="chat.id"
          class="flex items-center gap-3 p-3 rounded-xl cursor-pointer hover:bg-[#f0f4f8] transition-colors group"
        >
          <el-icon class="text-gray-400 group-hover:text-[#409eff]"><ChatDotRound /></el-icon>
          <span v-if="!isSidebarCollapse" class="truncate text-sm font-medium">{{ chat.title }}</span>
        </div>
      </nav>

      <div class="p-4 border-t border-[#eef2f7] space-y-2">
        <div class="flex items-center gap-3 p-2 rounded-lg hover:bg-[#f0f4f8] cursor-pointer">
          <el-avatar :size="32" src="https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png" />
          <div v-if="!isSidebarCollapse" class="flex flex-col">
            <span class="text-sm font-semibold">User Admin</span>
            <span class="text-xs text-gray-400">Pro Plan</span>
          </div>
        </div>
      </div>
    </aside>

    <!-- 移动端侧边栏抽屉 -->
    <el-drawer
      v-model="drawerVisible"
      direction="ltr"
      size="280px"
      :with-header="false"
      class="mobile-drawer"
    >
      <div class="flex flex-col h-full bg-white p-4">
        <div class="flex items-center gap-2 font-bold text-xl text-[#409eff] mb-6">
          <el-icon :size="24"><ChatDotRound /></el-icon>
          <span>CodeSage</span>
        </div>
        <el-button type="primary" class="w-full !rounded-xl !h-12 mb-4" :icon="Plus">开启新对话</el-button>
        <div class="flex-1 overflow-y-auto space-y-1">
          <div 
            v-for="chat in chatHistory" 
            :key="chat.id"
            class="flex items-center gap-3 p-3 rounded-xl hover:bg-[#f0f4f8]"
          >
            <el-icon class="text-gray-400"><ChatDotRound /></el-icon>
            <span class="truncate text-sm font-medium">{{ chat.title }}</span>
          </div>
        </div>
      </div>
    </el-drawer>

    <!-- 主聊天区域 -->
    <main class="flex-1 flex flex-col relative min-w-0">
      <!-- 顶部导航 -->
      <header class="h-16 border-b border-[#eef2f7] bg-white/80 backdrop-blur-md flex items-center px-4 justify-between sticky top-0 z-10">
        <div class="flex items-center gap-3">
          <el-button 
            v-if="isMobile" 
            link 
            @click="drawerVisible = true"
            class="p-2"
          >
            <el-icon :size="24"><Operation /></el-icon>
          </el-button>
          <h2 class="font-bold text-lg truncate">当前对话</h2>
        </div>
        <div class="flex items-center gap-2">
          <el-button link><el-icon :size="20"><Monitor /></el-icon></el-button>
          <el-button link><el-icon :size="20"><Setting /></el-icon></el-button>
        </div>
      </header>

      <!-- 消息列表 -->
      <div 
        ref="chatContainer"
        class="flex-1 overflow-y-auto p-4 md:p-8 space-y-6 scroll-smooth"
      >
        <div 
          v-for="msg in messages" 
          :key="msg.id"
          :class="[
            'flex gap-4 max-w-4xl mx-auto',
            msg.role === 'user' ? 'flex-row-reverse' : ''
          ]"
        >
          <div 
            :class="[
              'w-10 h-10 rounded-2xl flex items-center justify-center shrink-0 shadow-sm',
              msg.role === 'user' ? 'bg-[#409eff] text-white' : 'bg-white border border-[#eef2f7]'
            ]"
          >
            <el-icon :size="20"><component :is="msg.role === 'user' ? User : ChatDotRound" /></el-icon>
          </div>
          <div 
            :class="[
              'p-4 rounded-2xl shadow-sm max-w-[85%] leading-relaxed text-[15px]',
              msg.role === 'user' 
                ? 'bg-[#409eff] text-white rounded-tr-none' 
                : 'bg-white border border-[#eef2f7] rounded-tl-none text-[#34495e]'
            ]"
          >
            <div class="whitespace-pre-wrap">{{ msg.content }}</div>
            <div v-if="isTyping && msg.id === messages[messages.length-1].id && msg.role === 'assistant'" class="inline-block w-1 h-4 bg-current animate-pulse ml-1 align-middle"></div>
          </div>
        </div>
      </div>

      <!-- 输入框 -->
      <footer class="p-4 md:p-8 bg-gradient-to-t from-[#f9fbff] via-[#f9fbff] to-transparent">
        <div class="max-w-4xl mx-auto relative group">
          <el-input
            v-model="userInput"
            type="textarea"
            :rows="1"
            autosize
            placeholder="输入您的问题..."
            class="chat-input shadow-xl !rounded-2xl overflow-hidden"
            @keydown.enter.prevent="sendMessage"
          >
            <template #append>
              <el-button 
                type="primary" 
                class="!h-full !rounded-none !bg-[#409eff] hover:!bg-[#66b1ff]"
                @click="sendMessage"
                :disabled="!userInput.trim() || isTyping"
              >
                <el-icon :size="20"><Promotion /></el-icon>
              </el-button>
            </template>
          </el-input>
          
          <div class="absolute right-3 bottom-3 flex items-center gap-2">
             <el-button 
                type="primary" 
                circle
                :icon="Promotion"
                @click="sendMessage"
                :disabled="!userInput.trim() || isTyping"
                class="shadow-md hover:scale-105 transition-transform"
              />
          </div>
        </div>
        <p class="text-center text-xs text-gray-400 mt-4">
          CodeSage AI 可能会产生错误信息，请核实重要信息。
        </p>
      </footer>
    </main>
  </div>
</template>

<style>
.chat-input .el-textarea__inner {
  padding: 16px 60px 16px 16px !important;
  border-radius: 16px !important;
  border: 1px solid #eef2f7 !important;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05) !important;
  resize: none !important;
  font-size: 15px !important;
  line-height: 1.6 !important;
  transition: all 0.3s ease !important;
}

.chat-input .el-textarea__inner:focus {
  border-color: #409eff !important;
  box-shadow: 0 4px 24px rgba(64, 158, 255, 0.15) !important;
}

.mobile-drawer .el-drawer__body {
  padding: 0 !important;
}

::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: #eef2f7;
  border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
  background: #d0d7de;
}

/* 动画 */
.animate-pulse {
  animation: pulse 1s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}
</style>
