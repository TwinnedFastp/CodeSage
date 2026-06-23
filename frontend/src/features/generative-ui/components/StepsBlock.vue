<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ props: Record<string, any> }>()

interface Step {
  title: string
  description?: string
}

const steps = computed<Step[]>(() => props.props?.steps || [])
const title = computed(() => props.props?.title || '')
const current = computed(() => Number(props.props?.current || 0))

function status(i: number): string {
  if (i < current.value) return 'success'
  if (i === current.value) return 'process'
  return 'wait'
}
</script>

<template>
  <div class="rounded-xl border border-[#E8E6E1] bg-white p-5">
    <h4 v-if="title" class="font-serif text-[15px] text-[#111] mb-5">{{ title }}</h4>
    <el-steps :active="current" finish-status="success" align-center>
      <el-step
        v-for="(step, i) in steps"
        :key="i"
        :title="step.title"
        :description="step.description || ''"
        :status="status(i) as any"
      />
    </el-steps>
  </div>
</template>
