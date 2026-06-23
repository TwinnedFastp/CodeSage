<script setup lang="ts">
import { computed } from 'vue'
import { ExternalLink } from '@element-plus/icons-vue'

const props = defineProps<{
  props: {
    text?: string
    type?: 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'default'
    size?: 'small' | 'medium' | 'large'
    href?: string
    target?: '_blank' | '_self'
    disabled?: boolean
    loading?: boolean
    icon?: string
    round?: boolean
  }
}>()

const emit = defineEmits<{
  (e: 'click'): void
}>()

const buttonType = computed(() => {
  const typeMap: Record<string, string> = {
    primary: 'primary',
    success: 'success',
    warning: 'warning',
    danger: 'danger',
    info: 'info',
    default: ''
  }
  return typeMap[props.props.type || 'default']
})

const buttonSize = computed(() => {
  const sizeMap: Record<string, string> = {
    small: 'small',
    medium: 'default',
    large: 'large'
  }
  return sizeMap[props.props.size || 'medium']
})

function handleClick() {
  if (!props.props.disabled && !props.props.loading) {
    emit('click')
    if (props.props.href) {
      window.open(props.props.href, props.props.target || '_blank')
    }
  }
}
</script>

<template>
  <el-button
    :type="buttonType"
    :size="buttonSize"
    :disabled="props.props.disabled"
    :loading="props.props.loading"
    :round="props.props.round"
    class="transition-all duration-200 hover:shadow-lg"
    @click="handleClick"
  >
    <template #icon v-if="props.props.icon === 'external'">
      <el-icon><ExternalLink /></el-icon>
    </template>
    {{ props.props.text || '按钮' }}
    <ExternalLink v-if="props.props.href && props.props.icon !== 'external'" class="ml-1.5" :size="14" />
  </el-button>
</template>