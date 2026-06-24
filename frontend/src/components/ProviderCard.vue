<script setup lang="ts">
import { Cpu, Check, Edit, Delete } from '@element-plus/icons-vue'
import type { Provider } from '@/api/providers'

/**
 * 供应商配置卡片
 *
 * 视觉规范：
 * - 启用态：蓝色细边框 + 蓝色顶条 + 蓝色图标背景（精致、不粗暴）
 * - 非启用态：浅边框
 * - 两种状态统一 hover 上浮 0.5 + 阴影加深
 */
defineProps<{
  provider: Provider
}>()

const emit = defineEmits<{
  (e: 'toggle', p: Provider): void
  (e: 'edit', p: Provider): void
  (e: 'delete', p: Provider): void
}>()
</script>

<template>
  <div
    :class="[
      'group relative rounded-2xl border transition-all duration-300 overflow-hidden hover:-translate-y-0.5',
      // 启用态：蓝色强调边框 + 微蓝底色；暗色模式下通过 CSS 变量自动适配
      provider.is_enabled
        ? 'border-[#3B82F6] bg-[#F8FAFC] shadow-[0_4px_20px_rgb(59,130,246,0.08)] hover:shadow-[0_14px_34px_rgb(59,130,246,0.16)] dark:bg-[rgba(59,130,246,0.06)] dark:border-[#60A5FA]'
        : 'bg-white border-[#E8E6E1] hover:border-[#D1CFCA] shadow-[0_1px_3px_rgb(0,0,0,0.04)] hover:shadow-[0_14px_34px_rgb(0,0,0,0.12)] dark:bg-[var(--el-bg-color-overlay)] dark:border-[var(--el-border-color)] dark:hover:border-[var(--el-border-color-light)]',
    ]"
  >
    <!-- 启用标识条：顶部 3px 蓝色渐变细条 -->
    <div v-if="provider.is_enabled" class="absolute top-0 left-0 right-0 h-[3px] bg-gradient-to-r from-[#3B82F6] to-[#8B5CF6]"></div>

    <div class="p-5 sm:p-6 pt-6 sm:pt-7">
      <!-- 标题区 -->
      <div class="flex items-start justify-between gap-3 mb-5">
        <div class="flex items-center gap-3 min-w-0">
          <div
            :class="[
              'w-11 h-11 rounded-xl flex items-center justify-center transition-colors shrink-0',
              // 启用态：蓝底白图标（精致）；非启用态：灰底灰图标
              provider.is_enabled
                ? 'bg-[#3B82F6] text-white shadow-sm shadow-[rgb(59,130,246,0.25)]'
                : 'bg-[#F3F2EE] text-[#999] group-hover:text-[#555] dark:bg-[var(--el-fill-color-light)]',
            ]"
          >
            <el-icon :size="20"><Cpu /></el-icon>
          </div>
          <div class="min-w-0">
            <div class="flex items-center gap-2 flex-wrap">
              <h3 class="text-[15px] sm:text-[16px] font-semibold tracking-tight">{{ provider.provider_name }}</h3>
              <span
                v-if="provider.is_enabled"
                class="flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-[#EFF6FF] text-[#2563EB] font-medium shrink-0 dark:bg-[rgba(59,130,246,0.15)] dark:text-[#93C5FD]"
              >
                <el-icon :size="9"><Check /></el-icon> 使用中
              </span>
            </div>
            <p class="text-[11px] text-[#999] mt-0.5 font-mono truncate dark:text-[var(--el-text-color-secondary)]">{{ provider.llm_base_url }}</p>
          </div>
        </div>

        <!-- 启用开关：启用态蓝色 -->
        <button
          @click="emit('toggle', provider)"
          :class="[
            'relative w-11 h-6 rounded-full transition-colors duration-300 shrink-0',
            provider.is_enabled ? 'bg-[#3B82F6]' : 'bg-[#D1CFCA]',
          ]"
          :title="provider.is_enabled ? '点击禁用' : '点击启用'"
        >
          <span
            :class="[
              'absolute top-0.5 w-5 h-5 rounded-full bg-white shadow-sm transition-all duration-300',
              provider.is_enabled ? 'left-[22px]' : 'left-0.5',
            ]"
          ></span>
        </button>
      </div>

      <!-- 配置详情网格 -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3 pt-4 border-t border-[#F3F2EE] dark:border-[var(--el-border-color-lighter)]">
        <div>
          <p class="text-[10px] text-[#999] uppercase tracking-wider mb-1 dark:text-[var(--el-text-color-secondary)]">LLM 模型</p>
          <p class="text-[13px] font-mono text-[#333] break-all dark:text-[var(--el-text-color-primary)]">{{ provider.llm_model }}</p>
        </div>
        <div>
          <p class="text-[10px] text-[#999] uppercase tracking-wider mb-1 dark:text-[var(--el-text-color-secondary)]">EMBEDDING 模型</p>
          <p class="text-[13px] font-mono text-[#333] break-all dark:text-[var(--el-text-color-primary)]">{{ provider.embedding_model }}</p>
        </div>
        <div>
          <p class="text-[10px] text-[#999] uppercase tracking-wider mb-1 dark:text-[var(--el-text-color-secondary)]">API KEY</p>
          <p class="text-[13px] font-mono text-[#333] break-all dark:text-[var(--el-text-color-primary)]">{{ provider.llm_api_key }}</p>
        </div>
        <div>
          <p class="text-[10px] text-[#999] uppercase tracking-wider mb-1 dark:text-[var(--el-text-color-secondary)]">向量维度</p>
          <p class="text-[13px] font-mono text-[#333] dark:text-[var(--el-text-color-primary)]">{{ provider.embedding_dim }} dim</p>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="flex items-center justify-end gap-2 mt-5 pt-4 border-t border-[#F3F2EE] dark:border-[var(--el-border-color-lighter)]">
        <button
          @click="emit('edit', provider)"
          class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[12px] text-[#666] hover:text-[#111] hover:bg-[#F3F2EE] transition-colors dark:text-[var(--el-text-color-secondary)] dark:hover:text-[var(--el-text-color-primary)] dark:hover:bg-[var(--el-fill-color)]"
        >
          <el-icon :size="13"><Edit /></el-icon><span>编辑</span>
        </button>
        <button
          @click="emit('delete', provider)"
          class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[12px] text-[#666] hover:text-[#D32F2F] hover:bg-[#FFEBEE] transition-colors dark:text-[var(--el-text-color-secondary)] dark:hover:text-[##F87171] dark:hover:bg-[rgba(248,113,113,0.1)]"
        >
          <el-icon :size="13"><Delete /></el-icon><span>删除</span>
        </button>
      </div>
    </div>
  </div>
</template>
