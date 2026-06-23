<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{ props: Record<string, any> }>()

interface GalleryItem {
  title?: string
  caption?: string
  url?: string
  color?: string
  icon?: string
}

const items = computed<GalleryItem[]>(() => props.props?.items || [])
const title = computed(() => props.props?.title || '')
const viewerVisible = ref(false)
const viewerIndex = ref(0)
const viewerUrl = computed(() => items.value[viewerIndex.value]?.url || '')

const defaultColors = ['#111111', '#333333', '#555555', '#777777', '#999999', '#BBBBBB']

function openViewer(i: number) {
  viewerIndex.value = i
  viewerVisible.value = true
}
</script>

<template>
  <div>
    <h4 v-if="title" class="font-serif text-[15px] text-[#111] mb-3">{{ title }}</h4>
    <el-row :gutter="12">
      <el-col v-for="(item, i) in items" :key="i" :xs="12" :sm="8" :md="6" class="mb-3">
        <el-card
          shadow="never"
          :body-style="{ padding: 0 }"
          class="!rounded-xl !border-[#E8E6E1] hover:shadow-lg hover:-translate-y-1 transition-all duration-300 cursor-pointer overflow-hidden group"
          @click="openViewer(i)"
        >
          <div
            class="h-28 flex items-center justify-center relative"
            :style="{ backgroundColor: item.color || defaultColors[i % defaultColors.length] }"
          >
            <img v-if="item.url" :src="item.url" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
            <span v-else-if="item.icon" class="text-3xl opacity-40 group-hover:scale-110 transition-transform">{{ item.icon }}</span>
            <span v-else class="text-white/30 text-3xl">+</span>
          </div>
          <div class="p-3">
            <div class="text-[12px] font-semibold text-[#111] truncate">{{ item.title || `卡片 ${i + 1}` }}</div>
            <p v-if="item.caption" class="text-[11px] text-[#777] mt-0.5 line-clamp-1">{{ item.caption }}</p>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-image-viewer
      v-if="viewerVisible && viewerUrl"
      :url-list="items.map(i => i.url || '')"
      :initial-index="viewerIndex"
      @close="viewerVisible = false"
      hide-on-click-modal
    />
  </div>
</template>
