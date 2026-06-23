<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ props: Record<string, any> }>()

/**
 * 将内容中的 HTML 标签和 Markdown 语法渲染为富文本。
 * - <p>, <code>, <ul>, <li>, <strong> 等 HTML 标签保留渲染
 * - 行内代码 `` `code` `` 转为 <code>
 * - 纯文本自动换行
 */
const renderedHtml = computed(() => {
  let content = props.props.content || ''

  // 如果内容已经包含 HTML 标签，直接使用（AI 生成的富文本）
  if (/<(p|div|ul|ol|li|code|pre|strong|em|br|table|tr|td|th|h[1-6]|span|a|blockquote)\b/i.test(content)) {
    return content
  }

  // 纯文本处理：转义 HTML 后做基本格式化
  content = content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  // 行内代码
  content = content.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')
  // **加粗**
  content = content.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  // 换行转 <br>（但不在代码块内）
  content = content.replace(/\n/g, '<br>')

  return content
})
</script>

<template>
  <div class="text-block-content" v-html="renderedHtml" />
</template>

<style scoped>
.text-block-content {
  font-size: 15px;
  line-height: 1.75;
  color: #111111;
  word-wrap: break-word;
}

/* 行内代码样式 */
.text-block-content :deep(.inline-code) {
  background: #F3F2EE;
  color: #C7254E;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
  font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
}

/* 继承的 HTML 标签样式优化 */
.text-block-content :deep(p) {
  margin: 0.4em 0;
}

.text-block-content :deep(ul),
.text-block-content :deep(ol) {
  padding-left: 1.5em;
  margin: 0.5em 0;
}

.text-block-content :deep(li) {
  margin: 0.25em 0;
}

.text-block-content :deep(code) {
  background: #F3F2EE;
  color: #C7254E;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
  font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
}

.text-block-content :deep(pre) {
  background: #1E1E1E;
  color: #D4D4D4;
  padding: 14px 18px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 0.6em 0;
  font-size: 13px;
  line-height: 1.6;
}

.text-block-content :deep(pre code) {
  background: none;
  color: inherit;
  padding: 0;
  border-radius: 0;
}

.text-block-content :deep(strong) {
  font-weight: 600;
  color: #000;
}

.text-block-content :deep(blockquote) {
  border-left: 3px solid #3B82F6;
  padding-left: 14px;
  margin: 0.6em 0;
  color: #555;
  font-style: italic;
}
</style>
