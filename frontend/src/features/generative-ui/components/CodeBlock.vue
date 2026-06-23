<script setup lang="ts">
defineProps<{ props: Record<string, any> }>()
</script>

<template>
  <div class="rounded-xl overflow-hidden border border-[#111111]">
    <div v-if="props.language" class="px-3 py-1.5 bg-[#222] text-[#FAFAFA] text-[11px] font-mono tracking-wide flex items-center gap-1.5">
      <span class="w-1.5 h-1.5 rounded-full bg-[#FAFAFA]/50"></span>
      {{ props.language }}
    </div>
    <pre class="bg-[#111111] text-[#FAFAFA] p-4 overflow-x-auto custom-scrollbar text-[13px] leading-relaxed font-mono"><code>{{ props.code }}</code></pre>
  </div>
</template>
