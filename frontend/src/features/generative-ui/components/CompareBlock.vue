<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ props: Record<string, any> }>()

interface CompareItem {
  label: string
  left: string
  right: string
}

const items = computed<CompareItem[]>(() => props.props?.items || [])
const leftTitle = computed(() => props.props?.left_title || '方案 A')
const rightTitle = computed(() => props.props?.right_title || '方案 B')
const title = computed(() => props.props?.title || '')
</script>

<template>
  <div class="rounded-xl border border-[#E8E6E1] bg-white overflow-hidden">
    <h4 v-if="title" class="font-serif text-[15px] text-[#111] px-5 pt-4 pb-2">{{ title }}</h4>

    <!-- 表头 -->
    <div class="grid grid-cols-[1fr_1.5fr_1.5fr] border-b border-[#E8E6E1] bg-[#FAFAFA]">
      <div class="px-4 py-2.5 text-[11px] font-medium text-[#999]">对比项</div>
      <div class="px-4 py-2.5 text-[12px] font-semibold text-[#111] border-l border-[#E8E6E1]">{{ leftTitle }}</div>
      <div class="px-4 py-2.5 text-[12px] font-semibold text-[#111] border-l border-[#E8E6E1]">{{ rightTitle }}</div>
    </div>

    <!-- 行 -->
    <div v-for="(item, i) in items" :key="i" class="grid grid-cols-[1fr_1.5fr_1.5fr] border-b border-[#E8E6E1] last:border-0 hover:bg-[#FAFAFA] transition-colors">
      <div class="px-4 py-3 text-[12px] font-medium text-[#555]">{{ item.label }}</div>
      <div class="px-4 py-3 text-[12px] text-[#333] border-l border-[#E8E6E1] leading-relaxed">{{ item.left }}</div>
      <div class="px-4 py-3 text-[12px] text-[#333] border-l border-[#E8E6E1] leading-relaxed">{{ item.right }}</div>
    </div>
  </div>
</template>
