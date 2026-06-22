// 生成式 UI 模块的共享类型，严格对齐后端 ComponentProtocol 契约

export type ComponentActionType = 'regenerate' | 'expand' | 'function_call'

export interface ComponentAction {
  type: ComponentActionType
  target_id?: string
  function_name?: string
  params?: Record<string, any>
}

export interface Component {
  type: string
  props: Record<string, any>
  id?: string
}

export interface ComponentProtocol {
  page_type: string
  title: string
  components: Component[]
  actions: ComponentAction[]
  meta: Record<string, any>
}

export interface NodeCurrentVersion {
  id: string
  version_no: number
  content_json: ComponentProtocol
  source: string
  created_at: string
}

export interface NodeVersionSummary {
  id: string
  version_no: number
  content_json?: ComponentProtocol
  source: string
  created_at?: string
}

export interface NodeInfo {
  id: string
  conversation_id: string | null
  parent_id: string | null
  node_type: string
  created_at: string
  current_version: NodeCurrentVersion | null
}

export interface NodeDetail {
  node: NodeInfo
  versions: NodeVersionSummary[]
}

export interface ExpandOut {
  node_id: string
  version_no: number
  component: ComponentProtocol
}

export interface RegenerateOut {
  node_id: string
  version_no: number
  component: ComponentProtocol
}

export interface KnowledgeIngestOut {
  success: boolean
  message: string
}

export interface KnowledgeQueryOut {
  answer: string
  mode: string
}

export interface FunctionParam {
  name: string
  type: string
  required: boolean
  description: string
}

export interface FunctionMeta {
  name: string
  description: string
  params: FunctionParam[]
  requires_admin: boolean
}

export interface FunctionsListOut {
  functions: FunctionMeta[]
}

export interface FunctionCallOut {
  success: boolean
  result: any
  error: string | null
  duration_ms: number
  function_name: string
  node_id?: string
  version_no?: number
}
