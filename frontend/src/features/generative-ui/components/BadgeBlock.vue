<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  props: {
    label: string
    type?: 'primary' | 'success' | 'warning' | 'danger' | 'info'
    size?: 'small' | 'medium'
    variant?: 'default' | 'outline' | 'dot'
  }
}>()

const badgeStyle = computed(() => {
  const baseStyle = {
    display: 'inline-flex',
    alignItems: 'center',
    padding: props.props.size === 'small' ? '2px 8px' : '4px 12px',
    borderRadius: '9999px',
    fontSize: props.props.size === 'small' ? '11px' : '12px',
    fontWeight: 500,
    whiteSpace: 'nowrap' as const
  }

  const typeStyles: Record<string, Record<string, string>> = {
    primary: {
      default: 'background: #E8E6E1; color: #111;',
      outline: 'border: 1px solid #111; color: #111; background: transparent;',
      dot: 'background: #111; width: 8px; height: 8px; padding: 0; border-radius: 50%;'
    },
    success: {
      default: 'background: #DCFCE7; color: #166534;',
      outline: 'border: 1px solid #16A34A; color: #166534; background: transparent;',
      dot: 'background: #22C55E; width: 8px; height: 8px; padding: 0; border-radius: 50%;'
    },
    warning: {
      default: 'background: #FEF3C7; color: #92400E;',
      outline: 'border: 1px solid #F59E0B; color: #92400E; background: transparent;',
      dot: 'background: #F59E0B; width: 8px; height: 8px; padding: 0; border-radius: 50%;'
    },
    danger: {
      default: 'background: #FEE2E2; color: #991B1B;',
      outline: 'border: 1px solid #EF4444; color: #991B1B; background: transparent;',
      dot: 'background: #EF4444; width: 8px; height: 8px; padding: 0; border-radius: 50%;'
    },
    info: {
      default: 'background: #DBEAFE; color: #1E40AF;',
      outline: 'border: 1px solid #3B82F6; color: #1E40AF; background: transparent;',
      dot: 'background: #3B82F6; width: 8px; height: 8px; padding: 0; border-radius: 50%;'
    }
  }

  const type = props.props.type || 'primary'
  const variant = props.props.variant || 'default'

  return {
    ...baseStyle,
    ...(typeStyles[type]?.[variant] || typeStyles.primary.default)
  }
})
</script>

<template>
  <span :style="badgeStyle" class="transition-all duration-200">
    {{ props.variant !== 'dot' ? props.label : '' }}
  </span>
</template>