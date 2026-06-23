/**
 * 组件注册表 — 控制 LLM 生成协议到前端组件的映射。
 *
 * 设计原则：
 * - LLM 只负责决定"展示什么"（type + props）
 * - 前端负责决定"怎么展示"（组件实现）
 * - 核心组件同步加载（首屏必需），冷门/大组件异步按需加载
 *
 * 注册表分层：
 * - 同步核心组件：基础展示类 + 常用交互类（6 个，首屏不加载体积大的）
 * - 异步组件：图表/ECharts、画廊等大体积组件（用 defineAsyncComponent 懒加载）
 */
import { defineAsyncComponent, type Component as VueComponent } from 'vue'

// ===== 核心同步组件（首屏即时可用） =====
import SummaryCard from './components/SummaryCard.vue'
import TextBlock from './components/TextBlock.vue'
import ListBlock from './components/ListBlock.vue'
import QuoteBlock from './components/QuoteBlock.vue'
import CodeBlock from './components/CodeBlock.vue'
import TableBlock from './components/TableBlock.vue'
import Flowchart from './components/Flowchart.vue'
import WebPageBlock from './components/WebPageBlock.vue'
import StepsBlock from './components/StepsBlock.vue'
import CompareBlock from './components/CompareBlock.vue'
import TimelineBlock from './components/TimelineBlock.vue'
import TabBlock from './components/TabBlock.vue'
import AccordionBlock from './components/AccordionBlock.vue'
import StatBlock from './components/StatBlock.vue'
// 新增高级组件
import FormBlock from './components/FormBlock.vue'
import ButtonBlock from './components/ButtonBlock.vue'
import GridLayout from './components/GridLayout.vue'
import HeroSection from './components/HeroSection.vue'
import BadgeBlock from './components/BadgeBlock.vue'
import ProgressBlock from './components/ProgressBlock.vue'

// ===== 异步组件（大体积 / 冷门，按需加载） =====
// ChartBlock 引入 ECharts（~900KB），GalleryBlock 引入 el-image-viewer
const AsyncChartBlock = defineAsyncComponent(() => import('./components/ChartBlock.vue'))
const AsyncGalleryBlock = defineAsyncComponent(() => import('./components/GalleryBlock.vue'))

// ===== 注册表 =====
export const componentRegistry: Record<string, VueComponent> = {
  // 核心展示类（同步）
  summary_card: SummaryCard,
  text_block: TextBlock,
  list: ListBlock,
  quote: QuoteBlock,
  code: CodeBlock,
  table: TableBlock,
  flowchart: Flowchart,
  // 交互类（同步，ElementPlus 基础组件体积小）
  webpage: WebPageBlock,
  tabs: TabBlock,
  accordion: AccordionBlock,
  steps: StepsBlock,
  compare: CompareBlock,
  timeline: TimelineBlock,
  stat: StatBlock,
  // 新增高级组件（同步）
  form: FormBlock,
  button: ButtonBlock,
  grid_layout: GridLayout,
  hero_section: HeroSection,
  badge: BadgeBlock,
  progress: ProgressBlock,
  // 大体积组件（异步懒加载）
  chart: AsyncChartBlock,
  gallery: AsyncGalleryBlock,
}

/**
 * 标记哪些组件是异步加载的（用于 loading 占位处理）
 */
export const ASYNC_COMPONENTS = new Set(['chart', 'gallery'])

/**
 * 组件加载状态：包含异步组件的 Pending/Resolved/Rejected 状态
 */
export const asyncComponentLoadState = new Map<string, 'pending' | 'loaded' | 'error'>()
for (const key of ASYNC_COMPONENTS) {
  asyncComponentLoadState.set(key, 'pending')
}

export const ALLOWED_TYPES = Object.keys(componentRegistry)

export function isAllowed(type: string): boolean {
  return type in componentRegistry
}

export function componentFor(type: string): VueComponent | null {
  return componentRegistry[type] || null
}

export function isAsyncComponent(type: string): boolean {
  return ASYNC_COMPONENTS.has(type)
}
