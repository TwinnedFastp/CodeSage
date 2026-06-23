# CodeSage 生成式交互界面产品文档

# CodeSage 生成式交互界面产品文档

面向开发者的产品说明、架构约定与接口设计

---

# 1\. 产品概述

目标：让 AI 不再只输出 Markdown，而是输出可渲染、可交互、可版本化的 “组件协议”，由前端动态组装界面。

定位：CodeSage 负责产品壳、用户系统、交互体验与业务编排；LightRAG 作为独立能力服务，负责知识检索、知识库管理和上下文召回。

边界：不在 CodeSage 内部重写完整 RAG / 图谱 / 搜索链路，统一通过 LightRAG REST API 接入。

# 2\. 核心体验流程

1. 用户提出问题。

2. 后端先判断是否需要生成交互界面，以及界面需要哪些组件，同步判断是否需要触发工具调用。

3. LLM 输出结构化 JSON（组件计划 \+ 可选函数调用指令），而不是任意 HTML。

4. 前端根据白名单组件库渲染页面。

5. 用户点击组件后，后端只携带局部上下文重新生成该区域内容，或触发对应工具调用。

6. 生成结果写入数据库，并保留版本与父子关系。

7. 用户点击 “再思考” 时，创建新版本并替换当前激活版本。

# 3\. 系统分工

|模块|职责|说明|
|---|---|---|
|Vue3 前端|渲染组件协议|只认 type \+ props \+ actions，不执行任意 HTML/JS|
|FastAPI 网关|统一接口、鉴权与业务编排|负责会话、权限、缓存、向 LightRAG 转发请求；内置独立 Function Calling 模块负责工具调用编排|
|LightRAG Server|知识库能力|负责知识导入、检索、图谱、上下文召回|
|PostgreSQL|主存储 \+ 可选向量能力|存卡片、版本、关系、摘要、会话、审计；启用 pgvector 扩展后可直接承担向量检索|
|向量存储层（可选：Qdrant）|高性能语义检索|超大规模向量场景下独立部署，存向量与 payload，服务相似召回|
|Redis|临时缓存|存验证码、会话临时态、短期缓存|
|Function Calling 模块|工具注册、编排与安全执行|代码独立目录维护，与主业务解耦，负责工具集管理、参数校验、执行沙箱|

# 4\. 组件协议设计

原则：模型不直接输出 HTML，而是输出受控 JSON。后端先校验，再交给前端渲染。

推荐字段：page\_type、title、components、actions、meta。

```json
{
  "page_type": "analysis",
  "title": "登录流程分析",
  "components": [
    {
      "type": "summary_card",
      "props": {
        "title": "结论",
        "content": "这是一个 JWT 登录流程"
      }
    },
    {
      "type": "flowchart",
      "props": {
        "nodes": ["Controller", "Service", "Token"],
        "edges": [["Controller", "Service"], ["Service", "Token"]]
      }
    }
  ],
  "actions": [
    {
      "type": "regenerate",
      "target_id": "node_123"
    }
  ]
}
```

# 5\. 版本化与 “再思考” 机制

- 每个可点击内容都是一个 ui\_node，代表一个稳定对象。

- 每次生成结果、工具调用返回结果都写入 ui\_node\_version，作为版本历史。

- 当前激活版本通过 current\_version\_id 指向。

- “再思考” 不是覆盖旧版本，而是创建新版本并切换激活指针。

- 父子关系使用 parent\_id 外键表示，支持卡片树、展开链、引用链。

|表|作用|关键字段|说明|
|---|---|---|---|
|ui\_node|卡片实体|id, parent\_id, current\_version\_id|保存节点关系|
|ui\_node\_version|版本历史|node\_id, version\_no, content\_json, html\_snapshot|保存每次生成内容|
|ui\_node\_relation|扩展关系|from\_node\_id, to\_node\_id, relation\_type|支持网状连接|

# 6\. 存储策略

- **PostgreSQL**：主存储，保存原文、摘要、版本、父子关系、审计日志；启用 pgvector 扩展后可同时承担向量存储与检索，实现单数据库全链路部署。

- **向量存储层（可插拔选型）**：

    - **pgvector（默认推荐）**：基于 PostgreSQL 扩展实现，无需额外部署服务，适合中小规模知识库、简化技术栈，向量数据与业务数据同库事务一致。

    - **Qdrant（可选）**：独立向量数据库，适合超大规模向量数据集、高并发检索场景，支持更丰富的索引策略与量化优化。

- **Redis**：短期缓存，适合验证码、会话状态、频控、临时任务。

- **厂商模型缓存**：仅作为性能优化层，不作为长期记忆的唯一来源。

# 7\. 记忆与召回策略

- 短期记忆：保留最近若干轮上下文，直接注入 prompt。

- 中期记忆：会话摘要，存 PostgreSQL。

- 长期记忆：用户偏好、项目背景、稳定事实，存 PostgreSQL \+ 向量存储层（pgvector / Qdrant），支持语义召回。

- 临时内容：任务态、一次性解释、短期问答结果，设置 TTL 到期清除。

# 8\. LightRAG 接入方式

- LightRAG 建议独立部署为服务，不要直接把它的全部源码耦合进 CodeSage 主后端。

- CodeSage 通过 FastAPI 调用 LightRAG REST API。

- LightRAG 前端可作为后台管理入口，也可以完全不对普通用户开放。

- 用户前台只访问 CodeSage，管理员用于知识库导入、同步、排错和查看索引状态。

# 9\. 组件安全与格式控制

- 禁止让模型输出任意 HTML 作为唯一数据源。

- 模型只输出 JSON 协议，后端先做 schema 校验，再渲染。

- 前端只允许渲染白名单组件，不允许任意脚本执行。

- 冷门组件采用异步加载，避免一次性把所有模板塞进项目。

# 10\. 推荐的开发路径

- 第一阶段：聊天 \+ 组件协议 \+ 前端渲染 \+ 基础 Function Calling 框架。

- 第二阶段：节点版本化、点击展开、再思考。

- 第三阶段：接入 LightRAG 作为知识能力服务；默认基于 pgvector 实现向量检索。

- 第四阶段：支持向量引擎平滑切换（Qdrant）、记忆压缩、组件懒加载、工具市场扩展。

# 11\. 开发者接口建议

- `POST /api/chat`：接收用户问题，返回组件协议。

- `POST /api/node/{id}/expand`：点击节点后局部展开。

- `POST /api/node/{id}/regenerate`：再思考并生成新版本。

- `GET /api/node/{id}`：按主键直接取历史版本。

- `POST /api/knowledge/ingest`：转发到 LightRAG 导入知识。

- `POST /api/knowledge/query`：转发到 LightRAG 检索。

- `GET /api/functions/list`：获取当前可用工具列表与参数定义。

- `POST /api/functions/call`：同步执行指定工具调用（受权限与沙箱约束）。

# 12\. Function Calling 独立模块设计

## 12\.1 模块定位

作为 FastAPI 项目内的独立代码模块，与主业务、组件协议、RAG 链路解耦，单独维护工具注册、参数校验、执行逻辑与安全沙箱。
核心边界：只负责 “工具调用的执行与结果返回”，不参与会话编排、组件生成，由主流程统一调度。

## 12\.2 代码目录结构

所有 Function Calling 相关代码收敛至独立文件夹，结构如下：

```Plain Text
app/
├── function_calling/          # Function Calling 独立模块根目录
│   ├── __init__.py
│   ├── registry.py            # 工具注册中心，管理所有可用工具白名单
│   ├── validator.py           # 参数 Schema 校验、模型输出解析
│   ├── sandbox.py             # 执行沙箱，控制权限、超时、资源隔离
│   ├── tools/                 # 具体工具实现目录
│   │   ├── __init__.py
│   │   ├── knowledge_query.py # 知识库检索工具
│   │   ├── code_executor.py   # 代码执行工具
│   │   └── custom_tools/      # 自定义工具扩展目录
│   ├── exceptions.py          # 模块专属异常定义
│   └── schemas.py             # 工具入参/出参统一数据模型
```

## 12\.3 执行流程

1. 主流程判断用户请求需要调用工具，将模型输出的函数调用参数传入模块。

2. validator 层校验工具名称、参数格式是否匹配注册的 Schema，拦截非法请求。

3. registry 路由到对应工具实现，传入 sandbox 隔离执行。

4. 执行结果标准化后返回主流程，注入会话上下文或渲染为组件。

5. 全链路执行日志写入审计表，支持回溯与问题排查。

## 12\.4 与组件协议的联动

组件协议的 `actions` 字段新增 `function_call` 类型，支持前端点击组件直接触发工具调用：

```json
{
  "actions": [
    {
      "type": "function_call",
      "function_name": "knowledge_query",
      "params": {
        "query": "登录流程安全规范"
      },
      "target_id": "node_123"
    }
  ]
}
```

调用结果将以新版本形式更新到对应 ui\_node 中，完整保留版本历史。

## 12\.5 安全约束

- 所有工具必须在 registry 白名单注册，禁止动态执行未注册函数。

- 工具入参强制 Schema 校验，拒绝参数注入与非法格式。

- 代码执行类工具运行在隔离沙箱中，限制网络访问、文件系统权限与执行时长。

- 工具执行受用户权限控制，敏感工具仅管理员角色可用。

# 13\. 结论

这个方案的核心不是 “AI 生成 HTML”，而是 “AI 生成可控的交互协议”。本次优化后进一步实现：

1. 向量存储层可插拔，支持 pgvector 轻量化部署与 Qdrant 高性能部署平滑切换，降低初始部署门槛与运维成本。

2. Function Calling 独立模块化，职责清晰、易扩展、易维护，同时通过沙箱机制保障工具执行安全。

整体方案同时满足：响应快、token 可控、交互丰富、易扩展、可版本化、可回滚、部署灵活。

> （注：部分内容可能由 AI 生成）
