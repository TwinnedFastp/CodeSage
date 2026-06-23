<script setup lang="ts">
import { FullScreen } from '@element-plus/icons-vue'

const props = defineProps<{ props: Record<string, any> }>()

const emit = defineEmits<{
  (e: 'open', payload: { html_content: string; title: string }): void
}>()

function open() {
  const html = props.props?.html_content || ''
  const title = props.props?.title || props.props?.name || '详情页'
  if (!html) return
  emit('open', { html_content: html, title })
}
</script>

<template>
  <button
    type="button"
    class="group w-full text-left rounded-2xl bg-gradient-to-br from-[#F3F2EE] to-white border border-[#E8E6E1] p-5 shadow-[0_2px_10px_rgb(0,0,0,0.03)] hover:shadow-[0_8px_24px_rgb(0,0,0,0.08)] hover:border-[#111]/30 transition-all duration-300 hover:-translate-y-0.5"
    @click="open"
  >
    <div class="flex items-start gap-4">
      <div class="shrink-0 w-11 h-11 rounded-xl bg-[#111] text-white flex items-center justify-center group-hover:bg-[#333] transition-colors">
        <el-icon :size="20"><FullScreen /></el-icon>
      </div>
      <div class="flex-1 min-w-0">
        <h4 class="font-serif text-[16px] text-[#111111] leading-snug mb-1 truncate">
          {{ props.props?.title || props.props?.name || '详情页面' }}
        </h4>
        <p v-if="props.props?.description" class="text-[13px] text-[#666] leading-relaxed line-clamp-2">
          {{ props.props?.description }}
        </p>
        <p v-else class="text-[13px] text-[#999] leading-relaxed">点击查看完整交互页面</p>
      </div>
      <span class="shrink-0 text-[11px] text-[#999] group-hover:text-[#111] transition-colors mt-1">
        展开 →
      </span>
    </div>
  </button>
</template>
