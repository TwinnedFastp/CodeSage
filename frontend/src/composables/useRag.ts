/**
 * RAG 知识库管理：状态检查 / 文档上传 / 文档列表 / 文档删除
 */
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as ragApi from '@/api/rag'
import type { RagDocument, RagStatus } from '@/api/rag'

export function useRag() {
  const ragReady = ref(false)
  const ragEnabled = ref(false)
  const ragMode = ref<'off' | 'naive' | 'local' | 'global' | 'hybrid'>('hybrid')
  const documents = ref<RagDocument[]>([])
  const loadingDocs = ref(false)
  const uploading = ref(false)
  const knowledgePanelVisible = ref(false)

  const ragActive = computed(() => ragMode.value !== 'off')

  async function checkStatus() {
    try {
      const status: RagStatus = await ragApi.getRagStatus()
      ragReady.value = status.ready
      ragEnabled.value = status.enabled
    } catch {
      ragReady.value = false
    }
  }

  async function loadDocuments() {
    loadingDocs.value = true
    try {
      const result = await ragApi.listDocuments()
      documents.value = result.documents || []
    } catch (err: any) {
      ElMessage.error(err.response?.data?.detail || '加载文档列表失败')
    } finally {
      loadingDocs.value = false
    }
  }

  async function uploadDocument(text: string, source?: string) {
    if (!text.trim()) { ElMessage.warning('内容不能为空'); return false }
    uploading.value = true
    try {
      const result = await ragApi.insertDocument(text, source)
      ElMessage.success(result.message || '已写入知识库')
      await loadDocuments()
      return true
    } catch (err: any) {
      ElMessage.error(err.response?.data?.detail || '写入知识库失败')
      return false
    } finally {
      uploading.value = false
    }
  }

  async function removeDocument(docId: string) {
    try {
      await ElMessageBox.confirm('删除后该文档及其相关实体/关系/向量将一并移除，确定继续吗？', '删除文档', {
        type: 'warning',
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        confirmButtonClass: 'el-button--danger',
      })
    } catch { return }

    try {
      await ragApi.deleteDocument(docId)
      documents.value = documents.value.filter(d => d.id !== docId)
      ElMessage.success('已删除')
    } catch (err: any) {
      ElMessage.error(err.response?.data?.detail || '删除失败')
    }
  }

  function openKnowledgePanel() {
    knowledgePanelVisible.value = true
    loadDocuments()
  }

  onMounted(() => { checkStatus() })

  return {
    ragReady, ragEnabled, ragMode, ragActive,
    documents, loadingDocs, uploading, knowledgePanelVisible,
    checkStatus, loadDocuments, uploadDocument, removeDocument,
    openKnowledgePanel,
  }
}
