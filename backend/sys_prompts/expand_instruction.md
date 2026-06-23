# ============================================================================
# 节点"展开"默认指令
# ============================================================================
#
# 【调用位置】
#   backend/services/node_service.py → expand_node()
#
# 【使用场景】
#   用户在对话中点击"展开"按钮时，AI 基于父节点内容生成子节点的
#   首版组件协议。此提示词作为 instruction 参数的默认值。
#
# 【注入方式】
#   component_service.generate_component_protocol() 的 user message
#
# 【关联提示词】
#   component_protocol.md — 作为 system prompt 一起发送给 LLM
#
# 【可用工具】
#   draw_beautiful_page / draw_ui_page 等（通过 function calling 注入）
#
# ============================================================================
请详细展开说明该主题的所有方面，输出完整组件协议 JSON。
