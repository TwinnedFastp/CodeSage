import request from './request'
import type { ChatSession, ChatMessage, UserPreference, UserFact, UserTask } from '@/types'

// ---- 会话 ----
export async function createSession(title?: string): Promise<ChatSession> {
  const { data } = await request.post('/conversations/sessions', { title: title ?? null })
  return data
}

export async function listSessions(limit = 50, offset = 0, archived = false): Promise<ChatSession[]> {
  const { data } = await request.get('/conversations/sessions', { params: { limit, offset, archived } })
  return data
}

export async function getSession(id: string): Promise<ChatSession> {
  const { data } = await request.get(`/conversations/sessions/${id}`)
  return data
}

export async function updateSession(id: string, payload: { title?: string; summary?: string; is_archived?: boolean }): Promise<ChatSession> {
  const { data } = await request.patch(`/conversations/sessions/${id}`, payload)
  return data
}

export async function archiveSession(id: string): Promise<ChatSession> {
  const { data } = await request.post(`/conversations/sessions/${id}/archive`)
  return data
}

export async function unarchiveSession(id: string): Promise<ChatSession> {
  const { data } = await request.post(`/conversations/sessions/${id}/unarchive`)
  return data
}

export async function deleteSession(id: string): Promise<void> {
  await request.delete(`/conversations/sessions/${id}`)
}

// AI 自动生成会话标题
export async function generateSessionTitle(id: string): Promise<ChatSession> {
  const { data } = await request.post(`/conversations/sessions/${id}/generate-title`)
  return data
}

// ---- 消息 ----
export async function listMessages(sessionId: string, limit = 100, offset = 0): Promise<ChatMessage[]> {
  const { data } = await request.get(`/conversations/sessions/${sessionId}/messages`, {
    params: { limit, offset },
  })
  return data
}

// ---- 偏好 ----
export async function getPreferences(): Promise<UserPreference> {
  const { data } = await request.get('/conversations/preferences')
  return data
}

export async function updatePreferences(prefs: Record<string, unknown>): Promise<UserPreference> {
  const { data } = await request.put('/conversations/preferences', { preferences: prefs })
  return data
}

// ---- 事实记忆 ----
export async function listFacts(category?: string): Promise<UserFact[]> {
  const { data } = await request.get('/conversations/facts', { params: { category } })
  return data
}

export async function upsertFact(payload: { fact_key: string; fact_value: string; fact_category?: string }): Promise<UserFact> {
  const { data } = await request.post('/conversations/facts', payload)
  return data
}

export async function deleteFact(id: number): Promise<void> {
  await request.delete(`/conversations/facts/${id}`)
}

// ---- 任务 ----
export async function listTasks(status?: string): Promise<UserTask[]> {
  const { data } = await request.get('/conversations/tasks', { params: { status } })
  return data
}

export async function createTask(payload: { title: string; description?: string; session_id?: string; due_date?: string; status?: string }): Promise<UserTask> {
  const { data } = await request.post('/conversations/tasks', payload)
  return data
}

export async function updateTask(id: number, payload: { title?: string; description?: string; status?: string; due_date?: string }): Promise<UserTask> {
  const { data } = await request.patch(`/conversations/tasks/${id}`, payload)
  return data
}

export async function deleteTask(id: number): Promise<void> {
  await request.delete(`/conversations/tasks/${id}`)
}
