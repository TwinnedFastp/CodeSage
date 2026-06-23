<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{ props: Record<string, any> }>()

interface AccordionItem {
  title: string
  content: string
  defaultOpen?: boolean
}

const items = computed<AccordionItem[]>(() => props.props?.items || [])
const title = computed(() => props.props?.title || '')

const activeNames = ref<string[]>(
  items.value.filter((i) => i.defaultOpen).map((_, idx) => `item${idx}`),
)
</script>

<template>
  <div class="rounded-xl border border-[#E8E6E1] bg-white p-5">
    <h4 v-if="title" class="font-serif text-[15px] text-[#111] mb-4">{{ title }}</h4>
    <el-collapse v-model="activeNames" class="!border-0">
      <el-collapse-item
        v-for="(item, i) in items"
        :key="i"
        :title="item.title"
        :name="`item${i}`"
        class="[&_.el-collapse-item\_\_header]:!text-[13px] [&_.el-collapse-item\_\_header]:!font-semibold [&_.el-collapse-item\_\_header]:!border-b-[#E8E6E1]"
      >
        <p class="text-[13px] leading-relaxed text-[#555] whitespace-pre-wrap py-2">{{ item.content }}</p>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>
