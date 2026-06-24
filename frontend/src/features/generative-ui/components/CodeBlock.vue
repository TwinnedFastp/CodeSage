<script setup lang="ts">
import { DocumentCopy, FullScreen } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const props = defineProps<{ props: Record<string, any> }>()

const language = (props.props.language || 'text').toString().toLowerCase() || 'text'
const code = String(props.props.code || '')

function copyCode() {
  navigator.clipboard.writeText(code).then(() => {
    ElMessage.success('已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

function expandCode() {
  const w = window.open('', '_blank', 'width=900,height=700,menubar=no,toolbar=no')
  if (w) {
    const escaped = code
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
    w.document.write(`<!DOCTYPE html><html><head><meta charset="UTF-8"><title>代码片段</title></head><body style="margin:0;padding:24px;background:#111827;color:#f3f4f6;font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace;white-space:pre;">${escaped}</body></html>`)
    w.document.close()
  }
}
</script>

<template>
  <div class="code-block-card">
    <div class="code-block-header">
      <span class="code-block-lang">{{ language }}</span>
      <div class="code-block-actions">
        <button type="button" class="code-block-btn" title="复制" @click="copyCode">
          <el-icon :size="14"><DocumentCopy /></el-icon>
        </button>
        <button type="button" class="code-block-btn" title="新窗口展开" @click="expandCode">
          <el-icon :size="14"><FullScreen /></el-icon>
        </button>
      </div>
    </div>
    <div class="code-block-body">
      <pre class="custom-scrollbar"><code :class="`language-${language}`">{{ code }}</code></pre>
    </div>
  </div>
</template>

<style scoped>
/* 自包含样式：保证组件在 .markdown-body 容器外（生成式模式）也能正确渲染，
   并通过 CSS 变量自动适配暗色主题。与 style.css 中 .markdown-body :deep(.code-block-card) 保持一致。 */
.code-block-card {
  border: 1px solid var(--color-border);
  border-radius: 12px;
  overflow: hidden;
  margin: 0.75rem 0;
  background: var(--color-surface);
}

.code-block-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 0.75rem;
  background: var(--color-surface-soft);
  border-bottom: 1px solid var(--color-border);
}

.code-block-lang {
  font-size: 0.75rem;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  color: var(--color-muted);
  text-transform: lowercase;
  letter-spacing: 0.02em;
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
}

.code-block-actions {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.code-block-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: none;
  background: transparent;
  color: var(--color-subtle);
  cursor: pointer;
  transition: all 0.15s ease;
}

.code-block-btn:hover {
  background: var(--color-surface);
  color: var(--color-ink);
}

.code-block-body {
  padding: 1rem 1.25rem;
  overflow-x: auto;
  background: var(--color-surface);
}

.code-block-body pre {
  background: transparent;
  padding: 0;
  margin: 0;
  border-radius: 0;
  overflow: visible;
}

.code-block-body pre code {
  background: transparent;
  padding: 0;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.85rem;
  line-height: 1.6;
  color: var(--color-ink);
}
</style>
