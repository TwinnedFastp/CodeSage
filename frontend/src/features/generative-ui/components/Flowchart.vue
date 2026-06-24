<script setup lang="ts">
defineProps<{ props: Record<string, any> }>()
</script>

<template>
  <div class="rounded-2xl border border-(--color-border) bg-(--color-surface) p-4">
    <div v-if="(props.nodes || []).length" class="flex flex-col items-center gap-0.5">
      <template v-for="(node, i) in (props.nodes || [])" :key="'n' + i">
        <div class="px-4 py-2 rounded-xl bg-(--color-surface-soft) border border-(--color-border) text-[13px] text-(--color-ink) min-w-[128px] text-center font-medium">
          {{ node }}
        </div>
        <span v-if="Number(i) < Number(props.nodes?.length || 0) - 1" class="text-(--color-faint) my-0.5 text-sm leading-none">↓</span>
      </template>
    </div>
    <div v-if="(props.edges || []).length" class="mt-3 pt-3 border-t border-(--color-border) space-y-1">
      <div v-for="(e, i) in (props.edges || [])" :key="'e' + i" class="text-[12px] text-(--color-muted) flex items-center gap-1.5">
        <span class="px-2 py-0.5 rounded bg-(--color-surface-soft)">{{ Array.isArray(e) ? e[0] : e?.from }}</span>
        <span class="text-(--color-faint)">→</span>
        <span class="px-2 py-0.5 rounded bg-(--color-surface-soft)">{{ Array.isArray(e) ? e[1] : e?.to }}</span>
      </div>
    </div>
  </div>
</template>
