<script setup lang="ts">
import { ArrowRight } from '@element-plus/icons-vue'

defineProps<{
  props: {
    title?: string
    subtitle?: string
    description?: string
    ctaText?: string
    ctaHref?: string
    image?: string
    gradient?: string
  }
}>()

const emit = defineEmits<{
  (e: 'cta-click'): void
}>()

function handleCtaClick() {
  emit('cta-click')
}
</script>

<template>
  <div
    class="relative rounded-3xl overflow-hidden p-8 md:p-12 text-white"
    :style="{
      background: props.gradient || 'linear-gradient(135deg, #111 0%, #333 100%)',
      minHeight: '280px'
    }"
  >
    <div class="relative z-10 flex flex-col md:flex-row items-center justify-between gap-8">
      <div class="flex-1 text-center md:text-left">
        <h1 v-if="props.title" class="text-3xl md:text-4xl lg:text-5xl font-bold mb-4 leading-tight">
          {{ props.title }}
        </h1>
        <p v-if="props.subtitle" class="text-xl md:text-2xl font-medium mb-4 opacity-90">
          {{ props.subtitle }}
        </p>
        <p v-if="props.description" class="text-base md:text-lg opacity-80 mb-6 max-w-xl">
          {{ props.description }}
        </p>
        <el-button
          v-if="props.ctaText"
          type="primary"
          size="large"
          round
          @click="handleCtaClick"
          class="bg-white text-[#111] hover:bg-gray-100"
        >
          {{ props.ctaText }}
          <el-icon class="ml-2"><ArrowRight /></el-icon>
        </el-button>
      </div>
      <div v-if="props.image" class="flex-shrink-0">
        <img
          :src="props.image"
          :alt="props.title"
          class="w-48 h-48 md:w-64 md:h-64 object-cover rounded-2xl shadow-2xl"
        />
      </div>
    </div>
    
    <!-- 装饰性背景元素 -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div class="absolute top-1/4 -left-16 w-32 h-32 bg-white/5 rounded-full blur-3xl"></div>
      <div class="absolute bottom-1/4 -right-16 w-48 h-48 bg-white/5 rounded-full blur-3xl"></div>
    </div>
  </div>
</template>