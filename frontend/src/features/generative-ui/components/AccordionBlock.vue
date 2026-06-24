<script setup lang="ts">
import { ref, computed } from 'vue'
import { renderMarkdown } from '../utils/markdown'

const props = defineProps<{ props: Record<string, any> }>()

interface AccordionItem {
  title: string
  content: string
  defaultOpen?: boolean
}

const items = computed<AccordionItem[]>(() => props.props?.items || [])
const title = computed(() => props.props?.title || '')

const activeNames = ref<string[]>(
  items.value.filter((i) => i.defaultOpen).map((_, idx) => `item${idx}`),
)
</script>

<template>
  <div class="rounded-xl border border-(--color-border) bg-white dark:bg-[var(--el-bg-color-overlay)] p-5">
    <h4 v-if="title" class="font-serif text-[15px] text-(--color-ink) mb-4">{{ title }}</h4>
    <el-collapse v-model="activeNames" class="!border-0">
      <el-collapse-item
        v-for="(item, i) in items"
        :key="i"
        :title="item.title"
        :name="`item${i}`"
        class="[&_.el-collapse-item__header]:!text-[13px] [&_.el-collapse-item__header]:!font-semibold [&_.el-collapse-item__header]:!border-b-(--color-border)"
      >
        <div class="text-[13px] leading-relaxed text-(--color-muted) py-2 markdown-body" v-html="renderMarkdown(item.content || '')" />
      </el-collapse-item>
    </el-collapse>
  </div>
</template>
