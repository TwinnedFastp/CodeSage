"""前端UI绘制技能 - 让AI能够直接生成精美的前端页面"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class UiSkillResult(BaseModel):
    """UI技能执行结果"""
    success: bool = True
    html: str = ""
    css: str = ""
    js: str = ""
    message: str = ""


class ColorScheme(BaseModel):
    """颜色方案配置"""
    primary: str = "#3B82F6"
    secondary: str = "#6366F1"
    accent: str = "#F59E0B"
    success: str = "#22C55E"
    warning: str = "#F59E0B"
    danger: str = "#EF4444"
    background: str = "#FFFFFF"
    surface: str = "#FAFAFA"
    text: str = "#111111"
    textSecondary: str = "#666666"


class TypographyConfig(BaseModel):
    """排版配置"""
    fontFamily: str = "Inter, -apple-system, BlinkMacSystemFont, sans-serif"
    fontSize: str = "16px"
    lineHeight: str = "1.6"
    headingWeight: int = 700
    bodyWeight: int = 400


class PaddingConfig(BaseModel):
    """内边距配置"""
    xs: str = "4px"
    sm: str = "8px"
    md: str = "16px"
    lg: str = "24px"
    xl: str = "32px"


class BorderConfig(BaseModel):
    """边框配置"""
    radius: str = "12px"
    width: str = "1px"
    color: str = "#E5E7EB"


class UiTheme(BaseModel):
    """UI主题配置"""
    colors: ColorScheme = Field(default_factory=ColorScheme)
    typography: TypographyConfig = Field(default_factory=TypographyConfig)
    padding: PaddingConfig = Field(default_factory=PaddingConfig)
    border: BorderConfig = Field(default_factory=BorderConfig)


class ComponentSpec(BaseModel):
    """组件规格"""
    type: str
    props: Dict[str, Any] = Field(default_factory=dict)
    children: Optional[List['ComponentSpec']] = None


class PageLayout(BaseModel):
    """页面布局配置"""
    type: str = "vertical"  # vertical, horizontal, grid, card
    columns: int = 1
    gap: str = "20px"
    components: List[ComponentSpec] = Field(default_factory=list)


class UiDrawSkill:
    """前端UI绘制技能类"""

    def __init__(self):
        self.themes = {
            "modern": UiTheme(
                colors=ColorScheme(
                    primary="#6366F1",
                    secondary="#8B5CF6",
                    background="#FFFFFF",
                    surface="#F8FAFC",
                    text="#0F172A"
                )
            ),
            "dark": UiTheme(
                colors=ColorScheme(
                    primary="#818CF8",
                    secondary="#A78BFA",
                    background="#0F172A",
                    surface="#1E293B",
                    text="#F1F5F9"
                )
            ),
            "minimal": UiTheme(
                colors=ColorScheme(
                    primary="#111111",
                    secondary="#666666",
                    background="#FFFFFF",
                    surface="#FAFAFA",
                    text="#111111"
                )
            ),
            "gradient": UiTheme(
                colors=ColorScheme(
                    primary="#EC4899",
                    secondary="#8B5CF6",
                    background="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                    surface="rgba(255,255,255,0.1)"
                )
            )
        }

    def generate_html_page(
        self,
        title: str,
        description: str = "",
        theme: str = "modern",
        layout: str = "vertical",
        content_blocks: Optional[List[Dict[str, Any]]] = None
    ) -> UiSkillResult:
        """
        生成完整的HTML页面
        
        Args:
            title: 页面标题
            description: 页面描述
            theme: 主题名称 (modern/dark/minimal/gradient)
            layout: 布局类型 (vertical/horizontal/grid)
            content_blocks: 内容块列表
        
        Returns:
            包含HTML、CSS、JS的完整页面
        """
        theme_config = self.themes.get(theme, self.themes["modern"])
        
        content_html = self._generate_content_blocks(content_blocks or [], theme_config)
        page_html = self._render_page(title, description, theme_config, layout, content_html)
        
        return UiSkillResult(
            success=True,
            html=page_html,
            css="",
            js="",
            message=f"成功生成页面: {title}"
        )

    def _generate_content_blocks(
        self,
        blocks: List[Dict[str, Any]],
        theme: UiTheme
    ) -> str:
        """生成内容块HTML"""
        html_parts = []
        
        for block in blocks:
            block_type = block.get("type", "text")
            content = block.get("content", "")
            style = block.get("style", {})
            
            if block_type == "hero":
                html_parts.append(self._render_hero(block, theme))
            elif block_type == "card":
                html_parts.append(self._render_card(block, theme))
            elif block_type == "grid":
                html_parts.append(self._render_grid(block, theme))
            elif block_type == "chart":
                html_parts.append(self._render_chart(block, theme))
            elif block_type == "form":
                html_parts.append(self._render_form(block, theme))
            elif block_type == "table":
                html_parts.append(self._render_table(block, theme))
            elif block_type == "gallery":
                html_parts.append(self._render_gallery(block, theme))
            elif block_type == "timeline":
                html_parts.append(self._render_timeline(block, theme))
            elif block_type == "tabs":
                html_parts.append(self._render_tabs(block, theme))
            elif block_type == "accordion":
                html_parts.append(self._render_accordion(block, theme))
            else:
                html_parts.append(self._render_text(block, theme))
        
        return "\n".join(html_parts)

    def _render_page(
        self,
        title: str,
        description: str,
        theme: UiTheme,
        layout: str,
        content_html: str
    ) -> str:
        """渲染完整页面"""
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="description" content="{description}">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        html {{
            scroll-behavior: smooth;
        }}
        body {{
            font-family: {theme.typography.fontFamily};
            font-size: {theme.typography.fontSize};
            line-height: {theme.typography.lineHeight};
            color: {theme.colors.text};
            background: {theme.colors.background};
            min-height: 100vh;
        }}
        .page-container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: {theme.padding.lg};
        }}
        .{layout}-layout {{
            display: {'grid' if layout == 'grid' else 'flex'};
            {'grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));' if layout == 'grid' else ''}
            {'flex-direction: column;' if layout == 'vertical' else ''}
            {'flex-direction: row;' if layout == 'horizontal' else ''}
            gap: {theme.padding.md};
        }}
        h1, h2, h3, h4, h5, h6 {{
            font-weight: {theme.typography.headingWeight};
            margin-bottom: {theme.padding.sm};
        }}
        p {{
            font-weight: {theme.typography.bodyWeight};
            color: {theme.colors.textSecondary};
            margin-bottom: {theme.padding.sm};
        }}
        a {{
            color: {theme.colors.primary};
            text-decoration: none;
            transition: color 0.2s ease;
        }}
        a:hover {{
            color: {theme.colors.secondary};
        }}
        button {{
            font-family: inherit;
            cursor: pointer;
            transition: all 0.2s ease;
            border: none;
            border-radius: {theme.border.radius};
        }}
        .btn-primary {{
            background: {theme.colors.primary};
            color: white;
            padding: {theme.padding.sm} {theme.padding.md};
            font-weight: 600;
        }}
        .btn-primary:hover {{
            opacity: 0.9;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba({self._hex_to_rgb(theme.colors.primary)}, 0.3);
        }}
        .card {{
            background: {theme.colors.surface};
            border-radius: {theme.border.radius};
            padding: {theme.padding.md};
            border: {theme.border.width} solid {theme.border.color};
            transition: all 0.3s ease;
        }}
        .card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
        }}
        .grid-2 {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: {theme.padding.md};
        }}
        .grid-3 {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: {theme.padding.md};
        }}
        .grid-4 {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: {theme.padding.md};
        }}
        @media (max-width: 768px) {{
            .page-container {{
                padding: {theme.padding.md};
            }}
            .grid-2, .grid-3, .grid-4 {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="page-container">
        <div class="{layout}-layout">
            {content_html}
        </div>
    </div>
    <script>
        // 交互式功能
        document.addEventListener('DOMContentLoaded', function() {{
            // 标签页切换
            document.querySelectorAll('.tabs-header button').forEach(btn => {{
                btn.addEventListener('click', function() {{
                    const tabId = this.dataset.tab;
                    document.querySelectorAll('.tab-content').forEach(tab => {{
                        tab.style.display = 'none';
                    }});
                    document.querySelectorAll('.tabs-header button').forEach(b => {{
                        b.classList.remove('active');
                    }});
                    document.getElementById(tabId).style.display = 'block';
                    this.classList.add('active');
                }});
            }});
            
            // 手风琴展开/收起
            document.querySelectorAll('.accordion-header').forEach(header => {{
                header.addEventListener('click', function() {{
                    const content = this.nextElementSibling;
                    content.style.maxHeight = content.style.maxHeight ? null : content.scrollHeight + 'px';
                    this.classList.toggle('active');
                }});
            }});
            
            // 动画效果
            const observer = new IntersectionObserver((entries) => {{
                entries.forEach(entry => {{
                    if (entry.isIntersecting) {{
                        entry.target.style.opacity = '1';
                        entry.target.style.transform = 'translateY(0)';
                    }}
                }});
            }}, {{ threshold: 0.1 }});
            
            document.querySelectorAll('.animate-on-scroll').forEach(el => {{
                el.style.opacity = '0';
                el.style.transform = 'translateY(20px)';
                el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
                observer.observe(el);
            }});
        }});
    </script>
</body>
</html>"""

    def _render_hero(self, block: Dict[str, Any], theme: UiTheme) -> str:
        """渲染英雄区块"""
        title = block.get("title", "")
        subtitle = block.get("subtitle", "")
        description = block.get("description", "")
        cta_text = block.get("cta_text", "立即开始")
        gradient = block.get("gradient", "linear-gradient(135deg, #667eea 0%, #764ba2 100%)")
        
        return f"""
<div class="animate-on-scroll" style="background: {gradient}; border-radius: {theme.border.radius}; padding: {theme.padding.xl}; text-align: center; color: white; margin-bottom: {theme.padding.lg};">
    <h1 style="font-size: 2.5rem; margin-bottom: {theme.padding.sm}; font-weight: 700;">{title}</h1>
    <p style="font-size: 1.1rem; opacity: 0.9; margin-bottom: {theme.padding.md};">{subtitle}</p>
    <p style="opacity: 0.85; margin-bottom: {theme.padding.lg}; max-width: 600px; margin-left: auto; margin-right: auto;">{description}</p>
    <button class="btn-primary" style="background: white; color: #6366F1; font-size: 1rem; padding: 12px 24px;">{cta_text}</button>
</div>"""

    def _render_card(self, block: Dict[str, Any], theme: UiTheme) -> str:
        """渲染卡片"""
        title = block.get("title", "")
        description = block.get("description", "")
        icon = block.get("icon", "")
        color = block.get("color", theme.colors.primary)
        
        return f"""
<div class="card animate-on-scroll">
    <div style="width: 40px; height: 40px; border-radius: 10px; background: {color}20; display: flex; align-items: center; justify-content: center; margin-bottom: {theme.padding.sm};">
        <span style="color: {color}; font-size: 1.2rem;">{icon}</span>
    </div>
    <h3 style="color: {theme.colors.text}; font-size: 1.1rem;">{title}</h3>
    <p style="color: {theme.colors.textSecondary};">{description}</p>
</div>"""

    def _render_grid(self, block: Dict[str, Any], theme: UiTheme) -> str:
        """渲染网格布局"""
        columns = block.get("columns", 3)
        items = block.get("items", [])
        
        items_html = "\n".join([
            f"""<div class="card" style="padding: {theme.padding.sm}; text-align: center;">
                <div style="font-size: 2rem; margin-bottom: {theme.padding.xs};">{item.get('icon', '')}</div>
                <div style="font-size: 1.5rem; font-weight: 700; color: {theme.colors.text}; margin-bottom: {theme.padding.xs};">{item.get('value', '')}</div>
                <div style="font-size: 0.875rem; color: {theme.colors.textSecondary};">{item.get('label', '')}</div>
            </div>"""
            for item in items
        ])
        
        return f"""
<div class="grid-{columns} animate-on-scroll">
    {items_html}
</div>"""

    def _render_chart(self, block: Dict[str, Any], theme: UiTheme) -> str:
        """渲染图表占位"""
        title = block.get("title", "")
        chart_type = block.get("type", "bar")
        labels = block.get("labels", [])
        data = block.get("data", [])
        
        max_value = max(data) if data else 100
        
        bars_html = ""
        if chart_type == "bar":
            bars_html = "\n".join([
                f"""<div style="flex: 1; text-align: center;">
                    <div style="background: {theme.colors.primary}; border-radius: 4px 4px 0 0; transition: height 0.5s ease; margin-bottom: 8px; height: {((value / max_value) * 120)}px; min-height: 8px;"></div>
                    <div style="font-size: 0.75rem; color: {theme.colors.textSecondary};">{label}</div>
                </div>"""
                for label, value in zip(labels, data)
            ])
        
        return f"""
<div class="card animate-on-scroll">
    <h3 style="color: {theme.colors.text}; margin-bottom: {theme.padding.md};">{title}</h3>
    <div style="display: flex; align-items: flex-end; gap: {theme.padding.sm}; height: 150px;">
        {bars_html}
    </div>
</div>"""

    def _render_form(self, block: Dict[str, Any], theme: UiTheme) -> str:
        """渲染表单"""
        fields = block.get("fields", [])
        
        fields_html = "\n".join([
            f"""<div style="margin-bottom: {theme.padding.md};">
                <label style="display: block; margin-bottom: {theme.padding.xs}; font-weight: 500; color: {theme.colors.text};">{field.get('label', '')}</label>
                <input 
                    type="{field.get('type', 'text')}" 
                    placeholder="{field.get('placeholder', '')}"
                    style="width: 100%; padding: {theme.padding.sm} {theme.padding.md}; border: {theme.border.width} solid {theme.border.color}; border-radius: {theme.border.radius}; font-family: inherit; font-size: inherit; background: {theme.colors.background};"
                />
            </div>"""
            for field in fields
        ])
        
        return f"""
<div class="card animate-on-scroll">
    <h3 style="color: {theme.colors.text}; margin-bottom: {theme.padding.md};">{block.get('title', '表单')}</h3>
    <form style="display: flex; flex-direction: column;">
        {fields_html}
        <button type="submit" class="btn-primary" style="align-self: flex-start;">{block.get('submit_text', '提交')}</button>
    </form>
</div>"""

    def _render_table(self, block: Dict[str, Any], theme: UiTheme) -> str:
        """渲染表格"""
        headers = block.get("headers", [])
        rows = block.get("rows", [])
        
        headers_html = "".join([f"<th style='padding: {theme.padding.sm} {theme.padding.md}; text-align: left; border-bottom: {theme.border.width} solid {theme.border.color}; font-weight: 600;'>{h}</th>" for h in headers])
        rows_html = "\n".join([
            f"""<tr style="transition: background 0.2s;">
                {"".join([f"<td style='padding: {theme.padding.sm} {theme.padding.md}; border-bottom: {theme.border.width} solid #F3F4F6;'>{cell}</td>" for cell in row])}
            </tr>"""
            for row in rows
        ])
        
        return f"""
<div class="card animate-on-scroll" style="overflow-x: auto;">
    <h3 style="color: {theme.colors.text}; margin-bottom: {theme.padding.md};">{block.get('title', '数据表格')}</h3>
    <table style="width: 100%; border-collapse: collapse;">
        <thead><tr>{headers_html}</tr></thead>
        <tbody>{rows_html}</tbody>
    </table>
</div>"""

    def _render_gallery(self, block: Dict[str, Any], theme: UiTheme) -> str:
        """渲染图片画廊"""
        images = block.get("images", [])
        
        images_html = "\n".join([
            f"""<div style="position: relative; border-radius: {theme.border.radius}; overflow: hidden; aspect-ratio: 16/10;">
                <img src="{img.get('url', '')}" alt="{img.get('alt', '')}" style="width: 100%; height: 100%; object-fit: cover; transition: transform 0.3s ease;" onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'"/>
                <div style="position: absolute; bottom: 0; left: 0; right: 0; background: linear-gradient(to top, rgba(0,0,0,0.7), transparent); padding: {theme.padding.md}; color: white;">
                    <div style="font-size: 0.875rem;">{img.get('caption', '')}</div>
                </div>
            </div>"""
            for img in images
        ])
        
        return f"""
<div class="animate-on-scroll">
    <h3 style="color: {theme.colors.text}; margin-bottom: {theme.padding.md};">{block.get('title', '图片画廊')}</h3>
    <div class="grid-2">
        {images_html}
    </div>
</div>"""

    def _render_timeline(self, block: Dict[str, Any], theme: UiTheme) -> str:
        """渲染时间线"""
        items = block.get("items", [])
        
        items_html = "\n".join([
            f"""<div style="display: flex; gap: {theme.padding.md}; padding-bottom: {theme.padding.lg}; border-left: 2px solid {theme.border.color}; padding-left: {theme.padding.md}; margin-left: {theme.padding.sm};">
                <div style="width: 12px; height: 12px; border-radius: 50%; background: {theme.colors.primary}; margin-left: -7px; margin-top: 4px; flex-shrink: 0;"></div>
                <div>
                    <div style="font-weight: 600; color: {theme.colors.text}; margin-bottom: {theme.padding.xs};">{item.get('title', '')}</div>
                    <div style="font-size: 0.875rem; color: {theme.colors.textSecondary}; margin-bottom: {theme.padding.xs};">{item.get('date', '')}</div>
                    <div style="color: {theme.colors.textSecondary};">{item.get('description', '')}</div>
                </div>
            </div>"""
            for item in items
        ])
        
        return f"""
<div class="card animate-on-scroll">
    <h3 style="color: {theme.colors.text}; margin-bottom: {theme.padding.md}; padding-left: {theme.padding.sm};">{block.get('title', '时间线')}</h3>
    {items_html}
</div>"""

    def _render_tabs(self, block: Dict[str, Any], theme: UiTheme) -> str:
        """渲染标签页"""
        tabs = block.get("tabs", [])
        active_tab = block.get("active", 0)
        
        tabs_html = "\n".join([
            f"""<button 
                data-tab="tab-{i}"
                style="padding: {theme.padding.sm} {theme.padding.md}; border: none; background: transparent; font-weight: 500; color: {theme.colors.textSecondary}; border-bottom: 2px solid transparent; transition: all 0.2s; {'color: ' + theme.colors.primary + '; border-bottom-color: ' + theme.colors.primary + ';' if i == active_tab else ''}"
            >{tab.get('label', '')}</button>"""
            for i, tab in enumerate(tabs)
        ])
        
        content_html = "\n".join([
            f"""<div id="tab-{i}" class="tab-content" style="display: {'block' if i == active_tab else 'none'}; padding-top: {theme.padding.md}; color: {theme.colors.textSecondary};">{tab.get('content', '')}</div>"""
            for i, tab in enumerate(tabs)
        ])
        
        return f"""
<div class="card animate-on-scroll">
    <div class="tabs-header" style="display: flex; gap: {theme.padding.sm}; border-bottom: {theme.border.width} solid {theme.border.color};">
        {tabs_html}
    </div>
    {content_html}
</div>"""

    def _render_accordion(self, block: Dict[str, Any], theme: UiTheme) -> str:
        """渲染手风琴"""
        items = block.get("items", [])
        
        items_html = "\n".join([
            f"""<div style="border-bottom: {theme.border.width} solid {theme.border.color}; last-child: border-bottom: none;">
                <div class="accordion-header" style="padding: {theme.padding.md}; cursor: pointer; display: flex; justify-content: space-between; align-items: center; font-weight: 500; color: {theme.colors.text};">
                    {item.get('title', '')}
                    <span style="transition: transform 0.2s;">{item.get('open', False) ? '−' : '+'}</span>
                </div>
                <div class="accordion-content" style="padding: 0 {theme.padding.md}; max-height: {item.get('open', False) ? '1000px' : '0'}; overflow: hidden; transition: max-height 0.3s ease;">
                    <p style="padding: {theme.padding.md} 0; color: {theme.colors.textSecondary};">{item.get('content', '')}</p>
                </div>
            </div>"""
            for item in items
        ])
        
        return f"""
<div class="card animate-on-scroll">
    <h3 style="color: {theme.colors.text}; margin-bottom: {theme.padding.md}; padding: 0 {theme.padding.md};">{block.get('title', '常见问题')}</h3>
    {items_html}
</div>"""

    def _render_text(self, block: Dict[str, Any], theme: UiTheme) -> str:
        """渲染文本块"""
        content = block.get("content", "")
        text_type = block.get("text_type", "paragraph")
        alignment = block.get("alignment", "left")
        
        if text_type == "heading":
            return f"<h2 style='color: {theme.colors.text}; text-align: {alignment};'>{content}</h2>"
        elif text_type == "quote":
            return f"""
<div style="border-left: 4px solid {theme.colors.primary}; padding-left: {theme.padding.md}; font-style: italic; color: {theme.colors.textSecondary}; margin: {theme.padding.md} 0;">{content}</div>"""
        else:
            return f"<p style='text-align: {alignment}; color: {theme.colors.textSecondary};'>{content}</p>"

    def _hex_to_rgb(self, hex_color: str) -> str:
        """将十六进制颜色转换为RGB"""
        hex_color = hex_color.lstrip('#')
        return f"{int(hex_color[0:2], 16)}, {int(hex_color[2:4], 16)}, {int(hex_color[4:6], 16)}"

    def generate_landing_page(self, title: str, features: List[Dict[str, Any]]) -> UiSkillResult:
        """
        生成着陆页
        
        Args:
            title: 页面标题
            features: 功能特性列表
        
        Returns:
            完整的着陆页HTML
        """
        blocks = [
            {
                "type": "hero",
                "title": title,
                "subtitle": "创新解决方案，赋能您的业务",
                "description": "基于先进技术，为您提供专业的产品和服务。让我们一起开创美好未来。",
                "cta_text": "立即体验"
            },
            {
                "type": "grid",
                "columns": 3,
                "items": features
            },
            {
                "type": "text",
                "text_type": "heading",
                "content": "为什么选择我们",
                "alignment": "center"
            },
            {
                "type": "text",
                "content": "我们致力于提供最优质的服务，帮助企业实现数字化转型，提升竞争力。",
                "alignment": "center"
            }
        ]
        
        return self.generate_html_page(
            title=title,
            description="专业的解决方案提供商",
            theme="modern",
            layout="vertical",
            content_blocks=blocks
        )

    def generate_dashboard(self, title: str, stats: List[Dict[str, Any]], charts: List[Dict[str, Any]]) -> UiSkillResult:
        """
        生成数据仪表盘
        
        Args:
            title: 仪表盘标题
            stats: 统计数据列表
            charts: 图表数据列表
        
        Returns:
            完整的仪表盘HTML
        """
        blocks = [
            {
                "type": "grid",
                "columns": 4,
                "items": stats
            }
        ]
        
        for chart in charts:
            blocks.append({
                "type": "chart",
                "title": chart.get("title", ""),
                "type": chart.get("type", "bar"),
                "labels": chart.get("labels", []),
                "data": chart.get("data", [])
            })
        
        return self.generate_html_page(
            title=title,
            description="数据可视化仪表盘",
            theme="dark",
            layout="vertical",
            content_blocks=blocks
        )

    def generate_portfolio(self, title: str, projects: List[Dict[str, Any]]) -> UiSkillResult:
        """
        生成作品集页面
        
        Args:
            title: 页面标题
            projects: 项目列表
        
        Returns:
            完整的作品集HTML
        """
        blocks = [
            {
                "type": "hero",
                "title": title,
                "subtitle": "探索我们的精选作品",
                "description": "每一个项目都是我们用心打造的艺术品",
                "gradient": "linear-gradient(135deg, #EC4899 0%, #8B5CF6 100%)"
            },
            {
                "type": "gallery",
                "title": "项目展示",
                "images": projects
            }
        ]
        
        return self.generate_html_page(
            title=title,
            description="创意作品集",
            theme="gradient",
            layout="vertical",
            content_blocks=blocks
        )
