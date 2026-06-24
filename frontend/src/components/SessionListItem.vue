<script setup lang="ts">
import { Edit, FolderAdd, FolderRemove, Delete } from '@element-plus/icons-vue'
import type { ChatSession } from '@/types'

/**
 * 单个会话列表项
 * 职责：行内展示（圆点 + 标题）+ 选中高亮 + 标题内联重命名 + 归档/取消归档/删除快捷操作
 * 修复要点：操作按钮平时 opacity-0 不可见，但若不加 pointer-events-none，
 * 它仍会拦截行内点击（@click.stop 吞掉选中事件），导致"点空白处无反应"。
 * 因此不可见时关闭其指针事件，仅 hover 时启用。
 */
const props = defineProps<{
  session: ChatSession
  active: boolean         // 是否为当前选中会话
  editing: boolean        // 是否处于标题内联编辑态
  modelValue: string       // 编辑中的标题文本（v-model）
  collapsed?: boolean     // 桌面端侧栏折叠态：仅显示圆点
  archived?: boolean      // 是否处于归档视图
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'select', id: string): void
  (e: 'start-edit', id: string, title: string): void
  (e: 'confirm-edit', id: string): void
  (e: 'cancel-edit'): void
  (e: 'title-keydown', ev: KeyboardEvent, id: string): void
  (e: 'archive', id: string): void
  (e: 'unarchive', id: string): void
  (e: 'delete', id: string): void
}>()

// 输入框双向绑定透传
function onInput(e: Event) {
  emit('update:modelValue', (e.target as HTMLInputElement).value)
}

function onArchiveClick() {
  if (props.archived || props.session.is_archived) {
    emit('unarchive', props.session.id)
  } else {
    emit('archive', props.session.id)
  }
}
</script>

<template>
  <div
    :class="[
      'group flex items-center gap-3 px-3 py-3 rounded-lg transition-colors cursor-pointer select-none',
      active ? 'bg-(--color-border)' : 'hover:bg-(--color-border)',
      editing ? 'ring-1 ring-(--color-ink)/20' : '',
    ]"
    @click="emit('select', session.id)"
  >
    <!-- 选中状态指示圆点 -->
    <div :class="['w-1.5 h-1.5 rounded-full shrink-0', active ? 'bg-(--color-ink)' : 'bg-(--color-border-strong)']"></div>

    <!-- 编辑态：内联输入框 -->
    <template v-if="editing">
      <input
        :value="modelValue"
        @input="onInput"
        class="session-title-input flex-1 min-w-0 bg-(--color-surface-soft) border border-(--color-border-strong) rounded-lg px-2.5 py-1.5 text-[13px] font-medium text-(--color-ink) outline-none focus:border-(--color-ink) transition-colors"
        maxlength="60"
        @keydown="emit('title-keydown', $event, session.id)"
        @blur="emit('confirm-edit', session.id)"
      />
    </template>

    <!-- 展示态 -->
    <template v-else>
      <span
        v-if="!collapsed"
        class="flex-1 min-w-0 truncate text-[13px] font-medium"
        :class="active ? 'text-(--color-ink)' : 'text-(--color-muted) group-hover:text-(--color-ink)'"
        @dblclick.stop="emit('start-edit', session.id, session.title || '')"
      >{{ session.title || '未命名会话' }}</span>
      <!--
        操作按钮：不可见（opacity-0）时关闭指针事件，
        避免它占据行右侧空白并拦截点击；hover 行时再启用，保证可点。
      -->
      <div
        v-if="!collapsed"
        class="flex items-center gap-0.5 shrink-0 opacity-0 group-hover:opacity-100 pointer-events-none group-hover:pointer-events-auto transition-opacity"
      >
        <button
          class="p-1.5 rounded-md hover:bg-(--color-surface-soft) transition-all text-(--color-faint) hover:text-(--color-ink)"
          :title="archived || session.is_archived ? '取消归档' : '归档会话'"
          @click.stop="onArchiveClick"
        >
          <el-icon :size="12"><component :is="archived || session.is_archived ? FolderRemove : FolderAdd" /></el-icon>
        </button>
        <button
          class="p-1.5 rounded-md hover:bg-(--color-surface-soft) transition-all text-(--color-faint) hover:text-(--color-ink)"
          title="重命名"
          @click.stop="emit('start-edit', session.id, session.title || '')"
        >
          <el-icon :size="12"><Edit /></el-icon>
        </button>
        <button
          class="p-1.5 rounded-md hover:bg-(--color-surface-soft) transition-all text-(--color-faint) hover:text-[#D9534F]"
          title="删除会话"
          @click.stop="emit('delete', session.id)"
        >
          <el-icon :size="12"><Delete /></el-icon>
        </button>
      </div>
      <!-- 折叠态：透明占位撑满整行点击热区 -->
      <div v-if="collapsed" class="flex-1" @click="emit('select', session.id)"></div>
    </template>
  </div>
</template>
