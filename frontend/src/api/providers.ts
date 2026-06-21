/**
 * AI 供应商配置 API 封装
 *
 * 对应后端 /api/v1/providers 接口
 */
import request from './request'

export interface Provider {
  id: number
  provider_name: string
  llm_api_key: string // 脱敏后的 key（如 sk-1***xyz）
  llm_base_url: string
  llm_model: string
  embedding_model: string
  embedding_dim: number
  is_enabled: boolean
  created_at: string
  updated_at: string
}

export interface ProviderCreateInput {
  provider_name: string
  llm_api_key: string
  llm_base_url: string
  llm_model: string
  embedding_model: string
  embedding_dim: number
}

export interface ProviderUpdateInput {
  provider_name?: string
  llm_api_key?: string
  llm_base_url?: string
  llm_model?: string
  embedding_model?: string
  embedding_dim?: number
  is_enabled?: boolean
}

/** 列出当前用户的所有供应商配置 */
export function listProviders() {
  return request.get<Provider[]>('/providers').then(r => r.data)
}

/** 新增供应商配置 */
export function createProvider(data: ProviderCreateInput) {
  return request.post<Provider>('/providers', data).then(r => r.data)
}

/** 获取单个供应商配置详情 */
export function getProvider(id: number) {
  return request.get<Provider>(`/providers/${id}`).then(r => r.data)
}

/** 更新供应商配置（部分更新） */
export function updateProvider(id: number, data: ProviderUpdateInput) {
  return request.put<Provider>(`/providers/${id}`, data).then(r => r.data)
}

/** 删除供应商配置 */
export function deleteProvider(id: number) {
  return request.delete(`/providers/${id}`)
}

/** 切换供应商启用/禁用状态 */
export function toggleProvider(id: number) {
  return request.patch<Provider>(`/providers/${id}/toggle`).then(r => r.data)
}
