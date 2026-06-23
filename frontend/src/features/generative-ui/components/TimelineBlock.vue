<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ props: Record<string, any> }>()

interface TimelineItem {
  time?: string
  title: string
  description?: string
  status?: 'done' | 'active' | 'pending'
}

const items = computed<TimelineItem[]>(() => props.props?.items || [])
const title = computed(() => props.props?.title || '')
</script>

<template>
  <div class="rounded-xl border border-[#E8E6E1] bg-white p-5">
    <h4 v-if="title" class="font-serif text-[15px] text-[#111] mb-5">{{ title }}</h4>
    <div class="relative pl-6">
      <!-- 竖线 -->
      <div class="absolute left-[7px] top-2 bottom-2 w-px bg-[#E8E6E1]"></div>

      <div v-for="(item, i) in items" :key="i" class="relative pb-6 last:pb-0">
        <!-- 节点圆点 -->
        <div
          class="absolute -left-6 top-0.5 w-4 h-4 rounded-full border-2 flex items-center justify-center transition-all"
          :class="{
            'bg-[#111] border-[#111]': item.status === 'done' || (!item.status && i < items.length - 1),
            'bg-white border-[#111] ring-4 ring-[#111]/10': item.status === 'active',
            'bg-white border-[#DDD]': item.status === 'pending'
          }"
        >
          <div v-if="item.status === 'active'" class="w-1.5 h-1.5 rounded-full bg-[#111] animate-pulse"></div>
        </div>

        <div class="ml-2">
          <div class="flex items-baseline gap-2 mb-1">
            <span v-if="item.time" class="text-[11px] text-[#999] tabular-nums shrink-0">{{ item.time }}</span>
            <span class="text-[13px] font-semibold text-[#111]">{{ item.title }}</span>
          </div>
          <p v-if="item.description" class="text-[12px] text-[#666] leading-relaxed">{{ item.description }}</p>
        </div>
      </div>
    </div>
  </div>
</template>
