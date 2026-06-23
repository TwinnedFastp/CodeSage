<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{ props: Record<string, any> }>()

interface TabItem {
  label: string
  content: string
}

const tabs = computed<TabItem[]>(() => props.props?.tabs || [])
const title = computed(() => props.props?.title || '')
const activeName = ref(tabs.value[0]?.label || 'tab0')
</script>

<template>
  <div class="rounded-xl border border-[#E8E6E1] bg-white p-5">
    <h4 v-if="title" class="font-serif text-[15px] text-[#111] mb-4">{{ title }}</h4>
    <el-tabs v-model="activeName" type="border-card" class="!shadow-none !border-[#E8E6E1] [&_.el-tabs\_\_header]:!bg-[#FAFAFA]">
      <el-tab-pane
        v-for="(tab, i) in tabs"
        :key="i"
        :label="tab.label"
        :name="tab.label"
      >
        <p class="text-[14px] leading-relaxed text-[#333] whitespace-pre-wrap py-2">{{ tab.content }}</p>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>
