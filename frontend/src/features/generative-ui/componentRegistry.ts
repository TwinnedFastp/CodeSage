import type { Component } from './types'
import SummaryCard from './components/SummaryCard.vue'
import TextBlock from './components/TextBlock.vue'
import Flowchart from './components/Flowchart.vue'
import ListBlock from './components/ListBlock.vue'
import CodeBlock from './components/CodeBlock.vue'
import QuoteBlock from './components/QuoteBlock.vue'
import TableBlock from './components/TableBlock.vue'
import UnknownBlock from './components/UnknownBlock.vue'

export const componentRegistry: Record<string, any> = {
  summary_card: SummaryCard,
  text_block: TextBlock,
  flowchart: Flowchart,
  list: ListBlock,
  code: CodeBlock,
  quote: QuoteBlock,
  table: TableBlock,
}

export const ALLOWED_TYPES = Object.keys(componentRegistry)

export function isAllowed(type: string): boolean {
  return type in componentRegistry
}

export function componentFor(c: Component): any {
  return componentRegistry[c.type] || UnknownBlock
}
