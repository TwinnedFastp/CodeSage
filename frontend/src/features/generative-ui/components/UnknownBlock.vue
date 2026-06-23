<script setup lang="ts">
defineProps<{ props: Record<string, any>; type?: string }>()
</script>

<template>
  <div class="rounded-xl border border-dashed border-[#D1CFCA] bg-[#FAFAFA] px-4 py-3 text-[12px] text-[#777777]">
    未支持的组件类型：<span class="font-mono text-[#111111]">{{ type || props._unknownType || '未知' }}</span>
  </div>
</template>
