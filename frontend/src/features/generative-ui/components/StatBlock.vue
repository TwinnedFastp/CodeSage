<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ props: Record<string, any> }>()

interface StatItem {
  label: string
  value: string | number
  unit?: string
  trend?: string
  trendUp?: boolean
}

const stats = computed<StatItem[]>(() => props.props?.stats || [])
const title = computed(() => props.props?.title || '')
</script>

<template>
  <div>
    <h4 v-if="title" class="font-serif text-[15px] text-[#111] mb-3">{{ title }}</h4>
    <div class="grid gap-3" :style="{ gridTemplateColumns: `repeat(${Math.min(stats.length, 4)}, minmax(0, 1fr))` }">
      <div
        v-for="(stat, i) in stats"
        :key="i"
        class="rounded-xl border border-[#E8E6E1] bg-white p-4 hover:shadow-md transition-shadow"
      >
        <div class="text-[11px] text-[#999] mb-1.5 truncate">{{ stat.label }}</div>
        <div class="flex items-baseline gap-1">
          <span class="text-[24px] font-bold text-[#111] tabular-nums leading-none">{{ stat.value }}</span>
          <span v-if="stat.unit" class="text-[12px] text-[#777]">{{ stat.unit }}</span>
        </div>
        <div v-if="stat.trend" class="mt-1.5 text-[11px] flex items-center gap-1" :class="stat.trendUp ? 'text-green-600' : 'text-red-500'">
          <span>{{ stat.trendUp ? '↑' : '↓' }}</span>
          <span>{{ stat.trend }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
