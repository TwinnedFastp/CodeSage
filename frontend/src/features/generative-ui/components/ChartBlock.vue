<script setup lang="ts">
import { computed, shallowRef, watch } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { BarChart, LineChart, PieChart, ScatterChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, TitleComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

use([BarChart, LineChart, PieChart, ScatterChart, GridComponent, TooltipComponent, LegendComponent, TitleComponent, CanvasRenderer])

const props = defineProps<{ props: Record<string, any> }>()

const chartType = computed(() => props.props?.chart_type || 'bar')
const labels = computed<string[]>(() => props.props?.labels || [])
const datasets = computed<any[]>(() => props.props?.datasets || [])
const title = computed(() => props.props?.title || '')
const smooth = computed(() => props.props?.smooth !== false)

const colors = ['#111111', '#666666', '#999999', '#AAAAAA', '#CCCCCC', '#DDDDDD']

// ECharts 使用 shallowRef 避免深度响应追踪导致性能问题
const chartOption = shallowRef<any>({})

watch([chartType, labels, datasets, title, smooth], () => {
  if (!labels.value.length) return

  if (chartType.value === 'pie') {
    chartOption.value = {
      title: { text: title.value, left: 'center', textStyle: { fontSize: 14, fontWeight: 500 } },
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      legend: { bottom: 0, textStyle: { fontSize: 11 } },
      series: [{
        type: 'pie',
        radius: ['45%', '72%'],
        center: ['50%', '48%'],
        data: labels.value.map((l, i) => ({
          name: l,
          value: Number(datasets.value[0]?.data?.[i]) || 0,
        })),
        itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 },
        label: { fontSize: 11 },
      }],
      color: colors,
      backgroundColor: 'transparent',
    }
  } else if (chartType.value === 'line' || chartType.value === 'scatter') {
    chartOption.value = {
      title: { text: title.value, left: 'center', textStyle: { fontSize: 14, fontWeight: 500 } },
      tooltip: { trigger: 'axis' },
      legend: { bottom: 0, textStyle: { fontSize: 11 }, itemWidth: 12, itemHeight: 12 },
      grid: { left: 50, right: 20, top: 40, bottom: 50 },
      xAxis: { type: 'category', data: labels.value, axisLabel: { fontSize: 10 } },
      yAxis: { type: 'value', axisLabel: { fontSize: 10 } },
      series: datasets.value.map((ds: any, di: number) => ({
        name: ds.label || `系列 ${di + 1}`,
        type: chartType.value === 'scatter' ? 'scatter' : 'line',
        data: (ds.data || []).map(Number),
        smooth: chartType.value === 'line' && smooth.value,
        symbolSize: 6,
      })),
      color: colors,
      backgroundColor: 'transparent',
    }
  } else {
    // bar (default)
    chartOption.value = {
      title: { text: title.value, left: 'center', textStyle: { fontSize: 14, fontWeight: 500 } },
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      legend: { bottom: 0, textStyle: { fontSize: 11 }, itemWidth: 12, itemHeight: 12 },
      grid: { left: 50, right: 20, top: 40, bottom: 50 },
      xAxis: { type: 'category', data: labels.value, axisLabel: { fontSize: 10 } },
      yAxis: { type: 'value', axisLabel: { fontSize: 10 } },
      series: datasets.value.map((ds: any, di: number) => ({
        name: ds.label || `系列 ${di + 1}`,
        type: 'bar',
        data: (ds.data || []).map(Number),
        barMaxWidth: 40,
        itemStyle: { borderRadius: [4, 4, 0, 0] },
      })),
      color: colors,
      backgroundColor: 'transparent',
    }
  }
}, { immediate: true, deep: true })
</script>

<template>
  <div class="rounded-xl border border-[#E8E6E1] bg-white p-4">
    <VChart
      v-if="chartOption.series"
      class="w-full"
      style="height: 300px"
      :option="chartOption"
      autoresize
    />
    <div v-else class="text-[12px] text-[#999] py-8 text-center">正在加载图表数据…</div>
  </div>
</template>
