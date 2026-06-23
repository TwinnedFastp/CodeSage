<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ props: Record<string, any> }>()

interface StatItem {
  label: string
  value: string | number
  unit?: string
  trend?: string
  trendUp?: boolean
}

const stats = computed<StatItem[]>(() => props.props?.stats || [])
const title = computed(() => props.props?.title || '')
const cols = computed(() => Math.min(stats.value.length, 4))
</script>

<template>
  <div>
    <h4 v-if="title" class="font-serif text-[15px] text-[#111] mb-3">{{ title }}</h4>
    <el-row :gutter="12">
      <el-col v-for="(stat, i) in stats" :key="i" :span="24 / cols">
        <el-card shadow="never" class="!rounded-xl !border-[#E8E6E1] hover:shadow-md transition-shadow">
          <el-statistic
            :value="Number(stat.value) || stat.value"
            :title="stat.label"
            :value-style="{ fontSize: '24px', fontWeight: 700, color: '#111' }"
          >
            <template v-if="stat.unit" #suffix>
              <span class="text-[12px] text-[#777] font-normal">{{ stat.unit }}</span>
            </template>
          </el-statistic>
          <div v-if="stat.trend" class="mt-2" :class="stat.trendUp ? 'text-green-600' : 'text-red-500'" style="font-size:11px">
            {{ stat.trendUp ? '↑' : '↓' }} {{ stat.trend }}
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>
