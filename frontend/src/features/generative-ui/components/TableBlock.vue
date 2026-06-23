<script setup lang="ts">
const props = defineProps<{
  props: Record<string, any>
}>()

const emit = defineEmits<{
  (e: 'row-click', payload: { rowData: any[]; rowIndex: number; html?: string; title?: string }): void
}>()

function onRowClick(row: any[], index: number) {
  // 如果行数据包含 HTML 内容（用于内联展示），触发事件
  const hasHtmlContent = row.some(cell => typeof cell === 'object' && cell?.html)
  if (hasHtmlContent) {
    const htmlCell = row.find(cell => typeof cell === 'object' && cell?.html)
    emit('row-click', {
      rowData: row,
      rowIndex: index,
      html: htmlCell?.html,
      title: htmlCell?.title || `详情 - ${index + 1}`
    })
  } else {
    // 普通行点击也触发事件，父组件可以根据需要处理
    emit('row-click', { rowData: row, rowIndex: index })
  }
}
</script>

<template>
  <div class="table-block-wrapper">
    <div class="overflow-x-auto rounded-xl border border-[#E8E6E1] custom-scrollbar">
      <table class="w-full text-[13px] border-collapse interactive-table">
        <thead>
          <tr class="bg-[#F3F2EE]">
            <th
              v-for="(h, i) in (props.headers || [])"
              :key="i"
              class="text-left px-4 py-2.5 font-serif font-medium text-[#111111] border-b border-[#E8E6E1]"
            >{{ h }}</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(row, ri) in (props.rows || [])"
            :key="ri"
            class="table-row"
            :class="{ 'has-action': row.some(cell => typeof cell === 'object' && cell?.html) }"
            @click="onRowClick(row, ri)"
          >
            <td
              v-for="(cell, ci) in row"
              :key="ci"
              class="px-4 py-2.5 border-b border-[#E8E6E1] text-[#333333] whitespace-pre-wrap align-top"
              :class="{ 'clickable-cell': typeof cell === 'object' && cell?.html }"
            >
              <!-- 支持对象类型的单元格（带 HTML 和标题） -->
              <template v-if="typeof cell === 'object' && cell !== null && cell.html">
                <span class="cell-with-action">
                  {{ cell.label || cell.value || '' }}
                  <el-icon class="action-icon"><FullScreen /></el-icon>
                </span>
              </template>
              <template v-else>{{ cell }}</template>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.table-block-wrapper {
  background: white;
  border-radius: 12px;
}

.interactive-table {
  cursor: default;
}

.table-row {
  transition: all 0.15s ease;
}

.table-row:hover {
  background: #FAFAFA;
}

/* 可点击的行 */
.table-row.has-action {
  cursor: pointer;
}

.table-row.has-action:hover {
  background: #F0F7FF;
  box-shadow: inset 0 0 0 2px #3B82F620;
}

/* 可点击的单元格 */
.clickable-cell {
  position: relative;
}

.cell-with-action {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #2563EB;
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

/* 自定义滚动条 */
.custom-scrollbar::-webkit-scrollbar {
  height: 6px;
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: #F5F5F5;
  border-radius: 3px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #D1D5DB;
  border-radius: 3px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #9CA3AF;
}
</style>
