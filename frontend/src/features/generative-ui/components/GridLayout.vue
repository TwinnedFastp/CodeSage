<script setup lang="ts">
import { computed } from 'vue'
import { componentRegistry } from '../componentRegistry'
import UnknownBlock from './UnknownBlock.vue'

const props = defineProps<{
  props: {
    columns?: number
    gap?: string
    children?: Array<{
      id?: string
      type: string
      props: Record<string, any>
    }>
  }
}>()

const gridStyle = computed(() => ({
  display: 'grid',
  gridTemplateColumns: `repeat(${props.props.columns || 2}, 1fr)`,
  gap: props.props.gap || '16px'
}))
</script>

<template>
  <div :style="gridStyle" class="w-full">
    <template v-for="(child, i) in props.children" :key="child.id || child.type + '_' + i">
      <div v-if="componentRegistry[child.type]">
        <component
          :is="componentRegistry[child.type]"
          :props="child.props"
        />
      </div>
      <UnknownBlock v-else :props="child.props" :type="child.type" />
    </template>
  </div>
</template>