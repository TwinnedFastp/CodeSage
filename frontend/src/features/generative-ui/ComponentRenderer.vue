<script setup lang="ts">
import { computed } from 'vue'
import { ElMessageBox } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
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
}>()

const expandActions = computed<ComponentAction[]>(() =>
  (props.protocol.actions || []).filter((a) => a.type === 'expand'),
)
const fnActions = computed<ComponentAction[]>(() =>
  (props.protocol.actions || []).filter((a) => a.type === 'function_call'),
)
const versionsList = computed<NodeVersionSummary[]>(() => props.versions || [])

function onRegenerate() {
  emit('regenerate')
}

async function onExpand(action: ComponentAction) {
  try {
    const res = await ElMessageBox.prompt('请输入展开指令', '展开节点', {
      confirmButtonText: '展开',
      cancelButtonText: '取消',
      inputPlaceholder: '继续补充说明…',
    })
    const message = (res?.value || '').trim()
    if (!message) return
    emit('expand', { id: action?.target_id, message })
  } catch {
    // 用户取消
  }
}

function onFunctionCall(action: ComponentAction) {
  emit('function-call', {
    function_name: action?.function_name,
    params: action?.params || {},
    target_id: action?.target_id,
  })
}

function onVersion(versionId: string) {
  emit('switch-version', { versionId })
}
</script>

<template>
  <div class="rounded-2xl bg-white border border-[#E8E6E1] p-5 md:p-6 shadow-[0_2px_12px_rgb(0,0,0,0.03)]">
    <h3 v-if="protocol.title" class="font-serif text-xl text-[#111111] leading-snug mb-4">{{ protocol.title }}</h3>

    <div class="space-y-4">
      <template v-for="(c, i) in protocol.components" :key="c.id || c.type + '_' + i">
        <component v-if="componentRegistry[c.type]" :is="componentRegistry[c.type]" :props="c.props" />
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
    </div>
  </div>
</template>
