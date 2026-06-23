<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  props: {
    title?: string
    value?: number
    max?: number
    type?: 'primary' | 'success' | 'warning' | 'danger'
    showLabel?: boolean
    size?: 'small' | 'medium' | 'large'
  }
}>()

const percentage = computed(() => {
  const max = props.props.max || 100
  const value = props.props.value || 0
  return Math.min(100, Math.max(0, (value / max) * 100))
})

const barColor = computed(() => {
  const colors: Record<string, string> = {
    primary: '#111',
    success: '#22C55E',
    warning: '#F59E0B',
    danger: '#EF4444'
  }
  return colors[props.props.type || 'primary']
})

const height = computed(() => {
  const heights: Record<string, string> = {
    small: '4px',
    medium: '8px',
    large: '12px'
  }
  return heights[props.props.size || 'medium']
})
</script>

<template>
  <div class="space-y-2">
    <div v-if="props.title" class="flex items-center justify-between">
      <span class="text-sm text-[#333]">{{ props.title }}</span>
      <span v-if="props.showLabel !== false" class="text-sm font-medium text-[#111]">
        {{ Math.round(percentage) }}%
      </span>
    </div>
    <div class="w-full bg-[#E8E6E1] rounded-full overflow-hidden" :style="{ height }">
      <div
        class="h-full rounded-full transition-all duration-500 ease-out"
        :style="{
          width: `${percentage}%`,
          backgroundColor: barColor
        }"
      />
    </div>
  </div>
</template>