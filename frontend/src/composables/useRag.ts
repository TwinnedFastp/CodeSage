/**
 * RAG 知识库管理：状态检查 / 文档上传 / 文件上传 / 文档列表 / 文档删除
 */
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as ragApi from '@/api/rag'
import type { RagDocument, RagStatus } from '@/api/rag'

export function useRag() {
  const ragReady = ref(false)
  const ragEnabled = ref(false)
  // 默认关闭：避免 RAG 环境故障连累普通对话，用户显式开启才走知识库检索
  // 6 种模式对齐 backend/rag/service.py:361 的 LightRAG 原生支持（含 mix 知识图谱+向量、bypass 跳过检索）
  const ragMode = ref<'off' | 'naive' | 'local' | 'global' | 'hybrid' | 'mix'>('off')
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

  async function uploadFile(filename: string, content: string, source?: string) {
    if (!content.trim()) { ElMessage.warning('文件内容为空'); return false }
    uploading.value = true
    try {
      const result = await ragApi.uploadFile({ filename, content, source })
      ElMessage.success(result.message || '文件已写入知识库')
      await loadDocuments()
      return true
    } catch (err: any) {
      ElMessage.error(err.response?.data?.detail || '上传文件失败')
      return false
    } finally {
      uploading.value = false
    }
  }

  function openKnowledgePanel() {
    knowledgePanelVisible.value = true
    loadDocuments()
  }

  async function resetKnowledge() {
    try {
      await ElMessageBox.confirm(
        '重建会清空知识库中所有文档与向量数据，且不可恢复，确定继续吗？',
        '重建知识库',
        {
          type: 'warning',
          confirmButtonText: '重建',
          cancelButtonText: '取消',
          confirmButtonClass: 'el-button--danger',
        },
      )
    } catch { return false }

    try {
      const result = await ragApi.resetKnowledge()
      documents.value = []
      ElMessage.success(result.message || '知识库已重建')
      await checkStatus()
      return true
    } catch (err: any) {
      ElMessage.error(err.response?.data?.detail || '重建知识库失败')
      return false
    }
  }

  onMounted(() => { checkStatus() })

  return {
    ragReady, ragEnabled, ragMode, ragActive,
    documents, loadingDocs, uploading, knowledgePanelVisible,
    checkStatus, loadDocuments, uploadDocument, uploadFile, removeDocument,
    resetKnowledge, openKnowledgePanel,
  }
}
