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
  <div class="rounded-2xl bg-white border border-[#E8E6E1] p-5 md:p-6 shadow-[0_2px_12px_rgb(0,0,0,0.03)]">
    <h3 v-if="protocol.title" class="font-serif text-xl text-[#111111] leading-snug mb-4">{{ protocol.title }}</h3>

    <div class="space-y-4">
      <template v-for="(c, i) in protocol.components" :key="c.id || c.type + '_' + i">
        <!-- webpage 类型组件：监听 open 事件 -->
        <component
          v-if="componentRegistry[c.type] && c.type === 'webpage'"
          :is="componentRegistry[c.type]"
          :props="c.props"
          @open="onOpenWebpage"
        />
        <!-- 其他普通组件 -->
        <component
          v-else-if="componentRegistry[c.type]"
          :is="componentRegistry[c.type]"
          :props="c.props"
        />
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
