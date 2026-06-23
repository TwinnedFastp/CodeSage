<script setup lang="ts">
import { computed } from 'vue'
import { FullScreen } from '@element-plus/icons-vue'

const props = defineProps<{
  props: Record<string, any>
}>()

const emit = defineEmits<{
  (e: 'item-click', payload: { item: any; index: number; html?: string; title?: string }): void
}>()

interface CompareItem {
  label: string
  left: string | { value?: string; html?: string; label?: string }
  right: string | { value?: string; html?: string; label?: string }
}

const items = computed<CompareItem[]>(() => props.props?.items || [])
const leftTitle = computed(() => props.props?.left_title || '方案 A')
const rightTitle = computed(() => props.props?.right_title || '方案 B')
const title = computed(() => props.props?.title || '')

function onItemClick(item: CompareItem, index: number) {
  // 检查是否有 HTML 内容可展示
  const leftHtml = typeof item.left === 'object' ? item.left.html : null
  const rightHtml = typeof item.right === 'object' ? item.right.html : null

  // 始终触发点击事件，让父组件决定如何处理
  emit('item-click', {
    item,
    index,
    html: leftHtml || rightHtml || '',
    title: `${item.label} - 详情`,
  })
}

// 判断单元格是否可点击（有 HTML 内容时显示特殊样式）
function isClickable(value: any): boolean {
  return typeof value === 'object' && value !== null && value.html
}

// 所有行都视为可交互
function isRowInteractive(): boolean {
  return true
}
</script>

<template>
  <div class="compare-block-wrapper">
    <h4 v-if="title" class="compare-title">{{ title }}</h4>
    <div class="compare-table">
      <!-- 表头 -->
      <div class="compare-header">
        <div class="compare-cell header-cell">对比项</div>
        <div class="compare-cell header-cell">{{ leftTitle }}</div>
        <div class="compare-cell header-cell">{{ rightTitle }}</div>
      </div>

      <!-- 数据行 -->
      <div
        v-for="(item, index) in items"
        :key="index"
        class="compare-row interactive-row"
        :class="{ 'has-action': isClickable(item.left) || isClickable(item.right) }"
        @click="onItemClick(item, index)"
      >
        <div class="compare-cell field-cell">
          {{ item.label }}
        </div>
        <div class="compare-cell value-cell" :class="{ clickable: isClickable(item.left) }">
          <template v-if="isClickable(item.left)">
            <span class="cell-action">
              {{ (item.left as any).label || (item.left as any).value || '' }}
              <el-icon class="cell-icon"><FullScreen /></el-icon>
            </span>
          </template>
          <template v-else>{{ item.left }}</template>
        </div>
        <div class="compare-cell value-cell" :class="{ clickable: isClickable(item.right) }">
          <template v-if="isClickable(item.right)">
            <span class="cell-action">
              {{ (item.right as any).label || (item.right as any).value || '' }}
              <el-icon class="cell-icon"><FullScreen /></el-icon>
            </span>
          </template>
          <template v-else>{{ item.right }}</template>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.compare-block-wrapper {
  background: white;
  border-radius: 12px;
  overflow: hidden;
}

.compare-title {
  font-family: Georgia, serif;
  font-size: 15px;
  color: #111;
  padding: 16px 20px 12px;
  font-weight: 600;
}

.compare-table {
  border-top: 1px solid #E8E6E1;
}

.compare-header {
  display: grid;
  grid-template-columns: 140px 1fr 1fr;
  background: #F3F2EE;
}

.compare-row {
  display: grid;
  grid-template-columns: 140px 1fr 1fr;
  border-bottom: 1px solid #F0EFE9;
  transition: all 0.15s ease;
}

.compare-row:hover {
  background: #FAFAFA;
}

/* 所有行可点击 */
.compare-row.interactive-row {
  cursor: pointer;
}

.compare-row.interactive-row:hover {
  background: #F0F7FF;
}

.compare-row.has-action {
  cursor: pointer;
}

.compare-row.has-action:hover {
  background: #F0F7FF;
}

.compare-cell {
  padding: 14px 18px;
  font-size: 13px;
  color: #333;
  border-right: 1px solid #F0EFE9;
}

.compare-cell:last-child {
  border-right: none;
}

.header-cell {
  font-weight: 600;
  color: #111;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.field-cell {
  font-weight: 500;
  color: #555;
  background: #FAFAFA;
}

.value-cell {
  font-weight: 400;
}

.value-cell.clickable {
  cursor: pointer;
}

.cell-action {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #2563EB;
  font-weight: 500;
}

.cell-icon {
  font-size: 11px;
  opacity: 0.6;
  transition: opacity 0.15s ease;
}

.cell-action:hover .cell-icon {
  opacity: 1;
}

/* 响应式 */
@media (max-width: 640px) {
  .compare-header,
  .compare-row {
    grid-template-columns: 100px 1fr 1fr;
  }

  .compare-cell {
    padding: 10px 12px;
    font-size: 12px;
  }
}
</style>
