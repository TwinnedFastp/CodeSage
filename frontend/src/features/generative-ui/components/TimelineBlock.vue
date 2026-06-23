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
    <h4 v-if="title" class="font-serif text-[15px] text-[#111] mb-4">{{ title }}</h4>
    <el-timeline>
      <el-timeline-item
        v-for="(item, i) in items"
        :key="i"
        :timestamp="item.time"
        placement="top"
        :type="(item.status === 'done' ? 'success' : item.status === 'active' ? 'primary' : 'info') as any"
        :hollow="item.status === 'pending'"
      >
        <div class="text-[13px] font-semibold text-[#111] mb-1">{{ item.title }}</div>
        <p v-if="item.description" class="text-[12px] text-[#666] leading-relaxed">{{ item.description }}</p>
      </el-timeline-item>
    </el-timeline>
  </div>
</template>
