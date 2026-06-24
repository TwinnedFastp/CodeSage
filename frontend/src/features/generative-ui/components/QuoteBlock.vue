<script setup lang="ts">
import { computed } from 'vue'
import { renderMarkdown } from '../utils/markdown'

const props = defineProps<{ props: Record<string, any> }>()
const renderedHtml = computed(() => renderMarkdown(props.props?.content || ''))
</script>

<template>
  <blockquote class="border-l-2 border-(--color-accent) pl-4 py-1 text-[15px] leading-relaxed text-(--color-ink-soft) italic">
    <span class="markdown-body" v-html="renderedHtml" />
    <footer v-if="props.props?.cite" class="mt-1 text-[12px] not-italic text-(--color-subtle)">— {{ props.props.cite }}</footer>
  </blockquote>
</template>
