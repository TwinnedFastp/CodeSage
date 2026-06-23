<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ props: Record<string, any> }>()

interface Step {
  title: string
  description?: string
}

const steps = computed<Step[]>(() => props.props?.steps || [])
const title = computed(() => props.props?.title || '')
const current = computed(() => Number(props.props?.current || steps.value.length))
</script>

<template>
  <div class="rounded-xl border border-[#E8E6E1] bg-white p-5">
    <h4 v-if="title" class="font-serif text-[15px] text-[#111] mb-5">{{ title }}</h4>

    <div class="flex items-start">
      <div v-for="(_step, i) in steps" :key="i" class="flex-1 flex items-start" :class="{ 'last:flex-none': i === steps.length - 1 }">
        <!-- 圆圈 + 序号 -->
        <div class="flex flex-col items-center shrink-0">
          <div
            class="w-8 h-8 rounded-full flex items-center justify-center text-[12px] font-bold transition-all"
            :class="i < current ? 'bg-[#111] text-white' : i === current ? 'bg-white border-2 border-[#111] text-[#111] ring-4 ring-[#111]/10' : 'bg-white border-2 border-[#DDD] text-[#999]'"
          >
            {{ i < current ? '✓' : i + 1 }}
          </div>
        </div>

        <!-- 连接线 -->
        <div v-if="i < steps.length - 1" class="flex-1 h-0.5 mx-2 mt-4 rounded-full" :class="i < current ? 'bg-[#111]' : 'bg-[#E8E6E1]'"></div>

        <!-- 文本（绝对定位避免影响连接线） -->
      </div>
    </div>

    <!-- 步骤文本：单独一行 -->
    <div class="flex items-start mt-3">
      <div v-for="(step, i) in steps" :key="'txt' + i" class="flex-1 px-1">
        <div class="text-[12px] font-semibold text-[#111] mb-0.5 truncate">{{ step.title }}</div>
        <p v-if="step.description" class="text-[11px] text-[#777] leading-relaxed line-clamp-2">{{ step.description }}</p>
      </div>
    </div>
  </div>
</template>
