<script setup lang="ts">
import { Cpu, Check, Edit, Delete } from '@element-plus/icons-vue'
import type { Provider } from '@/api/providers'

/**
 * 供应商配置卡片
 *
 * 职责：展示单个供应商配置（名称 / URL / LLM 模型 / Embedding 模型 / API Key / 向量维度）
 *       + 启用开关 + 编辑 / 删除操作。
 *
 * 视觉规范（杂志风）：
 * - 启用态：黑色顶条 + 黑色图标背景 + 加重边框；
 * - 非启用态：浅边框，hover 时上浮 0.5 + 阴影加深，呈现可点击的卡片质感；
 * - 配置详情网格在 sm 及以上双列，小屏自动单列，避免长模型名挤换行。
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
      'group relative bg-white rounded-2xl border transition-all duration-300 overflow-hidden',
      // 启用态边框 + 阴影；非启用态浅边框，hover 时上浮 + 阴影加深
      provider.is_enabled
        ? 'border-[#111] shadow-[0_4px_20px_rgb(0,0,0,0.06)]'
        : 'border-[#E8E6E1] hover:border-[#D1CFCA] hover:shadow-[0_12px_32px_rgb(0,0,0,0.10)] hover:-translate-y-0.5',
    ]"
  >
    <!-- 启用标识条：卡片顶部 3px 黑色细条 -->
    <div v-if="provider.is_enabled" class="absolute top-0 left-0 right-0 h-[3px] bg-[#111]"></div>

    <div class="p-5 sm:p-6 pt-6 sm:pt-7">
      <!-- 标题区：图标 + 名称 + URL + 启用开关 -->
      <div class="flex items-start justify-between gap-3 mb-5">
        <div class="flex items-center gap-3 min-w-0">
          <div
            :class="[
              'w-11 h-11 rounded-xl flex items-center justify-center transition-colors shrink-0',
              provider.is_enabled ? 'bg-[#111] text-white' : 'bg-[#F3F2EE] text-[#999] group-hover:text-[#555]',
            ]"
          >
            <el-icon :size="20"><Cpu /></el-icon>
          </div>
          <div class="min-w-0">
            <div class="flex items-center gap-2 flex-wrap">
              <h3 class="text-[15px] sm:text-[16px] font-semibold tracking-tight">{{ provider.provider_name }}</h3>
              <span
                v-if="provider.is_enabled"
                class="flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-[#E8F5E9] text-[#2E7D32] font-medium shrink-0"
              >
                <el-icon :size="9"><Check /></el-icon> 使用中
              </span>
            </div>
            <!-- Base URL：truncate 防止长地址撑破布局 -->
            <p class="text-[11px] text-[#999] mt-0.5 font-mono truncate">{{ provider.llm_base_url }}</p>
          </div>
        </div>

        <!-- 启用 / 禁用开关 -->
        <button
          @click="emit('toggle', provider)"
          :class="[
            'relative w-11 h-6 rounded-full transition-colors duration-300 shrink-0',
            provider.is_enabled ? 'bg-[#111]' : 'bg-[#D1CFCA]',
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

      <!-- 配置详情：小屏单列、sm 起双列；长模型名 break-all 防溢出 -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3 pt-4 border-t border-[#F3F2EE]">
        <div>
          <p class="text-[10px] text-[#999] uppercase tracking-wider mb-1">LLM 模型</p>
          <p class="text-[13px] font-mono text-[#333] break-all">{{ provider.llm_model }}</p>
        </div>
        <div>
          <p class="text-[10px] text-[#999] uppercase tracking-wider mb-1">Embedding 模型</p>
          <p class="text-[13px] font-mono text-[#333] break-all">{{ provider.embedding_model }}</p>
        </div>
        <div>
          <p class="text-[10px] text-[#999] uppercase tracking-wider mb-1">API Key</p>
          <p class="text-[13px] font-mono text-[#333] break-all">{{ provider.llm_api_key }}</p>
        </div>
        <div>
          <p class="text-[10px] text-[#999] uppercase tracking-wider mb-1">向量维度</p>
          <p class="text-[13px] font-mono text-[#333]">{{ provider.embedding_dim }} dim</p>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="flex items-center justify-end gap-2 mt-5 pt-4 border-t border-[#F3F2EE]">
        <button
          @click="emit('edit', provider)"
          class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[12px] text-[#666] hover:text-[#111] hover:bg-[#F3F2EE] transition-colors"
        >
          <el-icon :size="13"><Edit /></el-icon><span>编辑</span>
        </button>
        <button
          @click="emit('delete', provider)"
          class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[12px] text-[#666] hover:text-[#D32F2F] hover:bg-[#FFEBEE] transition-colors"
        >
          <el-icon :size="13"><Delete /></el-icon><span>删除</span>
        </button>
      </div>
    </div>
  </div>
</template>
