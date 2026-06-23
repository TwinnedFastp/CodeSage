<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { Loading, ArrowRight } from '@element-plus/icons-vue'

const props = defineProps<{
  rawText?: string
  done?: boolean
}>()

const expanded = ref(true)
const bodyRef = ref<HTMLElement | null>(null)

// 默认展开，生成完成后自动折叠
watch(
  () => props.done,
  (val) => {
    if (val) {
      // 延迟折叠，让用户看到完成的瞬间
      setTimeout(() => {
        expanded.value = false
      }, 600)
    }
  },
)

const displayText = computed(() => {
  const t = props.rawText || ''
  // 截断超长文本避免卡顿，但保留足够内容
  if (t.length > 8000) return t.slice(-8000)
  return t
})

const charCount = computed(() => (props.rawText || '').length)

function toggle() {
  expanded.value = !expanded.value
}

// 自动滚动到底部（展开状态时）
watch(
  () => props.rawText,
  async () => {
    if (expanded.value) {
      await nextTick()
      if (bodyRef.value) {
        bodyRef.value.scrollTop = bodyRef.value.scrollHeight
      }
    }
  },
)
</script>

<template>
  <div class="rounded-2xl border border-[#E8E6E1] bg-[#FAFAFA] overflow-hidden transition-all duration-300">
    <!-- 头部：可点击折叠 -->
    <button
      class="w-full flex items-center gap-3 px-5 py-4 text-left hover:bg-[#F3F2EE] transition-colors"
      @click="toggle"
    >
      <!-- 旋转动画的箭头 -->
      <el-icon :size="14" class="text-[#777] transition-transform duration-300" :class="expanded ? 'rotate-90' : ''">
        <ArrowRight />
      </el-icon>

      <!-- 思考图标 + 标题 -->
      <div class="flex items-center gap-2.5 flex-1 min-w-0">
        <div
          class="w-6 h-6 rounded-full flex items-center justify-center shrink-0 transition-all duration-300"
          :class="done ? 'bg-[#111] text-white' : 'bg-[#111]/8 text-[#111]'"
        >
          <el-icon :size="12" :class="done ? '' : 'animate-spin'">
            <Loading />
          </el-icon>
        </div>
        <span class="text-[13px] font-medium text-[#111] truncate">
          {{ done ? '思考完成' : 'AI 正在思考中…' }}
        </span>
      </div>

      <!-- 字数统计 -->
      <span class="text-[11px] text-[#999] tabular-nums shrink-0">
        {{ charCount }} 字
      </span>
    </button>

    <!-- 折叠内容 -->
    <transition
      enter-active-class="transition-all duration-300 ease-out"
      leave-active-class="transition-all duration-200 ease-in"
      enter-from-class="max-h-0 opacity-0"
      enter-to-class="max-h-[400px] opacity-100"
      leave-from-class="max-h-[400px] opacity-100"
      leave-to-class="max-h-0 opacity-0"
    >
      <div v-show="expanded" class="overflow-hidden">
        <div
          ref="bodyRef"
          class="px-5 pb-4 pt-1 max-h-[400px] overflow-y-auto custom-scrollbar border-t border-[#E8E6E1]/50"
        >
          <pre class="text-[11px] leading-relaxed text-[#666] font-mono whitespace-pre-wrap break-all">{{ displayText || '等待生成…' }}</pre>
        </div>
      </div>
    </transition>
  </div>
</template>
