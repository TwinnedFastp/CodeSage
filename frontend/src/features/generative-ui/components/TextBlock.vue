<script setup lang="ts">
defineProps<{ props: Record<string, any> }>()
</script>

<template>
  <div class="whitespace-pre-wrap text-[15px] leading-relaxed text-[#111111]">{{ props.content }}</div>
</template>
