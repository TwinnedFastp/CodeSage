<script setup lang="ts">
defineProps<{ props: Record<string, any> }>()
</script>

<template>
  <div class="overflow-x-auto rounded-xl border border-[#E8E6E1] custom-scrollbar">
    <table class="w-full text-[13px] border-collapse">
      <thead>
        <tr class="bg-[#F3F2EE]">
          <th
            v-for="(h, i) in (props.headers || [])"
            :key="i"
            class="text-left px-3 py-2 font-serif font-medium text-[#111111] border-b border-[#E8E6E1]"
          >{{ h }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(row, ri) in (props.rows || [])" :key="ri" class="hover:bg-[#FAFAFA]">
          <td
            v-for="(cell, ci) in row"
            :key="ci"
            class="px-3 py-2 border-b border-[#E8E6E1] text-[#333333] whitespace-pre-wrap align-top"
          >{{ cell }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
