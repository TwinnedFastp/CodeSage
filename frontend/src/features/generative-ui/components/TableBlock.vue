<script setup lang="ts">
const props = defineProps<{
  props: Record<string, any>
}>()

interface CellData {
  html?: string
  title?: string
  label?: string
  value?: string | number
  [key: string]: any
}

type CellValue = string | number | CellData

const emit = defineEmits<{
  (e: 'row-click', payload: { rowData: CellValue[]; rowIndex: number; html?: string; title?: string }): void
}>()

function onRowClick(row: CellValue[], index: number) {
  // 如果行数据包含 HTML 内容（用于内联展示），触发事件
  const hasHtmlContent = row.some((cell: CellValue) => typeof cell === 'object' && cell !== null && (cell as CellData)?.html)
  if (hasHtmlContent) {
    const htmlCell = row.find((cell: CellValue) => typeof cell === 'object' && cell !== null && (cell as CellData)?.html)
    emit('row-click', {
      rowData: row,
      rowIndex: index,
      html: (htmlCell as CellData)?.html,
      title: (htmlCell as CellData)?.title || `详情 - ${index + 1}`
    })
  } else {
    // 普通行点击也触发事件，父组件可以根据需要处理（如触发 AI 交互）
    emit('row-click', { rowData: row, rowIndex: index })
  }
}
</script>

<template>
  <div class="table-block-wrapper">
    <div class="overflow-x-auto rounded-xl border border-(--color-border) custom-scrollbar">
      <table class="w-full text-[13px] border-collapse interactive-table table-fixed">
        <thead>
          <tr class="bg-(--color-surface-soft)">
            <th
              v-for="(h, i) in (props.props.headers || [])"
              :key="i"
              class="text-left font-serif font-medium text-(--color-ink) border-b border-(--color-border) p-0 align-top"
            >
              <div class="table-cell-content table-cell-content-header">{{ h }}</div>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(row, ri) in (props.props.rows || [])"
            :key="ri"
            class="table-row interactive-row"
            :class="{ 'has-action': row.some((cell: CellValue) => typeof cell === 'object' && cell !== null && (cell as CellData)?.html) }"
            @click="onRowClick(row, Number(ri))"
          >
            <td
              v-for="(cell, ci) in row"
              :key="ci"
              class="border-b border-(--color-border) text-(--color-ink-soft) align-top p-0"
              :class="{ 'clickable-cell': typeof cell === 'object' && cell !== null && (cell as CellData)?.html }"
            >
              <!-- 支持对象类型的单元格（带 HTML 和标题） -->
              <template v-if="typeof cell === 'object' && cell !== null && (cell as CellData).html">
                <div class="table-cell-content">
                  <span class="cell-with-action">
                    {{ (cell as CellData).label || (cell as CellData).value || '' }}
                    <el-icon class="action-icon"><FullScreen /></el-icon>
                  </span>
                </div>
              </template>
              <template v-else>
                <div class="table-cell-content">{{ cell }}</div>
              </template>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.table-block-wrapper {
  background: var(--color-surface);
  border-radius: 12px;
}

.interactive-table {
  cursor: default;
  table-layout: fixed;
}

.table-row {
  transition: all 0.15s ease;
}

.table-row:hover {
  background: var(--color-surface-soft);
}

/* 所有行可点击 */
.table-row.interactive-row {
  cursor: pointer;
}

.table-row.interactive-row:hover {
  background: color-mix(in srgb, var(--color-accent) 8%, var(--color-surface-soft));
}

/* 可点击的行 */
.table-row.has-action {
  cursor: pointer;
}

.table-row.has-action:hover {
  background: color-mix(in srgb, var(--color-accent) 8%, var(--color-surface-soft));
  box-shadow: inset 0 0 0 2px color-mix(in srgb, var(--color-accent) 25%, transparent);
}

/* 可点击的单元格 */
.clickable-cell {
  position: relative;
}

.cell-with-action {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--color-accent);
  font-weight: 500;
}

.action-icon {
  font-size: 12px;
  opacity: 0.6;
  transition: opacity 0.15s ease;
}

.cell-with-action:hover .action-icon {
  opacity: 1;
}

/* 单元格内容：超出时单元格内横向滚动 */
.table-cell-content {
  max-width: 100%;
  max-height: 120px;
  overflow-x: auto;
  overflow-y: auto;
  padding: 0.5rem 0.75rem;
  white-space: nowrap;
  font-size: 0.95em;
  line-height: 1.5;
}

.table-cell-content-header {
  white-space: normal;
  color: var(--color-muted);
  font-weight: 500;
}

/* 自定义滚动条 */
.custom-scrollbar::-webkit-scrollbar {
  height: 4px;
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: var(--color-border-strong);
  border-radius: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: var(--color-subtle);
}
</style>
