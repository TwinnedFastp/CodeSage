/**
 * RAG 知识库 API 封装
 */
import request from './request'

export interface RagDocument {
  id: string
  content_summary: string
  content_length: number
  status: string
  created_at: string
  updated_at: string
}

export interface RagStatus {
  enabled: boolean
  has_provider_config: boolean
  ready: boolean
}

export interface RagQueryResult {
  answer: string
  mode: string
}

/** 检查 RAG 是否可用 */
export function getRagStatus() {
  return request.get<RagStatus>('/rag/status').then(r => r.data)
}

/** 写入文本到知识库 */
export function insertDocument(text: string, source?: string) {
  return request.post<{ success: boolean; message: string }>('/rag/documents', { text, source }).then(r => r.data)
}

/** 列出知识库文档 */
export function listDocuments() {
  return request.get<{ documents: RagDocument[]; total: number }>('/rag/documents').then(r => r.data)
}

/** 删除知识库文档 */
export function deleteDocument(docId: string) {
  return request.delete<{ success: boolean; message: string }>(`/rag/documents/${docId}`).then(r => r.data)
}

/** 独立查询知识库（不经过聊天接口） */
export function queryKnowledge(question: string, mode: 'naive' | 'local' | 'global' | 'hybrid' = 'hybrid') {
  return request.post<RagQueryResult>('/rag/query', { question, mode }).then(r => r.data)
}

/** 上传文件到知识库（MD/TXT 文本内容） */
export function uploadFile(payload: { filename: string; content: string; source?: string }) {
  return request.post<FileUploadOut>('/rag/upload-file', payload).then(r => r.data)
}

export interface FileUploadOut {
  success: boolean
  message: string
}
