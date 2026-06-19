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
  { id: 1, role: 'assistant', content: '你好。我是 CodeSage，你的代码工程师。有什么我可以帮你的吗？' }
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

// 自动调整文本框高度
const adjustTextareaHeight = (e: Event) => {
  const target = e.target as HTMLTextAreaElement;
  target.style.height = 'auto';
  target.style.height = Math.min(target.scrollHeight, 200) + 'px';
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
  // Reset textarea height
  const textarea = document.querySelector('textarea')
  if (textarea) textarea.style.height = 'auto'
  
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
      messages.value[msgIndex].content = '抱歉，连接到 CodeSage 服务器时发生了错误。请确保后端服务正在运行。'
    }
  } finally {
    isTyping.value = false
  }
}
</script>

<template>
  <!-- 整体采用极致的极简/杂志风格，去除多余的边框和强烈的色块 -->
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
          @click="messages = [{ id: Date.now(), role: 'assistant', content: '你好。我是 CodeSage，你的代码工程师。有什么我可以帮你的吗？' }]"
        >
          <el-icon><Plus /></el-icon>
          <span v-if="!isSidebarCollapse" class="text-sm font-medium">New Conversation</span>
        </button>
      </div>

      <nav class="flex-1 overflow-y-auto px-3 py-2 space-y-1 custom-scrollbar">
        <div 
          v-for="chat in chatHistory" 
          :key="chat.id"
          class="flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-pointer hover:bg-[#E8E6E1] transition-colors group"
        >
          <div class="w-1.5 h-1.5 rounded-full bg-[#D1CFCA] group-hover:bg-[#111111] transition-colors"></div>
          <span v-if="!isSidebarCollapse" class="truncate text-[13px] font-medium text-[#444444] group-hover:text-[#111111]">{{ chat.title }}</span>
        </div>
      </nav>

      <div class="p-5 border-t border-[#E8E6E1]/50">
        <div class="flex items-center gap-3 cursor-pointer group">
          <div class="w-9 h-9 rounded-full bg-[#E8E6E1] flex items-center justify-center text-[#555555] group-hover:bg-[#111111] group-hover:text-white transition-colors">
            <el-icon><User /></el-icon>
          </div>
          <div v-if="!isSidebarCollapse" class="flex flex-col">
            <span class="text-[13px] font-semibold">User Admin</span>
            <span class="text-[11px] text-[#777777]">Pro Plan</span>
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
      class="!bg-[#F3F2EE]"
    >
      <div class="flex flex-col h-full p-6">
        <div class="flex items-center gap-3 font-semibold text-lg tracking-tight mb-8">
          <div class="w-6 h-6 bg-[#111111] rounded-full flex items-center justify-center text-[#F3F2EE]">
            <el-icon :size="14"><ChatDotRound /></el-icon>
          </div>
          <span>CodeSage</span>
        </div>
        <button class="w-full h-11 bg-[#111111] hover:bg-[#333333] text-white rounded-full flex items-center justify-center gap-2 mb-8" @click="messages = [{ id: Date.now(), role: 'assistant', content: '你好。我是 CodeSage，你的代码工程师。有什么我可以帮你的吗？' }]; drawerVisible = false">
          <el-icon><Plus /></el-icon>
          <span class="text-sm font-medium">New Conversation</span>
        </button>
        <div class="flex-1 overflow-y-auto space-y-1">
          <div 
            v-for="chat in chatHistory" 
            :key="chat.id"
            class="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-[#E8E6E1]"
          >
            <div class="w-1.5 h-1.5 rounded-full bg-[#D1CFCA]"></div>
            <span class="truncate text-[13px] font-medium text-[#444444]">{{ chat.title }}</span>
          </div>
        </div>
      </div>
    </el-drawer>

    <!-- 主聊天区域 -->
    <main class="flex-1 flex flex-col relative min-w-0 bg-[#FAFAFA]">
      <!-- 顶部导航 -->
      <header class="h-20 flex items-center px-6 justify-between absolute top-0 left-0 right-0 z-10 bg-gradient-to-b from-[#FAFAFA] to-transparent">
        <div class="flex items-center gap-4">
          <button 
            v-if="isMobile" 
            @click="drawerVisible = true"
            class="p-2 -ml-2 text-[#555555]"
          >
            <el-icon :size="22"><Operation /></el-icon>
          </button>
          <h2 class="font-serif text-xl tracking-tight text-[#111111]/80">Current Session</h2>
        </div>
        <div class="flex items-center gap-4 text-[#777777]">
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
              <el-icon :size="14"><component :is="msg.role === 'user' ? User : ChatDotRound" /></el-icon>
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
                class="inline-block w-2 h-4 bg-[#111111] animate-pulse ml-1 align-middle"
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
              placeholder="Ask anything..."
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

<style>
/* 隐藏原生 textarea 滚动条 */
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #E8E6E1;
  border-radius: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #D1CFCA;
}

/* 动画 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fade-in-up {
  animation: fadeInUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

.animate-pulse {
  animation: pulse 1s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}
</style>
