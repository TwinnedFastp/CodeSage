<script setup lang="ts">
import { ref, computed } from 'vue'
import { renderMarkdown } from '../utils/markdown'

const props = defineProps<{ props: Record<string, any> }>()

interface TabItem {
  label: string
  content: string
}

const tabs = computed<TabItem[]>(() => props.props?.tabs || [])
const title = computed(() => props.props?.title || '')
const activeName = ref(tabs.value[0]?.label || 'tab0')
</script>

<template>
  <div class="rounded-xl border border-(--color-border) bg-white dark:bg-[var(--el-bg-color-overlay)] p-5">
    <h4 v-if="title" class="font-serif text-[15px] text-(--color-ink) mb-4">{{ title }}</h4>
    <el-tabs v-model="activeName" type="border-card" class="!shadow-none !border-(--color-border) [&_.el-tabs__header]:!bg-(--color-canvas)">
      <el-tab-pane
        v-for="(tab, i) in tabs"
        :key="i"
        :label="tab.label"
        :name="tab.label"
      >
        <div class="text-[14px] leading-relaxed text-(--color-ink-soft) py-2 markdown-body" v-html="renderMarkdown(tab.content || '')" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>
