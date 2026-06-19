<script setup lang="ts">
import { ref } from 'vue'
import { Collection, Upload, Delete, Document } from '@element-plus/icons-vue'

const props = defineProps<{
  visible: boolean
  documents: any[]
  loadingDocs: boolean
  uploading: boolean
}>()

const emit = defineEmits<{
  'update:visible': [val: boolean]
  upload: [text: string, source?: string]
  remove: [docId: string]
  refresh: []
}>()

const uploadText = ref('')
const uploadSource = ref('')

function close() { emit('update:visible', false) }

async function doUpload() {
  if (!uploadText.value.trim()) return
  emit('upload', uploadText.value, uploadSource.value || undefined)
  uploadText.value = ''
  uploadSource.value = ''
}

function formatTime(t: string) {
  if (!t) return '-'
  return t.replace('T', ' ').slice(0, 19)
}

function formatSize(len: number) {
  if (!len) return '-'
  if (len < 1024) return `${len} B`
  if (len < 1024 * 1024) return `${(len / 1024).toFixed(1)} KB`
  return `${(len / 1024 / 1024).toFixed(1)} MB`
}
</script>

<template>
  <el-drawer
    :model-value="visible"
    @update:model-value="close"
    direction="rtl"
    size="440px"
    :with-header="false"
    class="!bg-[#FAFAFA]"
  >
    <div class="flex flex-col h-full p-6">
      <!-- 头部 -->
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-2.5">
          <div class="w-7 h-7 bg-[#111111] rounded-full flex items-center justify-center text-white">
            <el-icon :size="14"><Collection /></el-icon>
          </div>
          <h3 class="font-serif text-xl text-[#111111]">知识库</h3>
        </div>
        <button @click="close" class="text-[13px] text-[#777] hover:text-[#111] transition-colors">关闭</button>
      </div>

      <!-- 上传区域 -->
      <div class="mb-6 p-4 rounded-2xl bg-white border border-[#E8E6E1]">
        <div class="flex items-center gap-2 mb-3">
          <el-icon :size="14" class="text-[#555]"><Upload /></el-icon>
          <span class="text-[13px] font-semibold text-[#111]">写入新文档</span>
        </div>
        <input
          v-model="uploadSource"
          placeholder="来源（可选，如：项目文档 / 论文 / 笔记）"
          class="w-full mb-2 px-3 py-2 text-[13px] bg-[#FAFAFA] border border-[#E8E6E1] rounded-lg outline-none focus:border-[#111] transition-colors"
        />
        <textarea
          v-model="uploadText"
          placeholder="粘贴或输入要写入知识库的文本内容..."
          rows="5"
          class="w-full mb-3 px-3 py-2 text-[13px] bg-[#FAFAFA] border border-[#E8E6E1] rounded-lg outline-none focus:border-[#111] transition-colors resize-none custom-scrollbar"
        ></textarea>
        <button
          @click="doUpload"
          :disabled="!uploadText.trim() || uploading"
          class="w-full h-9 bg-[#111] hover:bg-[#333] text-white rounded-full text-[13px] font-medium transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          <span v-if="!uploading">写入知识库</span>
          <span v-else>处理中…</span>
        </button>
      </div>

      <!-- 文档列表 -->
      <div class="flex items-center justify-between mb-3">
        <span class="text-[13px] font-semibold text-[#111]">已有文档 ({{ documents.length }})</span>
        <button @click="$emit('refresh')" class="text-[12px] text-[#777] hover:text-[#111] transition-colors">刷新</button>
      </div>

      <div class="flex-1 overflow-y-auto space-y-2 custom-scrollbar">
        <div v-if="loadingDocs" class="text-center text-[12px] text-[#999] py-8">加载中…</div>
        <div
          v-for="doc in documents"
          :key="doc.id"
          class="group p-3 rounded-xl bg-white border border-[#E8E6E1] hover:border-[#D1CFCA] transition-colors"
        >
          <div class="flex items-start justify-between gap-2 mb-1.5">
            <div class="flex items-center gap-2 min-w-0 flex-1">
              <el-icon :size="14" class="text-[#777] shrink-0"><Document /></el-icon>
              <span class="text-[13px] font-medium text-[#111] truncate">{{ doc.content_summary || doc.id.slice(0, 12) }}</span>
            </div>
            <button
              @click="$emit('remove', doc.id)"
              class="shrink-0 p-1 rounded-md opacity-0 group-hover:opacity-100 hover:bg-[#F3F2EE] text-[#999] hover:text-[#D9483F] transition-all"
              title="删除"
            >
              <el-icon :size="13"><Delete /></el-icon>
            </button>
          </div>
          <div class="flex items-center gap-3 text-[11px] text-[#999] ml-5">
            <span>{{ formatSize(doc.content_length) }}</span>
            <span class="px-1.5 py-0.5 rounded bg-[#F3F2EE] text-[#555]">{{ doc.status }}</span>
            <span>{{ formatTime(doc.created_at) }}</span>
          </div>
        </div>
        <div v-if="!loadingDocs && documents.length === 0" class="text-center text-[12px] text-[#999] py-12">
          知识库还是空的<br />上传第一个文档开始使用 RAG
        </div>
      </div>

      <!-- 底部说明 -->
      <div class="pt-4 mt-4 border-t border-[#E8E6E1]">
        <p class="text-[11px] text-[#999] leading-relaxed">
          知识库由 LightRAG 驱动，写入时会自动分块、抽取实体关系、向量化并构建知识图谱。
          聊天时开启 RAG 模式即可检索知识库内容。
        </p>
      </div>
    </div>
  </el-drawer>
</template>
