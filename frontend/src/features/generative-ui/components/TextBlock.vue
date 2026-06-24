<script setup lang="ts">
import { computed } from 'vue'
import { renderMarkdown } from '../utils/markdown'

const props = defineProps<{ props: Record<string, any> }>()

const renderedHtml = computed(() => renderMarkdown(props.props.content || ''))
</script>

<template>
  <div class="text-block-content markdown-body" v-html="renderedHtml" />
</template>

<style scoped>
.text-block-content {
  font-size: 15px;
  line-height: 1.75;
  color: var(--color-ink);
  word-wrap: break-word;
}

/* 行内代码样式 */
.text-block-content :deep(.inline-code),
.text-block-content :deep(code:not(pre code)) {
  background: var(--color-surface-soft, #F3F2EE);
  color: var(--color-accent, #C7254E);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
  font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
}

/* 继承的 HTML 标签样式 */
.text-block-content :deep(p) {
  margin: 0.5em 0;
}

.text-block-content :deep(p:first-child) {
  margin-top: 0;
}

.text-block-content :deep(p:last-child) {
  margin-bottom: 0;
}

.text-block-content :deep(ul),
.text-block-content :deep(ol) {
  padding-left: 1.5em;
  margin: 0.6em 0;
}

.text-block-content :deep(li) {
  margin: 0.25em 0;
}

.text-block-content :deep(li > p) {
  margin: 0.25em 0;
}

.text-block-content :deep(pre) {
  background: #1E1E1E;
  color: #D4D4D4;
  padding: 14px 18px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 0.7em 0;
  font-size: 13px;
  line-height: 1.6;
}

.text-block-content :deep(pre code) {
  background: none;
  color: inherit;
  padding: 0;
  border-radius: 0;
  font-size: inherit;
}

.text-block-content :deep(strong) {
  font-weight: 600;
  color: var(--color-ink, #000);
}

.text-block-content :deep(blockquote) {
  border-left: 3px solid var(--color-accent, #3B82F6);
  padding-left: 14px;
  margin: 0.7em 0;
  color: var(--color-muted, #555);
  font-style: italic;
}

.text-block-content :deep(h1),
.text-block-content :deep(h2),
.text-block-content :deep(h3),
.text-block-content :deep(h4) {
  font-weight: 700;
  margin: 1em 0 0.4em;
  line-height: 1.3;
  color: var(--color-ink, #111);
}

.text-block-content :deep(h1) { font-size: 1.4em; }
.text-block-content :deep(h2) { font-size: 1.2em; }
.text-block-content :deep(h3) { font-size: 1.1em; }

.text-block-content :deep(a) {
  color: var(--color-accent, #3B82F6);
  text-decoration: underline;
  text-underline-offset: 2px;
}

.text-block-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 0.7em 0;
  font-size: 14px;
}

.text-block-content :deep(th),
.text-block-content :deep(td) {
  border: 1px solid var(--color-border, #E8E6E1);
  padding: 8px 12px;
  text-align: left;
}

.text-block-content :deep(th) {
  background: var(--color-surface-soft, #F3F2EE);
  font-weight: 600;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* 暗色模式适配 */
:root[data-theme="dark"] .text-block-content :deep(pre) {
  background: #1a1a2e;
  color: #e0e0e0;
}
</style>
