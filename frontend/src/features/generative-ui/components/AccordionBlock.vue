<script setup lang="ts">
import { ref, computed } from 'vue'
import { ArrowDown } from '@element-plus/icons-vue'

const props = defineProps<{ props: Record<string, any> }>()

interface AccordionItem {
  title: string
  content: string
  defaultOpen?: boolean
}

const items = computed<AccordionItem[]>(() => props.props?.items || [])
const title = computed(() => props.props?.title || '')

const openSet = ref<Set<number>>(new Set())

// 初始化默认展开项
items.value.forEach((item, i) => {
  if (item.defaultOpen) openSet.value.add(i)
})

function toggle(i: number) {
  if (openSet.value.has(i)) openSet.value.delete(i)
  else openSet.value.add(i)
}
</script>

<template>
  <div class="rounded-xl border border-[#E8E6E1] bg-white overflow-hidden">
    <h4 v-if="title" class="font-serif text-[15px] text-[#111] px-5 pt-4 pb-2">{{ title }}</h4>

    <div class="divide-y divide-[#E8E6E1]">
      <div v-for="(item, i) in items" :key="i">
        <button
          class="w-full flex items-center justify-between px-5 py-3.5 text-left hover:bg-[#FAFAFA] transition-colors"
          @click="toggle(i)"
        >
          <span class="text-[13px] font-semibold text-[#111]">{{ item.title }}</span>
          <el-icon :size="14" class="text-[#999] transition-transform duration-300" :class="openSet.has(i) ? 'rotate-180' : ''">
            <ArrowDown />
          </el-icon>
        </button>
        <transition
          enter-active-class="transition-all duration-300 ease-out"
          leave-active-class="transition-all duration-200 ease-in"
          enter-from-class="max-h-0 opacity-0"
          enter-to-class="max-h-96 opacity-100"
          leave-from-class="max-h-96 opacity-100"
          leave-to-class="max-h-0 opacity-0"
        >
          <div v-show="openSet.has(i)" class="overflow-hidden">
            <p class="px-5 pb-4 text-[13px] leading-relaxed text-[#555] whitespace-pre-wrap">{{ item.content }}</p>
          </div>
        </transition>
      </div>
    </div>
  </div>
</template>
