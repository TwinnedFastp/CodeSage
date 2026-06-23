<script setup lang="ts">
defineProps<{ props: Record<string, any> }>()
</script>

<template>
  <component
    :is="props.ordered ? 'ol' : 'ul'"
    class="space-y-1.5 pl-5 text-[15px] leading-relaxed text-[#111111]"
    :class="props.ordered ? 'list-decimal' : 'list-disc'"
  >
    <li v-for="(item, i) in (props.items || [])" :key="i" class="marker:text-[#999]">{{ item }}</li>
  </component>
</template>
