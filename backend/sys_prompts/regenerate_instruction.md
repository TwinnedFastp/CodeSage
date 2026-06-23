# ============================================================================
# 节点"再思考"默认指令
# ============================================================================
#
# 【调用位置】
#   backend/services/node_service.py → regenerate_node()
#
# 【使用场景】
#   用户在详情页点击"再思考"按钮时，AI 基于现有节点内容重新生成
#   一个全新的组件协议版本。此提示词作为 instruction 参数的默认值。
#
# 【注入方式】
#   component_service.generate_component_protocol() 的 user message
#
# 【关联提示词】
#   component_protocol.md — 作为 system prompt 一起发送给 LLM
#
# 【可用工具】
#   draw_beautiful_page / draw_ui_page / draw_dashboard 等（通过 function calling 注入）
#
# ============================================================================
请基于上下文重新生成该界面，使用 draw_beautiful_page 工具生成一个全新的专业网页，输出完整组件协议 JSON。
