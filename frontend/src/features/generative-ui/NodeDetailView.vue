<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, RefreshRight } from '@element-plus/icons-vue'
import * as genApi from './api'
import ComponentRenderer from './ComponentRenderer.vue'
import type { NodeDetail, NodeVersionSummary, ComponentProtocol } from './types'

const route = useRoute()
const router = useRouter()

const nodeId = computed(() => String(route.params.id || route.query.nodeId || ''))
const loading = ref(false)
const regenerating = ref(false)
const nodeDetail = ref<NodeDetail | null>(null)
const selectedVersionNo = ref(-1)
const error = ref<string | null>(null)

const currentProtocol = computed<ComponentProtocol | null>(() => {
  if (!nodeDetail.value) return null
  if (selectedVersionNo.value === -1) {
    return nodeDetail.value.node.current_version?.content_json ?? null
  }
  const ver = nodeDetail.value.versions.find((v) => v.version_no === selectedVersionNo.value)
  return ver?.content_json ?? null
})

const currentSource = computed<string>(() => {
  if (!nodeDetail.value) return ''
  if (selectedVersionNo.value === -1) {
    return nodeDetail.value.node.current_version?.source ?? ''
  }
  const ver = nodeDetail.value.versions.find((v) => v.version_no === selectedVersionNo.value)
  return ver?.source ?? ''
})

const sortedVersions = computed<NodeVersionSummary[]>(() => {
  if (!nodeDetail.value) return []
  return [...nodeDetail.value.versions].sort((a, b) => b.version_no - a.version_no)
})

const currentNodeVersionNo = computed<number>(() => {
  return nodeDetail.value?.node.current_version?.version_no ?? -1
})

function formatRelativeTime(dateStr?: string): string {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = Date.now()
  const diff = now - date.getTime()
  const sec = Math.floor(diff / 1000)
  if (sec < 60) return '刚刚'
  const min = Math.floor(sec / 60)
  if (min < 60) return `${min} 分钟前`
  const hour = Math.floor(min / 60)
  if (hour < 24) return `${hour} 小时前`
  const day = Math.floor(hour / 24)
  if (day < 30) return `${day} 天前`
  const month = Math.floor(day / 30)
  return `${month} 个月前`
}

function formatFullTime(dateStr?: string): string {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  const h = String(date.getHours()).padStart(2, '0')
  const mi = String(date.getMinutes()).padStart(2, '0')
  return `${y}-${m}-${d} ${h}:${mi}`
}

const sourceLabel: Record<string, string> = {
  llm: 'LLM',
  tool: '工具',
  regenerate: '再思考',
  expand: '展开',
}

function sourceBadgeClass(source: string): string {
  const map: Record<string, string> = {
    llm: 'bg-[#F3F2EE] text-[#111111]',
    tool: 'bg-[#EAE8E0] text-[#555555]',
    regenerate: 'bg-[#111111] text-[#FAFAFA]',
    expand: 'bg-[#111111] text-[#FAFAFA]',
  }
  return map[source] || 'bg-[#F3F2EE] text-[#555555]'
}

function goBack() {
  router.back()
}

async function loadNode() {
  if (!nodeId.value) {
    error.value = '缺少节点 ID'
    return
  }
  loading.value = true
  error.value = null
  try {
    nodeDetail.value = await genApi.getNode(nodeId.value)
    selectedVersionNo.value = -1
  } catch (err: any) {
    error.value = err.response?.data?.detail || '加载节点失败'
    ElMessage.error(error.value || '加载节点失败')
  } finally {
    loading.value = false
  }
}

function selectVersion(ver: NodeVersionSummary) {
  if (ver.version_no === selectedVersionNo.value) return
  selectedVersionNo.value = ver.version_no
}

function selectCurrent() {
  selectedVersionNo.value = -1
}

async function onRegenerate() {
  if (!nodeId.value || regenerating.value) return
  regenerating.value = true
  try {
    await genApi.regenerateNode(nodeId.value)
    ElMessage.success('再思考完成')
    await loadNode()
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '再思考失败')
  } finally {
    regenerating.value = false
  }
}

onMounted(() => {
  loadNode()
})
</script>

<template>
  <div class="min-h-screen bg-[#FAFAFA] text-[#111111] antialiased font-sans">
    <div class="max-w-6xl mx-auto px-4 md:px-8 py-8">
      <!-- 顶部导航栏 -->
      <div class="flex items-center gap-4 mb-8">
        <el-button link @click="goBack" class="text-[#555555] hover:text-[#111111] font-medium">
          <el-icon class="mr-1.5"><ArrowLeft /></el-icon>
          返回对话
        </el-button>
      </div>

      <!-- 加载骨架屏 -->
      <template v-if="loading">
        <el-skeleton :rows="2" animated class="mb-6" />
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div class="lg:col-span-2">
            <el-skeleton :rows="8" animated />
          </div>
          <div>
            <el-skeleton :rows="6" animated />
          </div>
        </div>
      </template>

      <!-- 错误状态 -->
      <div v-else-if="error" class="flex flex-col items-center justify-center py-24">
        <p class="text-[#999999] text-[15px] mb-4">{{ error }}</p>
        <el-button round @click="loadNode">重新加载</el-button>
      </div>

      <!-- 主内容 -->
      <template v-else-if="nodeDetail">
        <!-- 标题区 -->
        <div class="mb-6">
          <h1 class="font-serif text-3xl text-[#111111] tracking-tight leading-snug">
            {{ currentProtocol?.title || nodeDetail.node.node_type || '节点详情' }}
          </h1>
          <div class="flex items-center gap-3 mt-2 text-[13px] text-[#777777]">
            <span>节点 ID: {{ nodeDetail.node.id }}</span>
            <span class="text-[#E8E6E1]">|</span>
            <span>类型: {{ nodeDetail.node.node_type }}</span>
            <span class="text-[#E8E6E1]">|</span>
            <span>版本数: {{ nodeDetail.versions.length }}</span>
          </div>
        </div>

        <!-- 卡片网格：左 65% 组件渲染 + 右 35% 版本历史 -->
        <div class="grid grid-cols-1 lg:grid-cols-5 gap-6">
          <!-- 左侧：当前组件渲染 -->
          <div class="lg:col-span-[3/5]">
            <div class="detail-render-area">
              <div class="render-header">
                <h2 class="font-serif text-lg text-[#111111]">
                  内容渲染
                  <span v-if="selectedVersionNo > -1" class="text-[#777777] text-[13px] ml-2 font-sans">v{{ selectedVersionNo }}</span>
                  <span v-else class="text-[#777777] text-[13px] ml-2 font-sans">当前版本</span>
                </h2>
                <span
                  v-if="currentSource"
                  :class="['text-[11px] px-2.5 py-1 rounded-full font-medium', sourceBadgeClass(currentSource)]"
                >{{ sourceLabel[currentSource] || currentSource }}</span>
              </div>

              <ComponentRenderer
                v-if="currentProtocol"
                :protocol="currentProtocol"
                :versions="nodeDetail.versions"
                :current-version-no="selectedVersionNo > -1 ? selectedVersionNo : currentNodeVersionNo"
                :loading="regenerating"
                @regenerate="onRegenerate"
              />
            </div>
          </div>

          <!-- 右侧：版本历史 -->
          <div class="lg:col-span-[2/5]">
            <div class="detail-sidebar">
              <h2 class="font-serif text-lg text-[#111111] mb-5">版本历史</h2>

              <el-empty v-if="sortedVersions.length === 0" description="暂无版本" :image-size="80" />

              <div v-else class="space-y-3">
                <!-- 当前版本入口 -->
                <div
                  class="rounded-xl p-4 cursor-pointer transition-all duration-200 border-l-[3px] hover:shadow-[0_2px_8px_rgb(0,0,0,0.04)]"
                  :class="selectedVersionNo === -1
                    ? 'bg-white border-l-[#111111] shadow-[0_2px_8px_rgb(0,0,0,0.06)]'
                    : 'bg-white border-l-transparent hover:border-l-[#D1CFCA]'"
                  @click="selectCurrent"
                >
                  <div class="flex items-center justify-between mb-1">
                    <div class="flex items-center gap-2">
                      <span
                        :class="['text-[13px] font-bold font-mono', selectedVersionNo === -1 ? 'text-[#111111]' : 'text-[#555555]']"
                      >v{{ currentNodeVersionNo }}</span>
                      <span class="text-[10px] px-1.5 py-0.5 rounded-full bg-[#111111] text-white font-medium">当前</span>
                    </div>
                    <span
                      :class="['text-[11px] px-2 py-0.5 rounded-full font-medium', sourceBadgeClass(nodeDetail.node.current_version?.source || '')]"
                    >{{ sourceLabel[nodeDetail.node.current_version?.source || ''] || nodeDetail.node.current_version?.source || 'LLM' }}</span>
                  </div>
                  <p class="text-[11px] text-[#999999] mt-1">
                    {{ formatFullTime(nodeDetail.node.current_version?.created_at) }}
                  </p>
                </div>

                <!-- 历史版本列表 -->
                <div
                  v-for="ver in sortedVersions"
                  :key="ver.id"
                  class="rounded-xl p-4 cursor-pointer transition-all duration-200 border-l-[3px] hover:shadow-[0_2px_8px_rgb(0,0,0,0.04)]"
                  :class="selectedVersionNo === ver.version_no
                    ? 'bg-white border-l-[#111111] shadow-[0_2px_8px_rgb(0,0,0,0.06)]'
                    : 'bg-white border-l-transparent hover:border-l-[#D1CFCA]'"
                  @click="selectVersion(ver)"
                >
                  <div class="flex items-center justify-between mb-1">
                    <div class="flex items-center gap-2">
                      <span
                        :class="['text-[13px] font-bold font-mono', selectedVersionNo === ver.version_no ? 'text-[#111111]' : 'text-[#555555]']"
                      >v{{ ver.version_no }}</span>
                      <span
                        v-if="ver.version_no === currentNodeVersionNo"
                        class="text-[10px] px-1.5 py-0.5 rounded-full bg-[#111111] text-white font-medium"
                      >当前</span>
                    </div>
                    <span
                      :class="['text-[11px] px-2 py-0.5 rounded-full font-medium', sourceBadgeClass(ver.source)]"
                    >{{ sourceLabel[ver.source] || ver.source }}</span>
                  </div>
                  <p class="text-[11px] text-[#999999] mt-1">
                    {{ formatRelativeTime(ver.created_at) }}
                  </p>
                  <div class="mt-2">
                    <el-button
                      size="small"
                      text
                      type="primary"
                      :disabled="selectedVersionNo === ver.version_no"
                      @click.stop="selectVersion(ver)"
                      class="!text-[11px] !p-0 !h-auto"
                    >
                      {{ selectedVersionNo === ver.version_no ? '查看中' : '查看' }}
                    </el-button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 底部操作栏 -->
        <div class="mt-8 flex items-center gap-4">
          <el-button
            size="large"
            round
            :loading="regenerating"
            @click="onRegenerate"
            class="!bg-[#111111] !text-white !border-[#111111] hover:!bg-[#333333] hover:!border-[#333333] !font-medium"
          >
            <el-icon v-if="!regenerating" class="mr-1.5"><RefreshRight /></el-icon>
            再思考
          </el-button>
          <el-button
            size="large"
            round
            @click="goBack"
            class="!text-[#555555] hover:!text-[#111111]"
          >
            返回
          </el-button>
          <span class="text-[12px] text-[#999999] ml-auto">
            {{ formatFullTime(nodeDetail.node.created_at) }} 创建
          </span>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.detail-render-area {
  background: white;
  border-radius: 16px;
  border: 1px solid #E8E6E1;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 20px rgba(0,0,0,0.03);
  overflow: hidden;
}

.render-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 22px 14px;
  border-bottom: 1px solid #F0EFE9;
}

.detail-sidebar {
  background: white;
  border-radius: 16px;
  border: 1px solid #E8E6E1;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 20px rgba(0,0,0,0.03);
  padding: 22px;
  position: sticky;
  top: 24px;
}
</style>
