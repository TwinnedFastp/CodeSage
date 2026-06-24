<script setup lang="ts">
import { computed } from 'vue'
import { renderMarkdown } from '../utils/markdown'

const props = defineProps<{ props: Record<string, any> }>()
const renderedHtml = computed(() => renderMarkdown(props.props?.content || ''))
</script>

<template>
  <div class="summary-card rounded-2xl bg-(--color-surface-soft) border border-(--color-border) p-5 shadow-[0_2px_10px_rgb(0,0,0,0.03)]">
    <h3 v-if="props.props?.title" class="font-serif text-lg text-(--color-ink) mb-2 leading-snug">{{ props.props.title }}</h3>
    <div v-if="props.props?.content" class="text-[14px] leading-relaxed text-(--color-ink-soft) markdown-body" v-html="renderedHtml" />
  </div>
</template>
