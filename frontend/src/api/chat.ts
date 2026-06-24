/**
 * 聊天流式相关接口（会话恢复 / 进行中流式消息查询）
 */
import request from './request'

/** 进行中的流式消息（来自 Redis 缓存，尚未落库 PG） */
export interface StreamingMessage {
  /** 流式消息唯一标识（后端生成的 stream_token） */
  stream_token: string
  /** 已累加的内容（增量更新） */
  content: string
  /** 角色：assistant */
  role: string
  /** 渲染模式：text / component */
  render_mode: string
  /** 流式开始时间（ISO 8601） */
  started_at: string | null
}

export interface ActiveStreamingResponse {
  items: StreamingMessage[]
  count: number
}

/**
 * 查询某会话下所有"进行中"的流式消息。
 *
 * 使用场景：用户刷新页面 / 重新进入页面后调用，从 Redis 恢复未完成的 AI 回复。
 * 流式正常结束后后端清理 Redis key，此处返回空列表 —— 此时历史已落库 PG，
 * 由 listMessages 拉取即可。
 */
export async function getActiveStreaming(sessionId: string): Promise<ActiveStreamingResponse> {
  const { data } = await request.get(`/chat/streaming/${sessionId}`)
  return data
}
