<script setup lang="ts">
defineProps<{ props: Record<string, any> }>()
</script>

<template>
  <blockquote class="border-l-2 border-[#111111] pl-4 py-1 text-[15px] leading-relaxed text-[#333333] italic">
    <span class="whitespace-pre-wrap">{{ props.content }}</span>
    <footer v-if="props.cite" class="mt-1 text-[12px] not-italic text-[#999999]">— {{ props.cite }}</footer>
  </blockquote>
</template>
