<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { Refresh, FullScreen, Close } from '@element-plus/icons-vue'
import { componentRegistry } from './componentRegistry'
import UnknownBlock from './components/UnknownBlock.vue'
import type { ComponentAction, ComponentProtocol, NodeVersionSummary } from './types'

const props = defineProps<{
  protocol: ComponentProtocol
  versions?: NodeVersionSummary[]
  currentVersionNo?: number
  loading?: boolean
}>()

const emit = defineEmits<{
  (e: 'regenerate'): void
  (e: 'expand', payload: { id?: string; message: string }): void
  (e: 'function-call', payload: { function_name?: string; params?: Record<string, any>; target_id?: string }): void
  (e: 'switch-version', payload: { versionId: string }): void
  (e: 'open-webpage', payload: { htmlContent: string; title: string }): void
  (e: 'inline-open', payload: { title: string; html: string }): void
}>()

// 全屏网页查看器状态
const showWebpageViewer = ref(false)
const webpageContent = ref('')
const webpageTitle = ref('')

const expandActions = computed<ComponentAction[]>(() =>
  (props.protocol.actions || []).filter((a) => a.type === 'expand'),
)
const fnActions = computed<ComponentAction[]>(() =>
  (props.protocol.actions || []).filter((a) => a.type === 'function_call'),
)
// webpage 类型动作（打开预生成的子页面）
const webPageActions = computed<ComponentAction[]>(() =>
  (props.protocol.actions || []).filter((a) => a.type === 'open_webpage'),
)
const versionsList = computed<NodeVersionSummary[]>(() => props.versions || [])

function onRegenerate() {
  emit('regenerate')
}

function onExpand(action: ComponentAction) {
  emit('expand', { id: action?.target_id, message: '请详细展开说明该主题的所有方面' })
}

function onFunctionCall(action: ComponentAction) {
  emit('function-call', {
    function_name: action?.function_name,
    params: action?.params || {},
    target_id: action?.target_id,
  })
}

// 来自 webpage 组件卡片点击 或 open_webpage action 按钮
function onOpenWebpage(payload: { html_content?: string; html?: string; title?: string }) {
  const html = payload.html_content || payload.html || ''
  const title = payload.title || '详情页'
  if (!html) return
  webpageContent.value = html
  webpageTitle.value = title
  showWebpageViewer.value = true
  emit('open-webpage', { htmlContent: html, title })
  // 同时触发内联打开事件，让父组件可以在页面内展示
  emit('inline-open', { title, html })
}

// 来自 open_webpage action 按钮点击
function onOpenWebpageAction(action: ComponentAction) {
  const html = action.params?.html_content || ''
  const title = action.params?.title || action.function_name || '详情页'
  if (!html) return
  onOpenWebpage({ html_content: html, title })
}

function closeWebpageViewer() {
  showWebpageViewer.value = false
}

// Esc 键关闭全屏查看器
function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape' && showWebpageViewer.value) {
    closeWebpageViewer()
  }
}
onMounted(() => window.addEventListener('keydown', onKeydown))
onUnmounted(() => window.removeEventListener('keydown', onKeydown))

function onVersion(versionId: string) {
  emit('switch-version', { versionId })
}
</script>

<template>
  <div class="generative-renderer">
    <!-- 标题区 -->
    <div v-if="protocol.title" class="renderer-title-section">
      <h3 class="font-serif text-2xl text-[#111111] leading-snug">{{ protocol.title }}</h3>
    </div>

    <!-- 组件流式渲染 -->
    <div class="renderer-components">
      <template v-for="(c, i) in protocol.components" :key="c.id || c.type + '_' + i">
        <!-- hero_section: 全宽沉浸式渲染 -->
        <component
          v-if="componentRegistry[c.type] && c.type === 'hero_section'"
          :is="componentRegistry[c.type]"
          :props="c.props"
          class="hero-full-width"
        />

        <!-- grid_layout: 网格容器特殊处理 -->
        <component
          v-else-if="componentRegistry[c.type] && c.type === 'grid_layout'"
          :is="componentRegistry[c.type]"
          :props="c.props"
          class="grid-wrapper"
        />

        <!-- chart: 图表全宽展示 -->
        <component
          v-else-if="componentRegistry[c.type] && c.type === 'chart'"
          :is="componentRegistry[c.type]"
          :props="c.props"
          class="chart-block"
        />

        <!-- compare: 对比表全宽 -->
        <component
          v-else-if="componentRegistry[c.type] && c.type === 'compare'"
          :is="componentRegistry[c.type]"
          :props="c.props"
          class="compare-block"
        />

        <!-- timeline: 时间线全宽 -->
        <component
          v-else-if="componentRegistry[c.type] && c.type === 'timeline'"
          :is="componentRegistry[c.type]"
          :props="c.props"
          class="timeline-block"
        />

        <!-- webpage 类型组件：监听 open 事件 -->
        <component
          v-else-if="componentRegistry[c.type] && c.type === 'webpage'"
          :is="componentRegistry[c.type]"
          :props="c.props"
          class="webpage-block"
          @open="onOpenWebpage"
        />

        <!-- 其他普通组件：标准卡片包裹 -->
        <div v-else-if="componentRegistry[c.type]" class="standard-card">
          <component
            :is="componentRegistry[c.type]"
            :props="c.props"
          />
        </div>

        <!-- 未注册组件 -->
        <UnknownBlock v-else :props="c.props" :type="c.type" />
      </template>
    </div>

    <div class="mt-5 pt-4 border-t border-[#E8E6E1]/60 flex items-center gap-2 flex-wrap">
      <el-button size="small" round :loading="loading" @click="onRegenerate">
        <el-icon v-if="!loading" class="mr-1"><Refresh /></el-icon>
        再思考
      </el-button>

      <el-dropdown v-if="versionsList.length > 1" trigger="click" @command="onVersion">
        <el-button size="small" round>
          版本 {{ currentVersionNo ?? '切换' }}
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item
              v-for="v in versionsList"
              :key="v.id"
              :command="v.id"
              :disabled="v.version_no === currentVersionNo"
            >v{{ v.version_no }} · {{ v.source }}</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>

      <el-button
        v-for="(a, i) in expandActions"
        :key="'ex' + i"
        size="small"
        round
        plain
        @click="onExpand(a)"
      >展开</el-button>

      <el-button
        v-for="(a, i) in fnActions"
        :key="'fn' + i"
        size="small"
        round
        plain
        @click="onFunctionCall(a)"
      >{{ a.function_name || '工具调用' }}</el-button>

      <!-- open_webpage action 按钮：打开预生成的全屏 HTML 子页面 -->
      <el-button
        v-for="(a, i) in webPageActions"
        :key="'wp' + i"
        size="small"
        round
        type="primary"
        plain
        @click="onOpenWebpageAction(a)"
      >
        <el-icon class="mr-1"><FullScreen /></el-icon>
        {{ a.params?.title || a.function_name || '查看详情' }}
      </el-button>
    </div>

    <!-- 全屏 HTML 网页查看器（真正全屏，覆盖整个视口） -->
    <Teleport to="body">
      <transition name="webpage-fade">
        <div
          v-if="showWebpageViewer"
          class="fixed inset-0 z-[9999] bg-white flex flex-col"
        >
          <!-- 顶部工具栏 -->
          <div class="shrink-0 flex items-center justify-between px-6 h-14 border-b border-[#E8E6E1] bg-white">
            <div class="flex items-center gap-3 min-w-0">
              <el-icon :size="18" class="text-[#111] shrink-0"><FullScreen /></el-icon>
              <span class="font-serif text-[16px] text-[#111] truncate">{{ webpageTitle }}</span>
            </div>
            <div class="flex items-center gap-2 shrink-0">
              <span class="text-[11px] text-[#999] hidden md:block">按 Esc 关闭</span>
              <el-button text circle size="default" @click="closeWebpageViewer" title="关闭 (Esc)">
                <el-icon :size="20"><Close /></el-icon>
              </el-button>
            </div>
          </div>
          <!-- HTML 内容（iframe srcdoc 隔离，铺满剩余空间） -->
          <iframe
            :srcdoc="webpageContent"
            class="flex-1 w-full border-0 bg-white"
            sandbox="allow-scripts allow-same-origin"
            title="webpage-viewer"
          />
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<style scoped>
.generative-renderer {
  display: flex;
  flex-direction: column;
}

.renderer-title-section {
  padding: 0 0 16px;
  margin-bottom: 4px;
}

.renderer-title-section h3 {
  font-family: Georgia, 'Times New Roman', serif;
  font-size: 20px;
  color: #111;
  line-height: 1.35;
  font-weight: 700;
}

.renderer-components {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

/* Hero 全宽沉浸式 */
.hero-full-width {
  margin: -4px -5px 0;
  border-radius: 10px;
  overflow: hidden;
}

/* Grid 布局容器 */
.grid-wrapper {
  border-radius: 10px;
  overflow: hidden;
}

/* 图表全宽展示 */
.chart-block {
  background: #FAFAFA;
  border-radius: 12px;
  padding: 18px;
  border: 1px solid #F0EFE9;
}
.chart-block:hover {
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  transition: box-shadow 0.2s ease;
}

/* 对比表全宽 */
.compare-block {
  border-radius: 12px;
  overflow: hidden;
}

/* 时间线全宽 */
.timeline-block {
  background: #FAFAFA;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #F0EFE9;
}

/* Webpage 入口卡片 */
.webpage-block {
  border-radius: 12px;
  overflow: hidden;
}

/* 标准卡片包裹（text_block / list / stat / tabs / accordion 等） */
.standard-card {
  background: white;
  border-radius: 10px;
  padding: 18px 20px;
  border: 1px solid #F2F0EA;
  transition: all 0.2s ease;
}
.standard-card:hover {
  border-color: #E0DED8;
  box-shadow: 0 1px 6px rgba(0,0,0,0.04);
}

/* 操作按钮区 */
.mt-5.pt-4.border-t {
  margin-top: 18px !important;
  padding-top: 14px !important;
  border-top-color: #F0EFE9 !important;
}

.webpage-fade-enter-active,
.webpage-fade-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}
.webpage-fade-enter-from,
.webpage-fade-leave-to {
  opacity: 0;
  transform: scale(0.98);
}
</style>
