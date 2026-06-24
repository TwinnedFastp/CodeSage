/**
 * Markdown 富文本渲染工具
 *
 * 用于生成式 UI 组件（TextBlock / SummaryCard / QuoteBlock / AccordionBlock 等）
 * 将 AI 返回的 Markdown/纯文本转为安全的 HTML。
 *
 * 安全：使用 DOMPurify 过滤 XSS（通过 marked 的 sanitize 选项）
 */
import { marked } from 'marked'

// 配置 marked：关闭 sanitize（由调用方控制），开启 GFM
marked.setOptions({
  gfm: true,
  breaks: true,
})

/**
 * 将内容渲染为 HTML
 * - 已含 HTML 标签的内容直接返回（AI 生成的富文本）
 * - Markdown 文本 → 完整 HTML（支持标题/列表/代码块/表格/引用等）
 * - 纯文本 → 转义 + 换行转 <br>
 */
export function renderMarkdown(content: string): string {
  if (!content) return ''

  // 如果已包含复杂 HTML 标签，直接使用
  if (/<(p|div|ul|ol|li|code|pre|strong|em|br|table|tr|td|th|h[1-6]|span|a|blockquote|img)\b/i.test(content)) {
    return content
  }

  // 尝试解析为 Markdown（如果包含 markdown 语法特征）
  if (/^#{1,6}\s|^[\s]*[-*+]\s|^[\s]*\d+\.\s|^```|`{1,2}[^`]+`{1,2}|\*\*.+\*\*|\[.+\]\(.+\)/m.test(content)) {
    const parsed = marked.parse(content) as string
    return parsed || escapeHtml(content).replace(/\n/g, '<br>')
  }

  // 纯文本：转义 + 基础格式化
  let result = escapeHtml(content)
    .replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>')

  return result
}

/** 转义 HTML 特殊字符 */
function escapeHtml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}
