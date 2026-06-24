/**
 * 聊天流式相关接口（会话恢复 / 进行中流式消息查询 / 断点续传）
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

/** Stream 消息类型（Redis Stream 中的 type 字段） */
export type StreamMessageType = 'start' | 'content' | 'end' | 'error'

/** 单条 Stream 消息（SSE 推送格式） */
export interface StreamMessage {
  msgId: string
  type: StreamMessageType
  content: string
  timestamp: string
}

/**
 * 查询某会话下所有"进行中的流式消息。
 *
 * 使用场景：用户刷新页面 / 重新进入页面后调用，从 Redis 恢复未完成的 AI 回复。
 * 流式正常结束后后端清理 Redis key，此处返回空列表 —— 此时历史已落库 PG，
 * 由 listMessages 拉取即可。
 */
export async function getActiveStreaming(sessionId: string): Promise<ActiveStreamingResponse> {
  const { data } = await request.get(`/chat/streaming/${sessionId}`)
  return data
}

/**
 * SSE 断点续传：从指定消息 ID 继续接收流式消息。
 *
 * 使用 EventSource-like 的 fetch + ReadableStream 方式建立长连接。
 * 返回一个 AbortController 用于取消连接。
 *
 * @param sessionId 会话 ID
 * @param lastMsgId 上次收到的最后一条消息 ID，"0-0" 表示从头开始
 * @param onMessage 收到消息时的回调
 * @param onDone 流式结束时的回调
 * @param onError 发生错误时的回调
 * @returns AbortController 用于手动取消连接
 */
export function continueStream(
  sessionId: string,
  lastMsgId: string,
  onMessage: (msg: StreamMessage) => void,
  onDone?: () => void,
  onError?: (error: string) => void,
): AbortController {
  const controller = new AbortController()
  const token = localStorage.getItem('access_token') || ''

  ;(async () => {
    try {
      const response = await fetch(`/api/v1/chat/stream/continue?session_id=${sessionId}&last_msg_id=${lastMsgId}`, {
        method: 'GET',
        headers: {
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        signal: controller.signal,
      })

      if (!response.ok || !response.body) {
        onError?.(`HTTP ${response.status}`)
        return
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let lineBuffer = ''

      while (true) {
        const { value, done } = await reader.read()
        if (done) break

        lineBuffer += decoder.decode(value, { stream: true })
        const lines = lineBuffer.split('\n')
        lineBuffer = lines.pop() || ''

        for (const line of lines) {
          // 心跳行（以 : 开头的注释）
          if (line.startsWith(':')) continue
          if (!line.startsWith('data: ')) continue

          const data = line.slice(6).trim()
          if (data === '[DONE]') {
            onDone?.()
            return
          }

          try {
            const parsed: StreamMessage = JSON.parse(data)
            onMessage(parsed)
          } catch {
            // 忽略非 JSON 行
          }
        }
      }

      // 流正常结束
      onDone?.()
    } catch (err: any) {
      if (err.name === 'AbortError') return  // 用户主动取消
      onError?.(err.message || '断点续传连接异常')
    }
  })()

  return controller
}

// ---- 本地持久化：lastMsgId 存储 ----

const STREAM_RESUME_KEY_PREFIX = 'codesage_stream_resume:'

/** 获取某会话的断点位置 */
export function getStreamResumePoint(sessionId: string): string | null {
  try {
    return localStorage.getItem(`${STREAM_RESUME_KEY_PREFIX}${sessionId}`)
  } catch {
    return null
  }
}

/** 保存某会话的断点位置 */
export function setStreamResumePoint(sessionId: string, lastMsgId: string): void {
  try {
    localStorage.setItem(`${STREAM_RESUME_KEY_PREFIX}${sessionId}`, lastMsgId)
  } catch { /* 忽略 */ }
}

/** 清除某会话的断点位置 */
export function clearStreamResumePoint(sessionId: string): void {
  try {
    localStorage.removeItem(`${STREAM_RESUME_KEY_PREFIX}${sessionId}`)
  } catch { /* 忽略 */ }
}
