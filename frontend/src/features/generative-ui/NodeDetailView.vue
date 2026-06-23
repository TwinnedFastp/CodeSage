<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, RefreshRight, FullScreen, Close } from '@element-plus/icons-vue'
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

// 全屏模式
const isFullscreen = ref(false)

// 展开的子网页（内联展示）
const activeWebpage = ref<{
  title: string
  html: string
} | null>(null)

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

function toggleFullscreen() {
  isFullscreen.value = !isFullscreen.value
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

// 处理组件内的交互式打开事件（表格行点击、卡片点击等）
function handleInlineOpen(payload: { title: string; html: string }) {
  activeWebpage.value = payload
}

// 处理表格/对比表点击 → 触发 AI 展开交互
async function handleAiAsk(payload: { question: string; context: string }) {
  if (!nodeId.value) return

  // 显示提示
  ElMessage.info(`正在分析：${payload.context.slice(0, 30)}...`)

  try {
    // 调用 expand 接口，让 AI 基于点击内容生成新的子节点/版本
    await genApi.expandNode(nodeId.value, payload.question)
    ElMessage.success('AI 已生成详细分析，正在加载...')
    await loadNode()
    // 自动滚动到内容区
    activeWebpage.value = null
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || 'AI 分析失败')
  }
}

// 关闭内联网页
function closeWebpage() {
  activeWebpage.value = null
}

// 当协议加载完成时，如果有 open_webpage action，自动展示专业网页
watch(currentProtocol, (protocol) => {
  if (!protocol) return
  const webAction = protocol.actions?.find((a) => a.type === 'open_webpage' && a.params?.html_content)
  if (webAction?.params?.html_content) {
    activeWebpage.value = {
      title: webAction.params.title || '详情页',
      html: webAction.params.html_content,
    }
  }
}, { immediate: true })

// 再思考 - 生成新的专业网页
async function onRegenerate() {
  if (!nodeId.value || regenerating.value) return
  regenerating.value = true
  try {
    await genApi.regenerateNode(nodeId.value)
    ElMessage.success('正在生成新版本...')
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
  <!-- 全屏容器 -->
  <div class="node-detail-page" :class="{ 'is-fullscreen': isFullscreen }">
    <!-- 顶部导航栏 -->
    <header class="page-header">
      <div class="header-inner">
        <el-button link @click="goBack" class="back-btn">
          <el-icon class="mr-1"><ArrowLeft /></el-icon>
          返回对话
        </el-button>

        <div class="header-actions">
          <el-button link @click="toggleFullscreen" class="fullscreen-btn">
            <el-icon><FullScreen /></el-icon>
          </el-button>
        </div>
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
                  @inline-open="handleInlineOpen"
                  @ai-ask="handleAiAsk"
                />
              </div>
            </div>

            <!-- 内联子网页展示区 -->
            <transition name="webpage-slide">
              <div v-if="activeWebpage" class="inline-webpage-container">
                <div class="webpage-toolbar">
                  <span class="webpage-title">
                    <el-icon class="mr-1"><FullScreen /></el-icon>
                    {{ activeWebpage.title }}
                  </span>
                  <el-button link size="small" @click="closeWebpage">
                    <el-icon><Close /></el-icon>
                    关闭
                  </el-button>
                </div>
                <iframe
                  :srcdoc="activeWebpage.html"
                  class="webpage-iframe"
                  sandbox="allow-scripts allow-same-origin"
                ></iframe>
              </div>
            </transition>
          </article>

          <!-- 右侧：版本历史（桌面端显示） -->
          <aside class="sidebar desktop-only">
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
            {{ regenerating ? '生成中...' : '再思考' }}
          </el-button>
          <el-button size="large" round @click="goBack" class="btn-ghost">返回</el-button>
          <span class="footer-meta">{{ formatFullTime(nodeDetail.node.created_at) }} 创建</span>
        </footer>

        <!-- 移动端版本历史折叠面板 -->
        <details class="mobile-version-panel">
          <summary class="mobile-version-summary">
            版本历史 ({{ sortedVersions.length + 1 }} 个版本)
          </summary>
          <div class="mobile-version-content">
            <div
              class="version-item mobile"
              :class="{ active: selectedVersionNo === -1 }"
              @click="selectCurrent"
            >
              <span class="version-no">v{{ currentNodeVersionNo }}</span>
              <span class="version-current-badge">当前</span>
              <span class="version-time">{{ formatFullTime(nodeDetail.node.current_version?.created_at) }}</span>
            </div>
            <div
              v-for="ver in sortedVersions"
              :key="ver.id"
              class="version-item mobile"
              :class="{ active: selectedVersionNo === ver.version_no }"
              @click="selectVersion(ver)"
            >
              <span class="version-no">v{{ ver.version_no }}</span>
              <span class="version-time">{{ formatRelativeTime(ver.created_at) }}</span>
            </div>
          </div>
        </details>
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
  transition: all 0.3s ease;
}

/* 全屏模式 */
.node-detail-page.is-fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
  background: #FFFFFF;
  overflow-y: auto;
}
.node-detail-page.is-fullscreen .page-header {
  background: #111;
  border-bottom-color: #333;
}
.node-detail-page.is-fullscreen .back-btn,
.node-detail-page.is-fullscreen .fullscreen-btn {
  color: white;
}
.node-detail-page.is-fullscreen .back-btn:hover,
.node-detail-page.is-fullscreen .fullscreen-btn:hover {
  color: #DDD;
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
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
}
.header-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}
.back-btn {
  color: #555;
  font-weight: 500;
  font-size: 14px;
}
.back-btn:hover {
  color: #111;
}
.fullscreen-btn {
  color: #999;
  font-size: 16px;
}
.fullscreen-btn:hover {
  color: #111;
}

/* ===== 页面主体（全宽）===== */
.page-body {
  width: 100%;
  padding: 28px clamp(20px, 4vw, 48px);
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
  font-size: clamp(22px, 3vw, 32px);
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
  flex-wrap: wrap;
}
.meta-row .sep {
  color: #E0DED8;
}

/* ===== 主布局（Flexbox 全宽响应式）===== */
.main-layout {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}

.content-area {
  flex: 1;
  min-width: 0; /* 防止内容溢出 */
  min-width: 0; /* Flex 子项最小宽度 */
}

.sidebar {
  width: 280px;
  flex-shrink: 0;
}

/* ===== 内容卡片（全宽自适应）===== */
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

/* ===== 内联子网页展示 ===== */
.inline-webpage-container {
  margin-top: 20px;
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid #EAE8E2;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
  background: white;
}
.webpage-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #F8FAFC;
  border-bottom: 1px solid #E8E6E1;
}
.webpage-title {
  font-size: 13px;
  font-weight: 600;
  color: #444;
  display: flex;
  align-items: center;
}
.webpage-iframe {
  width: 100%;
  height: 600px;
  border: none;
  display: block;
}

/* 内联网页动画 */
.webpage-slide-enter-active,
.webpage-slide-leave-active {
  transition: all 0.35s ease;
}
.webpage-slide-enter-from {
  opacity: 0;
  transform: translateY(20px);
}
.webpage-slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
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

/* 桌面端侧边栏可见 */
.desktop-only {
  display: block;
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

/* 移动端版本项 */
.version-item.mobile {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

/* ===== 底部操作栏 ===== */
.page-footer {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 32px;
  padding-top: 20px;
  border-top: 1px solid #F0EFE9;
  flex-wrap: wrap;
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

/* ===== 移动端版本面板 ===== */
.mobile-version-panel {
  display: none;
  margin-top: 20px;
  border-radius: 14px;
  background: white;
  border: 1px solid #EAE8E2;
  overflow: hidden;
}
.mobile-version-summary {
  padding: 16px 20px;
  font-weight: 600;
  font-size: 14px;
  color: #111;
  cursor: pointer;
  user-select: none;
  list-style: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.mobile-version-summary::-webkit-details-marker {
  display: none;
}
.mobile-version-summary::after {
  content: '+';
  font-size: 18px;
  color: #888;
  transition: transform 0.2s;
}
.details[open] .mobile-version-summary::after {
  transform: rotate(45deg);
}
.mobile-version-content {
  padding: 0 16px 16px;
  border-top: 1px solid #F2F0EA;
}

/* ===== 响应式设计 ===== */

/* 平板及以下：隐藏右侧边栏，显示底部折叠面板 */
@media (max-width: 1024px) {
  .main-layout {
    flex-direction: column;
  }

  .sidebar.desktop-only {
    display: none; /* 隐藏桌面端侧边栏 */
  }

  .mobile-version-panel {
    display: block; /* 显示移动端版本面板 */
  }

  .webpage-iframe {
    height: 450px; /* 减小 iframe 高度 */
  }
}

/* 手机端优化 */
@media (max-width: 640px) {
  .page-body {
    padding: 16px 12px 36px;
  }

  .header-inner {
    padding: 10px 16px;
  }

  .page-footer {
    flex-direction: column;
    align-items: stretch;
  }

  .footer-meta {
    margin-left: 0;
    text-align: center;
    margin-top: 8px;
  }

  .btn-primary-dark,
  .btn-ghost {
    width: 100%;
    justify-content: center;
  }

  .content-card-header {
    padding: 12px 16px 10px;
  }

  .sidebar-card {
    padding: 14px;
  }

  .webpage-iframe {
    height: 350px;
  }

  .meta-row {
    font-size: 12px;
  }
}

/* 超大屏幕优化 */
@media (min-width: 1600px) {
  .page-body {
    padding: 32px clamp(40px, 5vw, 80px);
  }

  .sidebar {
    width: 320px;
  }

  .webpage-iframe {
    height: 700px;
  }
}
</style>
