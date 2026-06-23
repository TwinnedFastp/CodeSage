<script setup lang="ts">
import { ref, nextTick, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ChatDotRound, Promotion, User as UserIcon, Link } from '@element-plus/icons-vue'
import { useGenerativeUi } from './useGenerativeUi'
import ComponentRenderer from './ComponentRenderer.vue'

const props = defineProps<{
  sessionId: string | null
  useRag?: boolean
  ragMode?: string
}>()

const emit = defineEmits<{
  (e: 'session-created', id: string): void
}>()

const router = useRouter()

const {
  messages,
  streaming,
  streamComponentChat,
  expandNode,
  regenerateNode,
  callFunction,
  switchVersion,
  loadFunctions,
  loadSessionHistory,
  clearMessages,
} = useGenerativeUi()

const userInput = ref('')
const container = ref<HTMLElement | null>(null)
let pendingSessionId: string | null = null

async function scrollToBottom() {
  await nextTick()
  if (container.value) container.value.scrollTop = container.value.scrollHeight
}

function adjustTextareaHeight(e: Event) {
  const t = e.target as HTMLTextAreaElement
  t.style.height = 'auto'
  t.style.height = Math.min(t.scrollHeight, 200) + 'px'
}

const WELCOME = '你好。这里是 CodeSage 生成式界面。将以组件卡片呈现结构化回答，支持再思考、展开与版本切换。'

async function onSend() {
  const text = userInput.value.trim()
  if (!text || streaming.value) return
  userInput.value = ''
  const ta = container.value?.parentElement?.querySelector<HTMLTextAreaElement>('.gen-textarea')
  if (ta) ta.style.height = 'auto'
  const mode = props.ragMode === 'off' ? 'hybrid' : props.ragMode || 'hybrid'
  const id = await streamComponentChat(text, props.sessionId || undefined, !!props.useRag, mode)
  if (id && id !== props.sessionId) {
    pendingSessionId = id
    emit('session-created', id)
  }
  await scrollToBottom()
}

watch(
  () => props.sessionId,
  (newVal) => {
    if (newVal && newVal === pendingSessionId) {
      pendingSessionId = null
      return
    }
    // 切换会话时加载生成式历史，而不是只清空
    if (newVal) {
      loadSessionHistory(newVal)
    } else {
      clearMessages()
    }
  },
  { immediate: true },
)

onMounted(() => {
  loadFunctions().catch(() => {})
})
</script>

<template>
  <div class="flex-1 flex flex-col relative min-w-0 min-h-0 overflow-hidden bg-[#FAFAFA]">
    <div ref="container" class="flex-1 min-h-0 overflow-y-auto pt-24 pb-56 px-4 md:px-12 scroll-smooth custom-scrollbar">
      <div class="max-w-3xl mx-auto space-y-10 pb-6">
        <div v-if="messages.length === 0" class="text-center py-16">
          <div class="w-12 h-12 mx-auto mb-4 rounded-full bg-[#111111] text-[#FAFAFA] flex items-center justify-center">
            <el-icon :size="20"><ChatDotRound /></el-icon>
          </div>
          <p class="font-serif text-lg text-[#111111]/80 max-w-md mx-auto leading-relaxed">{{ WELCOME }}</p>
        </div>

        <div
          v-for="msg in messages"
          :key="msg.id"
          :class="['flex gap-5 animate-fade-in-up', msg.role === 'user' ? 'flex-row-reverse' : '']"
        >
          <div
            :class="['w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-1', msg.role === 'user' ? 'bg-[#EAE8E0] text-[#111111]' : 'bg-[#111111] text-[#FAFAFA]']"
          >
            <el-icon :size="14"><component :is="msg.role === 'user' ? UserIcon : ChatDotRound" /></el-icon>
          </div>

          <!-- 用户消息气泡 -->
          <div
            v-if="msg.role === 'user'"
            class="max-w-[85%] bg-[#F3F2EE] text-[#111111] px-5 py-3.5 rounded-2xl rounded-tr-sm text-[15px] leading-relaxed whitespace-pre-wrap"
          >{{ msg.content }}</div>

          <!-- 助手消息：组件协议 / 流式文本 / 加载占位 -->
          <div v-else class="max-w-[92%] w-full pt-1">
            <ComponentRenderer
              v-if="msg.protocol"
              :protocol="msg.protocol"
              :versions="msg.versions"
              :current-version-no="msg.currentVersionNo"
              :loading="msg.loading"
              @regenerate="msg.nodeId && regenerateNode(msg.nodeId)"
              @expand="(p) => msg.nodeId && expandNode(msg.nodeId, p.message)"
              @function-call="(p) => p.function_name && callFunction(p.function_name, p.params || {}, p.target_id || msg.nodeId)"
              @switch-version="(p) => msg.nodeId && switchVersion(msg.nodeId, p.versionId)"
            />
            <div v-if="msg.nodeId" class="mt-2">
              <el-button
                size="small"
                text
                @click="router.push({ name: 'node-detail', params: { id: msg.nodeId } })"
                class="!text-[11px] !text-[#777777] hover:!text-[#111111] !p-0 !h-auto"
              >
                <el-icon class="mr-1"><Link /></el-icon>
                查看详情
              </el-button>
            </div>
            <div v-else class="text-[15px] leading-relaxed text-[#111111] flex items-center gap-2">
              <span
                v-if="msg.loading"
                class="inline-block w-2 h-4 bg-[#111111] animate-pulse-cursor align-middle"
              ></span>
              <span
                :class="['whitespace-pre-wrap', msg.error ? 'text-[#b00020]' : '']"
              >{{ msg.content || (msg.loading ? '生成中…' : '') }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <footer class="absolute bottom-0 left-0 right-0 p-4 md:p-8 bg-gradient-to-t from-[#FAFAFA] via-[#FAFAFA] to-transparent pointer-events-none z-20">
      <div class="max-w-3xl mx-auto relative pointer-events-auto">
        <div class="bg-white rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-[#E8E6E1] p-2 pr-14 relative transition-all duration-300 focus-within:shadow-[0_8px_30px_rgb(0,0,0,0.08)] focus-within:border-[#D1CFCA]">
          <textarea
            v-model="userInput"
            class="gen-textarea"
            rows="1"
            :placeholder="props.sessionId ? '生成式提问…（结构化输出）' : '发送后将自动创建会话…'"
            @input="adjustTextareaHeight"
            @keydown.enter.prevent="onSend"
          ></textarea>
          <button
            @click="onSend"
            :disabled="!userInput.trim() || streaming"
            class="absolute right-3 bottom-3 w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 disabled:opacity-30 disabled:cursor-not-allowed text-white"
            :class="userInput.trim() && !streaming ? 'bg-[#111111] hover:bg-[#333333]' : 'bg-[#D1CFCA]'"
          >
            <el-icon :size="16"><Promotion /></el-icon>
          </button>
        </div>
        <p class="text-center text-[11px] text-[#999999] mt-3 font-medium tracking-wide">生成式模式：回复以组件卡片呈现，支持再思考 / 展开 / 版本切换。</p>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.gen-textarea {
  width: 100%;
  max-height: 200px;
  background: transparent;
  border: none;
  outline: none;
  resize: none;
  padding: 12px 16px;
  font-size: 15px;
  line-height: 1.6;
  color: #111111;
  font-family: inherit;
}
.gen-textarea::placeholder {
  color: #aaaaaa;
}
</style>
