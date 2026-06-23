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
  <div class="node-detail-page">
    <!-- 顶部导航栏 -->
    <header class="page-header">
      <div class="header-inner">
        <el-button link @click="goBack" class="back-btn">
          <el-icon class="mr-1"><ArrowLeft /></el-icon>
          返回对话
        </el-button>
      </div>
    </header>

    <div class="page-body">
      <!-- 加载骨架屏 -->
      <template v-if="loading">
        <div class="skeleton-wrap">
          <el-skeleton :rows="1" animated class="mb-6" :style="{ width: '60%' }" />
          <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div class="lg:col-span-2">
              <el-skeleton :rows="10" animated />
            </div>
            <div>
              <el-skeleton :rows="8" animated />
            </div>
          </div>
        </div>
      </template>

      <!-- 错误状态 -->
      <div v-else-if="error" class="error-state">
        <p>{{ error }}</p>
        <el-button round type="primary" @click="loadNode">重新加载</el-button>
      </div>

      <!-- 主内容 -->
      <template v-else-if="nodeDetail">
        <!-- 标题区 -->
        <section class="title-section">
          <h1 class="page-title">{{ currentProtocol?.title || nodeDetail.node.node_type || '节点详情' }}</h1>
          <div class="meta-row">
            <span>节点 ID: {{ nodeDetail.node.id }}</span>
            <span class="sep">|</span>
            <span>类型: {{ nodeDetail.node.node_type }}</span>
            <span class="sep">|</span>
            <span>版本数: {{ nodeDetail.versions.length }}</span>
          </div>
        </section>

        <!-- 主布局：左内容 + 右侧边栏 -->
        <main class="main-layout">
          <!-- 左侧：组件渲染区 -->
          <article class="content-area">
            <div class="content-card">
              <div class="content-card-header">
                <div class="content-card-title">
                  内容渲染
                  <span v-if="selectedVersionNo > -1" class="ver-tag">v{{ selectedVersionNo }}</span>
                  <span v-else class="ver-tag">当前版本</span>
                </div>
                <span
                  v-if="currentSource"
                  :class="['source-badge', sourceBadgeClass(currentSource)]"
                >{{ sourceLabel[currentSource] || currentSource }}</span>
              </div>
              <div class="content-card-body">
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
          </article>

          <!-- 右侧：版本历史 -->
          <aside class="sidebar">
            <div class="sidebar-card">
              <h2 class="sidebar-title">版本历史</h2>

              <el-empty v-if="sortedVersions.length === 0" description="暂无版本" :image-size="60" />

              <div v-else class="version-list">
                <!-- 当前版本入口 -->
                <div
                  class="version-item"
                  :class="{ active: selectedVersionNo === -1 }"
                  @click="selectCurrent"
                >
                  <div class="version-item-top">
                    <div class="version-item-left">
                      <span class="version-no">v{{ currentNodeVersionNo }}</span>
                      <span class="version-current-badge">当前</span>
                    </div>
                    <span
                      :class="['source-badge', sourceBadgeClass(nodeDetail.node.current_version?.source || '')]"
                    >{{ sourceLabel[nodeDetail.node.current_version?.source || ''] || nodeDetail.node.current_version?.source || 'LLM' }}</span>
                  </div>
                  <p class="version-time">{{ formatFullTime(nodeDetail.node.current_version?.created_at) }}</p>
                </div>

                <!-- 历史版本列表 -->
                <div
                  v-for="ver in sortedVersions"
                  :key="ver.id"
                  class="version-item"
                  :class="{ active: selectedVersionNo === ver.version_no }"
                  @click="selectVersion(ver)"
                >
                  <div class="version-item-top">
                    <div class="version-item-left">
                      <span class="version-no">v{{ ver.version_no }}</span>
                      <span
                        v-if="ver.version_no === currentNodeVersionNo"
                        class="version-current-badge"
                      >当前</span>
                    </div>
                    <span
                      :class="['source-badge', sourceBadgeClass(ver.source)]"
                    >{{ sourceLabel[ver.source] || ver.source }}</span>
                  </div>
                  <p class="version-time">{{ formatRelativeTime(ver.created_at) }}</p>
                </div>
              </div>
            </div>
          </aside>
        </main>

        <!-- 底部操作栏 -->
        <footer class="page-footer">
          <el-button
            size="large"
            round
            :loading="regenerating"
            @click="onRegenerate"
            class="btn-primary-dark"
          >
            <el-icon v-if="!regenerating" class="mr-1.5"><RefreshRight /></el-icon>
            再思考
          </el-button>
          <el-button size="large" round @click="goBack" class="btn-ghost">返回</el-button>
          <span class="footer-meta">{{ formatFullTime(nodeDetail.node.created_at) }} 创建</span>
        </footer>
      </template>
    </div>
  </div>
</template>

<style scoped>
/* ===== 页面容器 ===== */
.node-detail-page {
  min-height: 100vh;
  background: #FAFAFA;
  color: #111;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  -webkit-font-smoothing: antialiased;
}

/* ===== 顶部导航 ===== */
.page-header {
  background: white;
  border-bottom: 1px solid #E8E6E1;
  position: sticky;
  top: 0;
  z-index: 100;
}
.header-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 12px 24px;
}
.back-btn {
  color: #555;
  font-weight: 500;
  font-size: 14px;
}
.back-btn:hover {
  color: #111;
}

/* ===== 页面主体 ===== */
.page-body {
  max-width: 1200px;
  margin: 0 auto;
  padding: 28px 24px 48px;
}

/* 骨架屏 */
.skeleton-wrap {
  padding-top: 8px;
}

/* 错误状态 */
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 0;
  gap: 16px;
}
.error-state p {
  color: #999;
  font-size: 15px;
}

/* ===== 标题区 ===== */
.title-section {
  margin-bottom: 24px;
}
.page-title {
  font-family: Georgia, 'Times New Roman', serif;
  font-size: 26px;
  font-weight: 700;
  color: #111;
  line-height: 1.3;
  letter-spacing: -0.3px;
  margin-bottom: 8px;
}
.meta-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #888;
}
.meta-row .sep {
  color: #E0DED8;
}

/* ===== 主布局（Flexbox，不再依赖 Tailwind grid 崩溃）===== */
.main-layout {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.content-area {
  flex: 1;
  min-width: 0; /* 防止内容溢出 */
}

.sidebar {
  width: 260px;
  flex-shrink: 0;
}

/* ===== 内容卡片 ===== */
.content-card {
  background: white;
  border-radius: 14px;
  border: 1px solid #EAE8E2;
  box-shadow: 0 1px 3px rgba(0,0,0,0.03), 0 4px 16px rgba(0,0,0,0.02);
  overflow: hidden;
}
.content-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px 14px;
  border-bottom: 1px solid #F2F0EA;
}
.content-card-title {
  font-family: Georgia, serif;
  font-size: 15px;
  font-weight: 600;
  color: #111;
  display: flex;
  align-items: center;
  gap: 8px;
}
.ver-tag {
  font-family: -apple-system, sans-serif;
  font-size: 11px;
  color: #999;
  font-weight: 400;
}
.source-badge {
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 10px;
  font-weight: 500;
  white-space: nowrap;
}
.content-card-body {
  padding: 4px 0 0;
}

/* ===== 侧边栏 ===== */
.sidebar-card {
  background: white;
  border-radius: 14px;
  border: 1px solid #EAE8E2;
  box-shadow: 0 1px 3px rgba(0,0,0,0.03);
  padding: 18px;
  position: sticky;
  top: 68px; /* header height + spacing */
}
.sidebar-title {
  font-family: Georgia, serif;
  font-size: 15px;
  font-weight: 600;
  color: #111;
  margin-bottom: 14px;
}

/* 版本列表 */
.version-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.version-item {
  padding: 12px 14px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.18s ease;
  border-left: 3px solid transparent;
  background: #FAFAFA;
  border-color: transparent;
}
.version-item:hover {
  background: white;
  border-color: #D1CFCA;
  box-shadow: 0 1px 6px rgba(0,0,0,0.05);
}
.version-item.active {
  background: white;
  border-color: #111;
  box-shadow: 0 2px 10px rgba(0,0,0,0.07);
}
.version-item-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}
.version-item-left {
  display: flex;
  align-items: center;
  gap: 7px;
}
.version-no {
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 13px;
  font-weight: 700;
  color: #555;
}
.version-item.active .version-no {
  color: #111;
}
.version-current-badge {
  font-size: 10px;
  padding: 1px 7px;
  border-radius: 6px;
  background: #111;
  color: white;
  font-weight: 600;
  letter-spacing: 0.3px;
}
.version-time {
  font-size: 11px;
  color: #AAA;
  margin-left: 2px;
}

/* ===== 底部操作栏 ===== */
.page-footer {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 32px;
  padding-top: 20px;
  border-top: 1px solid #F0EFE9;
}
.btn-primary-dark {
  background: #111 !important;
  color: white !important;
  border-color: #111 !important;
  font-weight: 500;
}
.btn-primary-dark:hover {
  background: #333 !important;
  border-color: #333 !important;
}
.btn-ghost {
  color: #666;
  border-color: #E0DED8;
}
.btn-ghost:hover {
  color: #111;
  border-color: #AAA;
}
.footer-meta {
  font-size: 12px;
  color: #BBB;
  margin-left: auto;
}

/* ===== 响应式：小屏幕时侧边栏折叠到底部 ===== */
@media (max-width: 1024px) {
  .main-layout {
    flex-direction: column;
  }
  .sidebar {
    width: 100%;
  }
  .sidebar-card {
    position: static;
  }
  .page-title {
    font-size: 22px;
  }
}

@media (max-width: 640px) {
  .page-body {
    padding: 16px 16px 36px;
  }
  .page-title {
    font-size: 19px;
  }
  .content-card-header,
  .sidebar-card {
    padding: 14px 16px;
  }
}
</style>
