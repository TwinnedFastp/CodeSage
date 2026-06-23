"""
组件协议 (ComponentProtocol) Pydantic 模型与白名单校验。

模型输出该协议 JSON 后，由后端解析为 ComponentProtocol，
再由前端按 components 顺序渲染对应白名单组件。
"""

import json
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


# 前端白名单组件类型
ALLOWED_COMPONENT_TYPES = {
    "summary_card",
    "text_block",
    "flowchart",
    "list",
    "code",
    "quote",
    "table",
    "webpage",
    "chart",
    "timeline",
    "tabs",
    "accordion",
    "stat",
    "steps",
    "compare",
    "gallery",
}

# 允许的 action 类型
ALLOWED_ACTION_TYPES = {"regenerate", "expand", "function_call", "open_webpage"}


class ComponentAction(BaseModel):
    """组件交互行为。"""

    type: Literal["regenerate", "expand", "function_call", "open_webpage"]
    target_id: Optional[str] = None
    function_name: Optional[str] = None
    params: Optional[dict[str, Any]] = None


class Component(BaseModel):
    """单个渲染组件。"""

    type: str
    props: dict[str, Any] = Field(default_factory=dict)
    id: Optional[str] = None  # 可选，前端用于定位


class ComponentProtocol(BaseModel):
    """模型 → 前端的界面协议根对象。"""

    page_type: str = "analysis"
    title: str = ""
    components: list[Component] = Field(default_factory=list)
    actions: list[ComponentAction] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)


def validate_component_protocol(data: dict | None) -> ComponentProtocol:
    """对模型输出做白名单校验，返回 ComponentProtocol 实例。"""
    if data is None or not isinstance(data, dict):
        raise ValueError("组件协议数据为空或不是字典对象")

    components = data.get("components")
    if components is None:
        raise ValueError("组件协议缺少 components 字段")
    if not isinstance(components, list):
        raise ValueError("components 必须是数组")

    for idx, comp in enumerate(components):
        if not isinstance(comp, dict):
            raise ValueError(f"components[{idx}] 不是对象")
        comp_type = comp.get("type")
        if comp_type not in ALLOWED_COMPONENT_TYPES:
            raise ValueError(
                f"components[{idx}] 的 type '{comp_type}' 不在白名单内，"
                f"允许值：{sorted(ALLOWED_COMPONENT_TYPES)}"
            )

    actions = data.get("actions") or []
    if not isinstance(actions, list):
        raise ValueError("actions 必须是数组")
    for idx, act in enumerate(actions):
        if not isinstance(act, dict):
            raise ValueError(f"actions[{idx}] 不是对象")
        act_type = act.get("type")
        if act_type not in ALLOWED_ACTION_TYPES:
            raise ValueError(
                f"actions[{idx}] 的 type '{act_type}' 不在白名单内，"
                f"允许值：{sorted(ALLOWED_ACTION_TYPES)}"
            )
        if act_type == "function_call" and not act.get("function_name"):
            raise ValueError(f"actions[{idx}] 为 function_call 时必须提供 function_name")

    return ComponentProtocol(**data)


def component_protocol_from_text(raw: str) -> ComponentProtocol:
    """从模型原始文本输出解析出 ComponentProtocol。"""
    text = raw.strip()

    # 去除 markdown 代码块包裹
    if text.startswith("```"):
        # 形如 ```json ... ``` 或 ``` ... ```
        first_newline = text.find("\n")
        if first_newline != -1:
            text = text[first_newline + 1:]
        else:
            text = text[3:]
        text = text.rstrip()
        if text.endswith("```"):
            text = text[:-3].rstrip()
        text = text.strip()

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError(f"模型未输出有效 JSON：{raw[:120]}")

    try:
        parsed = json.loads(text[start:end + 1])
    except json.JSONDecodeError as e:
        raise ValueError(f"模型未输出有效 JSON：{e}") from e

    return validate_component_protocol(parsed)
