# 会话归档功能设计

## 1. 目标与范围

为 CodeSage 增加会话归档能力，让用户能把不常用但又不想删除的会话移出主列表，需要时进入“已归档”视图找回或取消归档。

## 2. 数据模型

在 `chat_sessions` 表新增两列：

- `is_archived` BOOLEAN NOT NULL DEFAULT FALSE
- `archived_at` TIMESTAMP WITH TIME ZONE（可空）

归档时设置 `is_archived = TRUE, archived_at = NOW()`；取消归档时设置 `is_archived = FALSE, archived_at = NULL`。

## 3. 后端 API

- `GET /api/v1/conversations/sessions?archived=true|false`
  - 默认 `false`（与现有行为一致）
  - `true` 时仅返回已归档会话
  - 不区分时按时间倒序返回所有（保持测试兼容）
- `POST /api/v1/conversations/sessions/{id}/archive` → 归档
- `POST /api/v1/conversations/sessions/{id}/unarchive` → 取消归档
- 同时允许通过 `PATCH /api/v1/conversations/sessions/{id}` 传入 `is_archived` 完成切换

## 4. 前端 UX 方案

沿用项目现有温暖、低饱和的“米色纸面”风格（米白底 #F3F2EE、炭黑字 #111111、暖灰线 #E8E6E1）。

- 侧边栏顶部导航由 3 格改为 4 格，新增“归档”入口（可折叠态仅显示图标）。
- 会话列表项 hover 时右侧显示：
  - 活跃会话：归档按钮
  - 已归档会话：取消归档按钮 + 删除按钮
- 归档视图底部提供“返回活跃会话”按钮。
- 列表项标题保持原有内联编辑和双击编辑能力。
- 当前会话若为已归档，主区域标题旁显示“已归档”小标签，并保留删除按钮。

## 5. 交互状态

- 归档操作即时更新本地状态，使用 toast 提示“已归档”。
- 取消归档后返回活跃列表，并选中该会话。
- 删除已归档会话后留在归档视图。

## 6. 验收标准

- 默认列表只展示未归档会话。
- 已归档会话不出现在主列表。
- 可在归档列表查看历史并取消归档。
- 后端通过新增/修改列保持迁移兼容，旧数据不受影响。
- 后端测试覆盖归档/取消归档与列表过滤。
- TypeScript 类型完整，前端无报错。
