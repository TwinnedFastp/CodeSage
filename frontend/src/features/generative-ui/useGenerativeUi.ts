import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import * as genApi from './api'
import type { ComponentProtocol, FunctionMeta, NodeVersionSummary, Component } from './types'

export interface GenerativeMessage {
  id: string
  role: 'user' | 'assistant'
  content?: string
  protocol?: ComponentProtocol
  nodeId?: string
  versions?: NodeVersionSummary[]
  currentVersionNo?: number
  loading?: boolean
  error?: boolean
  // 流式思考阶段
  thinkingRaw?: string
  thinkingDone?: boolean
  // JSONL 增量渲染：逐步收集部分组件
  partialComponents?: Component[]
  partialTitle?: string
}

export function useGenerativeUi() {
  const auth = useAuthStore()
  const messages = ref<GenerativeMessage[]>([])
  const streaming = ref(false)
  const currentNodeId = ref<string | null>(null)
  const functions = ref<FunctionMeta[]>([])

  function findAssistant(id: string) {
    return messages.value.find((m) => m.id === id)
  }

  async function refreshVersionsFor(nodeId: string, assistantId: string) {
    try {
      const detail = await genApi.getNode(nodeId)
      const m = findAssistant(assistantId)
      if (m) {
        m.versions = detail.versions
        m.currentVersionNo = detail.node.current_version?.version_no
      }
    } catch {
      // 版本信息加载失败不阻断主流程
    }
  }

  async function streamComponentChat(
    message: string,
    sessionId?: string,
    useRag = false,
    mode = 'hybrid',
  ): Promise<string | null> {
    if (!message.trim() || streaming.value) return null

    const userText = message.trim()
    const userMsgId = `u-${Date.now()}`
    const assistantId = `a-${Date.now()}`
    messages.value.push({ id: userMsgId, role: 'user', content: userText })
    messages.value.push({ id: assistantId, role: 'assistant', content: '', loading: true, thinkingRaw: '', thinkingDone: false, partialComponents: [] })
    streaming.value = true

    let backendSessionId: string | null = sessionId || null

    try {
      const token = auth.accessToken
      const response = await fetch('/api/v1/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          message: userText,
          session_id: sessionId,
          use_rag: useRag,
          mode,
          render_mode: 'component',
        }),
      })
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      if (!response.body) throw new Error('无响应流')

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let lineBuffer = ''
      let receivedComponent = false

      while (true) {
        const { value, done } = await reader.read()
        if (done) break
        lineBuffer += decoder.decode(value, { stream: true })
        const lines = lineBuffer.split('\n')
        lineBuffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const data = line.slice(6)
          if (data === '[DONE]') {
            const m = findAssistant(assistantId)
            if (m) m.loading = false
            continue
          }
          try {
            const parsed = JSON.parse(data)
            if (parsed.error) {
              const m = findAssistant(assistantId)
              if (m) {
                m.error = true
                m.loading = false
                m.content = m.content || `出错：${parsed.error}`
              }
              ElMessage.error(String(parsed.error))
              continue
            }
            if (parsed.session_id && !backendSessionId) {
              backendSessionId = parsed.session_id as string
              continue
            }
            // JSONL 增量：标题行
            if (parsed.partial_title) {
              const m = findAssistant(assistantId)
              if (m) m.partialTitle = parsed.partial_title
              continue
            }
            // JSONL 增量：单个组件（边生成边渲染）
            if (parsed.partial_component) {
              const m = findAssistant(assistantId)
              if (m) {
                if (!m.partialComponents) m.partialComponents = []
                m.partialComponents.push(parsed.partial_component as Component)
              }
              continue
            }
            // 流式原始文本片段：AI 正在生成组件 JSON，写入思考区实时显示
            if (parsed.streaming_raw) {
              const m = findAssistant(assistantId)
              if (m && !receivedComponent) {
                m.thinkingRaw = (m.thinkingRaw || '') + parsed.streaming_raw
              }
              continue
            }
            if (parsed.content) {
              const m = findAssistant(assistantId)
              if (m && !receivedComponent) {
                m.thinkingRaw = (m.thinkingRaw || '') + parsed.content
              }
              continue
            }
            if (parsed.node_id) {
              currentNodeId.value = parsed.node_id as string
              const m = findAssistant(assistantId)
              if (m) m.nodeId = parsed.node_id as string
              continue
            }
            if (parsed.component) {
              receivedComponent = true
              const m = findAssistant(assistantId)
              if (m) {
                m.protocol = parsed.component as ComponentProtocol
                m.content = ''
                m.loading = false
                m.thinkingDone = true
              }
              continue
            }
          } catch {
            // 忽略非 JSON 帧（如被拆分的不完整行）
          }
        }
      }

      const m = findAssistant(assistantId)
      if (m) {
        m.loading = false
        m.thinkingDone = true
      }
      if (m?.nodeId) {
        await refreshVersionsFor(m.nodeId, assistantId)
      }
    } catch (err: any) {
      const m = findAssistant(assistantId)
      if (m) {
        m.loading = false
        m.error = true
        m.thinkingDone = true
        m.content = `抱歉，生成式回复时发生错误：${err?.message || '未知错误'}`
      }
      console.error('streamComponentChat error', err)
    } finally {
      streaming.value = false
    }

    return backendSessionId
  }

  async function expandNode(nodeId: string, message: string) {
    try {
      const out = await genApi.expandNode(nodeId, message)
      const msgId = `a-${Date.now()}`
      messages.value.push({
        id: msgId,
        role: 'assistant',
        protocol: out.component,
        nodeId: out.node_id,
        loading: false,
      })
      currentNodeId.value = out.node_id
      await refreshVersionsFor(out.node_id, msgId)
    } catch (err: any) {
      ElMessage.error(err.response?.data?.detail || '展开节点失败')
    }
  }

  async function regenerateNode(nodeId: string) {
    const target = messages.value.find((m) => m.nodeId === nodeId && m.role === 'assistant')
    if (target) target.loading = true
    try {
      const out = await genApi.regenerateNode(nodeId)
      if (target) {
        target.protocol = out.component
        target.loading = false
      }
      currentNodeId.value = out.node_id
      if (target) await refreshVersionsFor(out.node_id, target.id)
    } catch (err: any) {
      if (target) target.loading = false
      ElMessage.error(err.response?.data?.detail || '再思考失败')
    }
  }

  async function callFunction(
    fnName: string,
    params: Record<string, any>,
    targetNodeId?: string,
  ) {
    try {
      const out = await genApi.callFunction(fnName, params, targetNodeId)
      if (!out.success) {
        ElMessage.error(out.error || '函数调用失败')
        return out
      }
      if (out.node_id) {
        const existing = targetNodeId
          ? messages.value.find((m) => m.nodeId === targetNodeId)
          : undefined
        if (existing) {
          const detail = await genApi.getNode(out.node_id)
          existing.protocol = detail.node.current_version?.content_json || existing.protocol
          existing.versions = detail.versions
          existing.currentVersionNo = detail.node.current_version?.version_no
          existing.loading = false
        } else {
          const msgId = `a-${Date.now()}`
          messages.value.push({
            id: msgId,
            role: 'assistant',
            loading: false,
            nodeId: out.node_id,
          })
          await refreshVersionsFor(out.node_id, msgId)
        }
      }
      return out
    } catch (err: any) {
      ElMessage.error(err.response?.data?.detail || '函数调用失败')
      return null
    }
  }

  async function loadNode(id: string) {
    try {
      const detail = await genApi.getNode(id)
      const proto = detail.node.current_version?.content_json
      if (!proto) return
      messages.value.push({
        id: `a-${Date.now()}`,
        role: 'assistant',
        protocol: proto,
        nodeId: detail.node.id,
        versions: detail.versions,
        currentVersionNo: detail.node.current_version?.version_no,
        loading: false,
      })
      currentNodeId.value = detail.node.id
    } catch (err: any) {
      ElMessage.error(err.response?.data?.detail || '加载节点失败')
    }
  }

  async function switchVersion(nodeId: string, versionId: string) {
    const target = messages.value.find((m) => m.nodeId === nodeId && m.role === 'assistant')
    if (target) target.loading = true
    try {
      const detail = await genApi.getNode(nodeId)
      const selected = detail.versions.find((v) => v.id === versionId)
      const versionWithContent = selected?.content_json
        ? selected
        : detail.node.current_version?.id === versionId
          ? detail.node.current_version
          : null
      if (target) {
        if (versionWithContent?.content_json) {
          target.protocol = versionWithContent.content_json as ComponentProtocol
        }
        target.versions = detail.versions
        target.currentVersionNo = selected?.version_no ?? detail.node.current_version?.version_no
        target.nodeId = nodeId
        target.loading = false
      }
    } catch (err: any) {
      if (target) target.loading = false
      ElMessage.error(err.response?.data?.detail || '切换版本失败')
    }
  }

  async function loadFunctions() {
    try {
      const out = await genApi.listFunctions()
      functions.value = out.functions || []
    } catch (err: any) {
      ElMessage.error(err.response?.data?.detail || '加载函数列表失败')
    }
  }

  /**
   * 加载某会话的生成式历史：从 UiNode 列表还原对话流。
   * 每个节点对应一条 assistant 消息（含组件协议）。
   * 用户消息从 chat_messages 表加载（render_mode='component' 的）。
   */
  async function loadSessionHistory(sessionId: string) {
    clearMessages()
    try {
      // 1. 加载该会话的 component 模式消息（user + assistant）
      const convResp = await fetch(`/api/v1/conversations/sessions/${sessionId}/messages?limit=100&offset=0`, {
        headers: { Authorization: `Bearer ${auth.accessToken}` },
      })
      if (convResp.ok) {
        const msgs = await convResp.json() as any[]
        const componentMsgs = msgs.filter((m: any) => m.render_mode === 'component')
        const userMsgs = componentMsgs.filter((m: any) => m.role === 'user')

        // 2. 加载该会话的 UiNode 列表
        const { nodes } = await genApi.listNodesBySession(sessionId)

        // 3. 按节点顺序还原对话：user 消息和 assistant 节点交替
        //    简化策略：按时间顺序合并 user 消息和 node（assistant）
        interface TimelineItem {
          ts: string
          type: 'user' | 'assistant'
          data: any
        }
        const timeline: TimelineItem[] = []
        for (const um of userMsgs) {
          timeline.push({ ts: um.created_at, type: 'user', data: um })
        }
        for (const n of nodes) {
          timeline.push({ ts: n.node.created_at, type: 'assistant', data: n })
        }
        timeline.sort((a, b) => new Date(a.ts).getTime() - new Date(b.ts).getTime())

        // 记录已显示的 assistant node id
        const nodeIdsShown = new Set<string>()

        for (const item of timeline) {
          if (item.type === 'user') {
            messages.value.push({
              id: `u-${item.data.message_id}`,
              role: 'user',
              content: item.data.content,
            })
          } else {
            const proto = item.data.node.current_version?.content_json
            if (proto) {
              messages.value.push({
                id: `a-${item.data.node.id}`,
                role: 'assistant',
                protocol: proto,
                nodeId: item.data.node.id,
                loading: false,
              })
              nodeIdsShown.add(item.data.node.id)
            }
          }
        }

        // 检测断线恢复：只有当会话有 component 消息但没有对应 UiNode 时，
        // 才从 _streaming_partial 消息恢复（正常完成的流程已通过 UiNode 显示）
        if (nodes.length === 0) {
          const assistantMsgs = componentMsgs.filter((m: any) => m.role === 'assistant')
          for (const am of assistantMsgs) {
            if (!am.content || am.content.length < 10) continue
            try {
              const parsed = JSON.parse(am.content)
              if (parsed._streaming_partial && parsed.components?.length) {
                messages.value.push({
                  id: `a-recover-${am.message_id || Date.now()}`,
                  role: 'assistant',
                  protocol: parsed as ComponentProtocol,
                  loading: false,
                })
                break // 只恢复最后一条 partial
              }
            } catch {
              // 非 JSON 内容，跳过
            }
          }
        }
      }
    } catch (err: any) {
      console.error('loadSessionHistory error', err)
    }
  }

  function clearMessages() {
    messages.value = []
  }

  return {
    messages,
    streaming,
    currentNodeId,
    functions,
    streamComponentChat,
    expandNode,
    regenerateNode,
    callFunction,
    loadNode,
    switchVersion,
    loadFunctions,
    loadSessionHistory,
    clearMessages,
  }
}
