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

/** 写入文本到知识库（同 uploadFile，给 180s 超时） */
export function insertDocument(text: string, source?: string) {
  return request.post<{ success: boolean; message: string }>('/rag/documents', { text, source }, { timeout: 180000 }).then(r => r.data)
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
export function queryKnowledge(question: string, mode: 'naive' | 'local' | 'global' | 'hybrid' | 'mix' = 'hybrid') {
  return request.post<RagQueryResult>('/rag/query', { question, mode }).then(r => r.data)
}

/** 上传文件到知识库（MD/TXT 文本内容）
 * 知识库处理含 LLM 实体抽取+向量化，后端同步等待最多 120s，
 * 这里给 180s 超时兜底，避免前端先于后端断开导致 499。
 */
export function uploadFile(payload: { filename: string; content: string; source?: string }) {
  return request.post<FileUploadOut>('/rag/upload-file', payload, { timeout: 180000 }).then(r => r.data)
}

export interface FileUploadOut {
  success: boolean
  message: string
}

/** 重建知识库：DROP 所有 lightrag 表 + 清空缓存（会清空所有文档） */
export function resetKnowledge() {
  return request.post<{ success: boolean; message: string }>('/rag/reset').then(r => r.data)
}
