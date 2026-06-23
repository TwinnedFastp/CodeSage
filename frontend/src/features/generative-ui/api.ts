import request from '@/api/request'
import type {
  ExpandOut,
  FunctionCallOut,
  FunctionsListOut,
  KnowledgeIngestOut,
  KnowledgeQueryOut,
  NodeDetail,
  RegenerateOut,
} from './types'

export function getNode(id: string): Promise<NodeDetail> {
  return request.get<NodeDetail>(`/nodes/${id}`).then((r) => r.data)
}

/** 列出某会话下的所有生成式节点（含当前版本内容），用于加载历史 */
export function listNodesBySession(sessionId: string): Promise<{ nodes: any[] }> {
  return request.get<{ nodes: any[] }>(`/nodes/by-session/${sessionId}`).then((r) => r.data)
}

export function expandNode(id: string, message: string): Promise<ExpandOut> {
  return request.post<ExpandOut>(`/nodes/${id}/expand`, { message }).then((r) => r.data)
}

export function regenerateNode(id: string): Promise<RegenerateOut> {
  return request.post<RegenerateOut>(`/nodes/${id}/regenerate`, {}).then((r) => r.data)
}

export function knowledgeIngest(text: string, source?: string): Promise<KnowledgeIngestOut> {
  return request.post<KnowledgeIngestOut>('/knowledge/ingest', { text, source }).then((r) => r.data)
}

export function knowledgeQuery(question: string, mode?: string): Promise<KnowledgeQueryOut> {
  return request.post<KnowledgeQueryOut>('/knowledge/query', { question, mode }).then((r) => r.data)
}

export function listFunctions(): Promise<FunctionsListOut> {
  return request.get<FunctionsListOut>('/functions/list').then((r) => r.data)
}

export function callFunction(
  function_name: string,
  params: Record<string, any>,
  target_node_id?: string,
): Promise<FunctionCallOut> {
  return request
    .post<FunctionCallOut>('/functions/call', { function_name, params, target_node_id })
    .then((r) => r.data)
}
