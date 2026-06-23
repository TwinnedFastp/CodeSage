"""UI设计技能包 - 集成专业UI/UX设计能力"""
from __future__ import annotations

# 导入核心技能类
from .skill import UiDrawSkill, UiSkillResult, UiTheme

# 导入UI/UX Pro Max集成
from .uipro_integration import (
    generate_design_system,
    search_design_guidelines,
    get_stack_guidelines,
    draw_beautiful_page
)

# 自动注册工具（导入时自动执行）
from . import uipro_integration

__all__ = [
    'UiDrawSkill',
    'UiSkillResult',
    'UiTheme',
    'generate_design_system',
    'search_design_guidelines',
    'get_stack_guidelines',
    'draw_beautiful_page'
]