<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{ props: Record<string, any> }>()

interface TabItem {
  label: string
  content: string
}

const tabs = computed<TabItem[]>(() => props.props?.tabs || [])
const activeIndex = ref(0)
const title = computed(() => props.props?.title || '')
</script>

<template>
  <div class="rounded-xl border border-[#E8E6E1] bg-white overflow-hidden">
    <h4 v-if="title" class="font-serif text-[15px] text-[#111] px-5 pt-4 pb-2">{{ title }}</h4>

    <!-- Tab 导航 -->
    <div class="flex border-b border-[#E8E6E1] px-3 gap-1 overflow-x-auto custom-scrollbar">
      <button
        v-for="(tab, i) in tabs"
        :key="i"
        class="px-4 py-2.5 text-[13px] font-medium whitespace-nowrap transition-all relative shrink-0"
        :class="activeIndex === i ? 'text-[#111]' : 'text-[#999] hover:text-[#555]'"
        @click="activeIndex = i"
      >
        {{ tab.label }}
        <span
          v-if="activeIndex === i"
          class="absolute bottom-0 left-2 right-2 h-0.5 bg-[#111] rounded-full"
        ></span>
      </button>
    </div>

    <!-- Tab 内容 -->
    <div class="p-5">
      <p class="text-[14px] leading-relaxed text-[#333] whitespace-pre-wrap">{{ tabs[activeIndex]?.content }}</p>
    </div>
  </div>
</template>
