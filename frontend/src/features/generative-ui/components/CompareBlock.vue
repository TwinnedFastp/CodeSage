<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ props: Record<string, any> }>()

interface CompareItem {
  label: string
  left: string
  right: string
}

const items = computed<CompareItem[]>(() => props.props?.items || [])
const leftTitle = computed(() => props.props?.left_title || '方案 A')
const rightTitle = computed(() => props.props?.right_title || '方案 B')
const title = computed(() => props.props?.title || '')

const tableData = computed(() =>
  items.value.map((item) => ({
    field: item.label,
    left: item.left,
    right: item.right,
  })),
)
</script>

<template>
  <div class="rounded-xl border border-[#E8E6E1] bg-white overflow-hidden">
    <h4 v-if="title" class="font-serif text-[15px] text-[#111] px-5 pt-4 pb-3">{{ title }}</h4>
    <el-table :data="tableData" style="width:100%" :show-header="true" stripe class="!text-[13px]">
      <el-table-column prop="field" label="对比项" width="120">
        <template #default="{ row }">
          <span class="font-medium text-[#555]">{{ row.field }}</span>
        </template>
      </el-table-column>
      <el-table-column :label="leftTitle" prop="left">
        <template #default="{ row }">
          <span class="font-semibold text-[#111]">{{ row.left }}</span>
        </template>
      </el-table-column>
      <el-table-column :label="rightTitle" prop="right">
        <template #default="{ row }">
          <span class="font-semibold text-[#111]">{{ row.right }}</span>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>
