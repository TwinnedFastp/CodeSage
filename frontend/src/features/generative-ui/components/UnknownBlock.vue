<script setup lang="ts">
defineProps<{ props: Record<string, any>; type?: string }>()
</script>

<template>
  <div class="rounded-xl border border-dashed border-(--color-border-strong) bg-(--color-surface) px-4 py-3 text-[12px] text-(--color-subtle)">
    未支持的组件类型：<span class="font-mono text-(--color-ink)">{{ type || props._unknownType || '未知' }}</span>
  </div>
</template>
