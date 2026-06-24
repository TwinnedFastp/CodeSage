// 全局类型定义
export interface User {
  id: number
  email: string
  username: string
  avatar_url?: string | null
  email_verified: boolean
  created_at: string
  last_login_ip?: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface ChatSession {
  id: string
  user_id: number
  title: string | null
  summary: string | null
  summary_generated_at: string | null
  is_archived: boolean
  archived_at: string | null
  created_at: string
  updated_at: string
}

export interface ChatMessage {
  id: number
  message_id: string
  session_id: string
  user_id: number
  role: 'user' | 'assistant' | 'system'
  content: string
  render_mode?: 'text' | 'component'
  attachments?: MessageAttachment[] | null
  created_at: string
}

export interface UserPreference {
  user_id: number
  preferences: Record<string, unknown>
  updated_at: string | null
}

export interface UserFact {
  id: number
  user_id: number
  fact_key: string
  fact_value: string
  fact_category: string | null
  updated_at: string
}

export interface UserTask {
  id: number
  user_id: number
  session_id: string | null
  title: string
  description: string | null
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled'
  due_date: string | null
  created_at: string
  updated_at: string
}

// 前端展示用的本地消息结构（含流式状态）
export interface DisplayMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  pending?: boolean
  /** 标记该消息来自生成式组件模式（用于显示特殊样式/提示） */
  _isComponent?: boolean
  /** 原始 JSON 内容（用于切换到组件模式时恢复） */
  _rawContent?: string
  /** 消息附件（图片/文档） */
  attachments?: MessageAttachment[]
}

export interface MessageAttachment {
  type: 'image' | 'document'
  data?: string
  filename?: string
}

export interface PendingImage {
  id: string
  dataUrl: string
}

export interface PendingDocument {
  id: string
  filename: string
  content: string
}
