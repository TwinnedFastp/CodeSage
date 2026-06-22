<script setup lang="ts">
defineProps<{ props: Record<string, any> }>()
</script>

<template>
  <div class="rounded-2xl border border-[#E8E6E1] bg-white p-4">
    <div v-if="(props.nodes || []).length" class="flex flex-col items-center gap-0.5">
      <template v-for="(node, i) in (props.nodes || [])" :key="'n' + i">
        <div class="px-4 py-2 rounded-xl bg-[#F3F2EE] border border-[#E8E6E1] text-[13px] text-[#111111] min-w-[128px] text-center font-medium">
          {{ node }}
        </div>
        <span v-if="Number(i) < Number(props.nodes?.length || 0) - 1" class="text-[#999] my-0.5 text-sm leading-none">↓</span>
      </template>
    </div>
    <div v-if="(props.edges || []).length" class="mt-3 pt-3 border-t border-[#E8E6E1] space-y-1">
      <div v-for="(e, i) in (props.edges || [])" :key="'e' + i" class="text-[12px] text-[#555] flex items-center gap-1.5">
        <span class="px-2 py-0.5 rounded bg-[#F3F2EE]">{{ Array.isArray(e) ? e[0] : e?.from }}</span>
        <span class="text-[#999]">→</span>
        <span class="px-2 py-0.5 rounded bg-[#F3F2EE]">{{ Array.isArray(e) ? e[1] : e?.to }}</span>
      </div>
    </div>
  </div>
</template>
