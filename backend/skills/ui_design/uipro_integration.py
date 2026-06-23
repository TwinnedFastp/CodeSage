"""UI/UX Pro Max 技能集成层 - 让AI能够调用专业设计能力"""
from __future__ import annotations

import subprocess
import json
from pathlib import Path
from typing import Any, Dict, Optional

from backend.function_calling.registry import default_registry
from backend.function_calling.schemas import ToolMetadata, ToolParamField

# 获取技能目录路径
SKILL_DIR = Path(__file__).parent.parent.parent / ".trae" / "skills" / "ui-ux-pro-max"


async def generate_design_system(params: dict, context: dict) -> dict:
    """
    生成完整的设计系统配置
    
    Args:
        params:
            query: 搜索关键词（产品类型、行业、风格关键词）
            project_name: 项目名称（可选）
            persist: 是否持久化设计系统（可选）
    
    Returns:
        包含设计系统配置的结果
    """
    try:
        query = params.get("query", "")
        project_name = params.get("project_name", "")
        
        cmd = ["python", str(SKILL_DIR / "scripts" / "search.py"), query, "--design-system"]
        
        if project_name:
            cmd.extend(["-p", project_name])
        
        if params.get("persist", False):
            cmd.append("--persist")
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=SKILL_DIR.parent.parent)
        
        if result.returncode == 0:
            return {
                "success": True,
                "design_system": result.stdout,
                "message": "设计系统生成成功"
            }
        else:
            return {
                "success": False,
                "error": result.stderr,
                "message": "设计系统生成失败"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "调用设计系统生成器时出错"
        }


async def search_design_guidelines(params: dict, context: dict) -> dict:
    """
    搜索设计指南
    
    Args:
        params:
            query: 搜索关键词
            domain: 搜索领域（style/color/typography/chart/landing/ux等）
            max_results: 最大结果数（可选，默认3）
    
    Returns:
        搜索结果列表
    """
    try:
        query = params.get("query", "")
        domain = params.get("domain", "")
        max_results = params.get("max_results", 3)
        
        cmd = ["python", str(SKILL_DIR / "scripts" / "search.py"), query]
        
        if domain:
            cmd.extend(["--domain", domain])
        
        cmd.extend(["-n", str(max_results)])
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=SKILL_DIR.parent.parent)
        
        if result.returncode == 0:
            return {
                "success": True,
                "results": result.stdout,
                "message": "搜索成功"
            }
        else:
            return {
                "success": False,
                "error": result.stderr,
                "message": "搜索失败"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "调用搜索功能时出错"
        }


async def get_stack_guidelines(params: dict, context: dict) -> dict:
    """
    获取技术栈特定的最佳实践指南
    
    Args:
        params:
            query: 搜索关键词
            stack: 技术栈（html-tailwind/react/nextjs/vue/svelte等）
    
    Returns:
        技术栈相关的最佳实践指南
    """
    try:
        query = params.get("query", "")
        stack = params.get("stack", "html-tailwind")
        
        cmd = ["python", str(SKILL_DIR / "scripts" / "search.py"), query, "--stack", stack]
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=SKILL_DIR.parent.parent)
        
        if result.returncode == 0:
            return {
                "success": True,
                "guidelines": result.stdout,
                "message": "获取指南成功"
            }
        else:
            return {
                "success": False,
                "error": result.stderr,
                "message": "获取指南失败"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "调用技术栈指南时出错"
        }


async def draw_beautiful_page(params: dict, context: dict) -> dict:
    """
    生成精美的前端页面（集成UI/UX Pro Max设计能力）
    
    Args:
        params:
            title: 页面标题
            type: 页面类型（landing/dashboard/portfolio/form等）
            style: 设计风格（minimal/professional/elegant/modern/dark等）
            industry: 行业类型（saas/ecommerce/healthcare/fintech等）
            features: 功能特性列表（可选）
    
    Returns:
        完整的HTML页面代码
    """
    try:
        title = params.get("title", "未命名页面")
        page_type = params.get("type", "landing")
        style = params.get("style", "modern")
        industry = params.get("industry", "saas")
        
        design_query = f"{page_type} {industry} {style}"
        
        design_cmd = ["python", str(SKILL_DIR / "scripts" / "search.py"), design_query, "--design-system", "-f", "markdown"]
        design_result = subprocess.run(design_cmd, capture_output=True, text=True, cwd=SKILL_DIR.parent.parent)
        
        if design_result.returncode != 0:
            return {
                "success": False,
                "error": design_result.stderr,
                "message": "设计系统生成失败"
            }
        
        design_system = design_result.stdout
        
        features = params.get("features", [])
        
        page_html = generate_page_from_design(title, page_type, style, design_system, features)
        
        return {
            "success": True,
            "html": page_html,
            "design_system": design_system,
            "message": "页面生成成功"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "生成页面时出错"
        }


def generate_page_from_design(title: str, page_type: str, style: str, design_system: str, features: list) -> str:
    """根据设计系统生成页面HTML"""
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary-color: #6366F1;
            --secondary-color: #8B5CF6;
            --bg-color: #FFFFFF;
            --surface-color: #FAFAFA;
            --text-color: #111111;
            --text-secondary: #666666;
            --border-color: #E5E7EB;
            --radius: 12px;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-color);
            color: var(--text-color);
            line-height: 1.6;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 24px;
        }}
        
        /* Hero Section */
        .hero {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 80px 0;
            text-align: center;
        }}
        
        .hero h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 16px;
            letter-spacing: -0.5px;
        }}
        
        .hero p {{
            font-size: 1.1rem;
            opacity: 0.9;
            margin-bottom: 24px;
            max-width: 600px;
            margin-left: auto;
            margin-right: auto;
        }}
        
        .btn {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 12px 24px;
            border-radius: var(--radius);
            font-weight: 600;
            transition: all 0.2s ease;
            cursor: pointer;
            border: none;
            font-family: inherit;
        }}
        
        .btn-primary {{
            background: white;
            color: #6366F1;
        }}
        
        .btn-primary:hover {{
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        
        .btn-secondary {{
            background: transparent;
            color: white;
            border: 2px solid rgba(255,255,255,0.3);
        }}
        
        .btn-secondary:hover {{
            background: rgba(255,255,255,0.1);
        }}
        
        /* Features Section */
        .features {{
            padding: 80px 0;
        }}
        
        .features h2 {{
            text-align: center;
            font-size: 2rem;
            margin-bottom: 16px;
        }}
        
        .features p {{
            text-align: center;
            color: var(--text-secondary);
            margin-bottom: 48px;
        }}
        
        .features-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 24px;
        }}
        
        .feature-card {{
            background: white;
            border-radius: var(--radius);
            padding: 28px;
            border: 1px solid var(--border-color);
            transition: all 0.3s ease;
        }}
        
        .feature-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 8px 24px rgba(0,0,0,0.08);
            border-color: var(--primary-color);
        }}
        
        .feature-icon {{
            width: 48px;
            height: 48px;
            border-radius: 12px;
            background: var(--surface-color);
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 16px;
            font-size: 1.5rem;
        }}
        
        .feature-card h3 {{
            margin-bottom: 8px;
            font-size: 1.1rem;
        }}
        
        .feature-card p {{
            text-align: left;
            margin-bottom: 0;
            font-size: 0.9rem;
        }}
        
        /* Stats Section */
        .stats {{
            background: var(--surface-color);
            padding: 60px 0;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 32px;
        }}
        
        .stat-item {{
            text-align: center;
        }}
        
        .stat-value {{
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--primary-color);
            margin-bottom: 4px;
        }}
        
        .stat-label {{
            color: var(--text-secondary);
            font-size: 0.9rem;
        }}
        
        /* CTA Section */
        .cta {{
            padding: 80px 0;
            text-align: center;
        }}
        
        .cta-card {{
            background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
            color: white;
            padding: 60px;
            border-radius: 20px;
        }}
        
        .cta-card h2 {{
            font-size: 1.8rem;
            margin-bottom: 12px;
        }}
        
        .cta-card p {{
            opacity: 0.9;
            margin-bottom: 24px;
        }}
        
        /* Footer */
        .footer {{
            background: #111;
            color: #999;
            padding: 40px 0;
            text-align: center;
            font-size: 0.875rem;
        }}
        
        @media (max-width: 768px) {{
            .hero h1 {{
                font-size: 1.8rem;
            }}
            
            .features-grid {{
                grid-template-columns: 1fr;
            }}
            
            .cta-card {{
                padding: 40px 24px;
            }}
        }}
    </style>
</head>
<body>
    <!-- Hero Section -->
    <section class="hero">
        <div class="container">
            <h1>{title}</h1>
            <p>创新解决方案，为您的业务赋能</p>
            <div>
                <button class="btn btn-primary">立即开始</button>
                <button class="btn btn-secondary">了解更多</button>
            </div>
        </div>
    </section>

    <!-- Features Section -->
    <section class="features">
        <div class="container">
            <h2>核心功能</h2>
            <p>为您提供全方位的专业服务</p>
            <div class="features-grid">
                {generate_feature_cards(features)}
            </div>
        </div>
    </section>

    <!-- Stats Section -->
    <section class="stats">
        <div class="container">
            <div class="stats-grid">
                <div class="stat-item"><div class="stat-value">10K+</div><div class="stat-label">活跃用户</div></div>
                <div class="stat-item"><div class="stat-value">99.9%</div><div class="stat-label">服务可用性</div></div>
                <div class="stat-item"><div class="stat-value">50+</div><div class="stat-label">合作伙伴</div></div>
                <div class="stat-item"><div class="stat-value">24/7</div><div class="stat-label">技术支持</div></div>
            </div>
        </div>
    </section>

    <!-- CTA Section -->
    <section class="cta">
        <div class="container">
            <div class="cta-card">
                <h2>准备好开始了吗？</h2>
                <p>加入我们，体验专业的服务</p>
                <button class="btn btn-primary">免费试用</button>
            </div>
        </div>
    </section>

    <!-- Footer -->
    <footer class="footer">
        <div class="container">
            <p>&copy; 2024 {title}. All rights reserved.</p>
        </div>
    </footer>
</body>
</html>"""


def generate_feature_cards(features: list) -> str:
    """生成功能卡片HTML"""
    icons = ["🚀", "🎯", "🔒", "⚡", "📊", "💡"]
    cards = []
    
    for i, feature in enumerate(features[:6]):
        icon = icons[i % len(icons)]
        title = feature.get("title", f"功能 {i+1}")
        desc = feature.get("description", "详细描述")
        
        cards.append(f"""
<div class="feature-card">
    <div class="feature-icon">{icon}</div>
    <h3>{title}</h3>
    <p>{desc}</p>
</div>""")
    
    return "\n".join(cards)


# 注册工具到函数调用系统
default_registry.register(
    ToolMetadata(
        name="generate_design_system",
        description="生成完整的UI设计系统配置，包括颜色方案、字体搭配、样式指南、交互规则等。基于搜索查询自动推荐最佳设计方案。",
        params=[
            ToolParamField(
                name="query",
                type="string",
                required=True,
                description="搜索关键词，包含产品类型、行业、风格关键词（如：saas dashboard modern）"
            ),
            ToolParamField(
                name="project_name",
                type="string",
                required=False,
                description="项目名称，用于持久化设计系统"
            ),
            ToolParamField(
                name="persist",
                type="bool",
                required=False,
                description="是否将设计系统持久化到文件"
            )
        ]
    ),
    generate_design_system
)

default_registry.register(
    ToolMetadata(
        name="search_design_guidelines",
        description="搜索UI/UX设计指南数据库，获取特定领域的设计建议和最佳实践。",
        params=[
            ToolParamField(
                name="query",
                type="string",
                required=True,
                description="搜索关键词"
            ),
            ToolParamField(
                name="domain",
                type="string",
                required=False,
                description="搜索领域：style/color/typography/chart/landing/ux/icons/react/web"
            ),
            ToolParamField(
                name="max_results",
                type="int",
                required=False,
                description="最大返回结果数（默认3）"
            )
        ]
    ),
    search_design_guidelines
)

default_registry.register(
    ToolMetadata(
        name="get_stack_guidelines",
        description="获取特定技术栈的前端开发最佳实践指南。",
        params=[
            ToolParamField(
                name="query",
                type="string",
                required=True,
                description="搜索关键词"
            ),
            ToolParamField(
                name="stack",
                type="string",
                required=False,
                description="技术栈：html-tailwind/react/nextjs/vue/svelte/flutter/react-native/swiftui/shadcn"
            )
        ]
    ),
    get_stack_guidelines
)

default_registry.register(
    ToolMetadata(
        name="draw_beautiful_page",
        description="生成精美的前端页面，集成UI/UX Pro Max设计能力。自动根据产品类型和风格生成专业的HTML页面。",
        params=[
            ToolParamField(
                name="title",
                type="string",
                required=True,
                description="页面标题"
            ),
            ToolParamField(
                name="type",
                type="string",
                required=False,
                description="页面类型：landing/dashboard/portfolio/form/about"
            ),
            ToolParamField(
                name="style",
                type="string",
                required=False,
                description="设计风格：minimal/professional/elegant/modern/dark/gradient"
            ),
            ToolParamField(
                name="industry",
                type="string",
                required=False,
                description="行业类型：saas/ecommerce/healthcare/fintech/gaming/education"
            ),
            ToolParamField(
                name="features",
                type="array",
                required=False,
                description="功能特性列表，每个对象包含title和description"
            )
        ]
    ),
    draw_beautiful_page
)