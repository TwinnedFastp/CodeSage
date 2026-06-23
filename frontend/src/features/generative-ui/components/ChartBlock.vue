<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ props: Record<string, any> }>()

const chartType = computed(() => props.props?.chart_type || 'bar')
const labels = computed<string[]>(() => props.props?.labels || [])
const datasets = computed<any[]>(() => props.props?.datasets || [])
const title = computed(() => props.props?.title || '')

// 饼图数据（适配 any→number）
const pieData = computed<number[]>(() =>
  (datasets.value[0]?.data || []).map(Number),
)
const pieDataRaw = computed<any[]>(() => datasets.value[0]?.data || [])


const maxVal = computed(() => {
  const all = datasets.value.flatMap((d) => d.data || [])
  return Math.max(...all, 1)
})

const colors = ['#111111', '#666666', '#999999', '#BBBBBB', '#DDDDDD']

// bar 数据：labels 和 values 配对（避免模板嵌套索引类型问题）
const barSeries = computed(() =>
  datasets.value.map((ds, di) => ({
    label: ds.label || `数据集 ${di + 1}`,
    color: colors[di % colors.length],
    bars: (ds.data || []).map((v: any, i: number) => ({
      label: labels.value[i] || '',
      value: Number(v),
      heightPct: Math.max((Number(v) / maxVal.value * 100), 0.5),
    })),
  })),
)

// 折线图数据点（展开为平面数组，用于 v-for）
interface Dot {
  cx: number
  cy: number
  fill: string
  key: string
}
const lineDots = computed<Dot[]>(() => {
  const dots: Dot[] = []
  datasets.value.forEach((ds, di) => {
    (ds.data || []).forEach((v: number, i: number) => {
      dots.push({
        cx: i * 60 + 30,
        cy: 150 - (v / maxVal.value * 120),
        fill: colors[di % colors.length],
        key: `d${di}-${i}`,
      })
    })
  })
  return dots
})

// 饼图扇形路径
function segPath(index: number, data: number[]) {
  const total = data.reduce((a, b) => a + b, 0)
  let cumAngle = -90
  for (let i = 0; i < index; i++) cumAngle += (data[i] / total) * 360
  const angle = (data[index] / total) * 360
  const startRad = (cumAngle * Math.PI) / 180
  const endRad = ((cumAngle + angle) * Math.PI) / 180
  const x1 = 70 + 60 * Math.cos(startRad)
  const y1 = 70 + 60 * Math.sin(startRad)
  const x2 = 70 + 60 * Math.cos(endRad)
  const y2 = 70 + 60 * Math.sin(endRad)
  const largeArc = angle > 180 ? 1 : 0
  return `M 70 70 L ${x1} ${y1} A 60 60 0 ${largeArc} 1 ${x2} ${y2} Z`
}
</script>

<template>
  <div class="rounded-xl border border-[#E8E6E1] bg-white p-5">
    <h4 v-if="title" class="font-serif text-[15px] text-[#111] mb-4">{{ title }}</h4>

    <!-- 柱状图 -->
    <div v-if="chartType === 'bar'" class="space-y-3">
      <div v-for="(ds, di) in barSeries" :key="di" class="space-y-2">
        <div class="text-[11px] text-[#777] font-medium">{{ ds.label }}</div>
        <div class="flex items-end gap-2 h-32 border-b border-[#E8E6E1]">
          <div
            v-for="(bar, bi) in ds.bars"
            :key="bi"
            class="flex-1 flex flex-col items-center justify-end group"
          >
            <span class="text-[10px] text-[#111] mb-1 opacity-0 group-hover:opacity-100 transition-opacity tabular-nums">{{ bar.value }}</span>
            <div
              class="w-full rounded-t-md transition-all duration-500 hover:opacity-80"
              :style="{
                height: bar.heightPct + '%',
                backgroundColor: ds.color,
                minHeight: '2px'
              }"
            ></div>
            <span class="text-[10px] text-[#999] mt-1 truncate max-w-full">{{ bar.label }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 折线图 -->
    <div v-else-if="chartType === 'line'" class="relative">
      <svg class="w-full h-40" :viewBox="`0 0 ${labels.length * 60} 160`" preserveAspectRatio="none">
        <line v-for="i in 4" :key="'grid' + i" :x1="0" :x2="labels.length * 60" :y1="i * 32" :y2="i * 32" stroke="#E8E6E1" stroke-width="1" />
        <polyline
          v-for="(ds, di) in datasets"
          :key="'line' + di"
          :points="(ds.data || []).map((v: number, i: number) => `${i * 60 + 30},${150 - (v / maxVal * 120)}`).join(' ')"
          fill="none"
          :stroke="colors[di % colors.length]"
          stroke-width="2"
          stroke-linejoin="round"
        />
        <circle
          v-for="dot in lineDots"
          :key="dot.key"
          :cx="dot.cx"
          :cy="dot.cy"
          r="3"
          :fill="dot.fill"
        />
      </svg>
      <div class="flex justify-around mt-2">
        <span v-for="(l, i) in labels" :key="i" class="text-[10px] text-[#999]">{{ l }}</span>
      </div>
    </div>

    <!-- 饼图 -->
    <div v-else-if="chartType === 'pie'" class="flex items-center gap-6">
      <svg width="140" height="140" viewBox="0 0 140 140" class="shrink-0">
        <circle cx="70" cy="70" r="60" fill="#FAFAFA" />
        <path
          v-for="(_, i) in pieData"
          :key="i"
          :d="segPath(i, pieData)"
          :fill="colors[i % colors.length]"
          stroke="white"
          stroke-width="2"
        />
      </svg>
      <div class="space-y-1.5 flex-1">
        <div v-for="(seg, i) in pieDataRaw" :key="'leg' + i" class="flex items-center gap-2 text-[12px]">
          <span class="w-3 h-3 rounded-sm shrink-0" :style="{ backgroundColor: colors[i % colors.length] }"></span>
          <span class="text-[#555]">{{ labels[i] }}</span>
          <span class="text-[#111] font-medium ml-auto tabular-nums">{{ seg }}</span>
        </div>
      </div>
    </div>

    <div v-else class="text-[12px] text-[#999] py-4 text-center">不支持的图表类型：{{ chartType }}</div>
  </div>
</template>
