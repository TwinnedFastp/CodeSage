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

const selected = ref<number | null>(null)

function open(i: number) {
  selected.value = i
}
function close() {
  selected.value = null
}

const defaultColors = ['#111111', '#333333', '#555555', '#777777', '#999999', '#BBBBBB']
</script>

<template>
  <div>
    <h4 v-if="title" class="font-serif text-[15px] text-[#111] mb-3">{{ title }}</h4>
    <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
      <button
        v-for="(item, i) in items"
        :key="i"
        class="rounded-xl overflow-hidden border border-[#E8E6E1] hover:shadow-lg hover:-translate-y-0.5 transition-all duration-300 text-left group"
        @click="open(i)"
      >
        <!-- 封面区 -->
        <div
          class="h-28 flex items-center justify-center relative overflow-hidden"
          :style="{ backgroundColor: item.color || defaultColors[i % defaultColors.length] }"
        >
          <span v-if="item.icon" class="text-3xl opacity-50 group-hover:scale-110 transition-transform">{{ item.icon }}</span>
          <img v-else-if="item.url" :src="item.url" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
          <span v-else class="text-white/40 text-3xl">◇</span>
        </div>
        <!-- 文本区 -->
        <div class="p-3 bg-white">
          <div class="text-[12px] font-semibold text-[#111] truncate">{{ item.title || `卡片 ${i + 1}` }}</div>
          <p v-if="item.caption" class="text-[11px] text-[#777] mt-0.5 line-clamp-1">{{ item.caption }}</p>
        </div>
      </button>
    </div>

    <!-- 放大查看 -->
    <Teleport to="body">
      <transition name="gallery-fade">
        <div
          v-if="selected !== null"
          class="fixed inset-0 z-[9999] bg-black/60 backdrop-blur-sm flex items-center justify-center p-8"
          @click.self="close"
        >
          <div class="relative max-w-2xl w-full bg-white rounded-2xl shadow-2xl overflow-hidden">
            <div
              class="h-64 flex items-center justify-center"
              :style="{ backgroundColor: items[selected]?.color || defaultColors[selected % defaultColors.length] }"
            >
              <img v-if="items[selected]?.url" :src="items[selected]!.url" class="w-full h-full object-cover" />
              <span v-else-if="items[selected]?.icon" class="text-6xl opacity-60">{{ items[selected]?.icon }}</span>
              <span v-else class="text-white/40 text-6xl">◇</span>
            </div>
            <div class="p-6">
              <h5 class="font-serif text-lg text-[#111] mb-2">{{ items[selected]?.title }}</h5>
              <p class="text-[14px] text-[#555] leading-relaxed">{{ items[selected]?.caption }}</p>
            </div>
            <button class="absolute top-3 right-3 w-8 h-8 rounded-full bg-black/40 text-white flex items-center justify-center hover:bg-black/60" @click="close">✕</button>
          </div>
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<style scoped>
.gallery-fade-enter-active,
.gallery-fade-leave-active { transition: opacity 0.25s; }
.gallery-fade-enter-from,
.gallery-fade-leave-to { opacity: 0; }
</style>
