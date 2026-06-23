<script setup lang="ts">
defineProps<{ props: Record<string, any> }>()
</script>

<template>
  <div class="rounded-2xl bg-[#F3F2EE] border border-[#E8E6E1] p-5 shadow-[0_2px_10px_rgb(0,0,0,0.03)]">
    <h3 v-if="props.title" class="font-serif text-lg text-[#111111] mb-2 leading-snug">{{ props.title }}</h3>
    <p v-if="props.content" class="whitespace-pre-wrap text-[14px] leading-relaxed text-[#333333]">{{ props.content }}</p>
  </div>
</template>
