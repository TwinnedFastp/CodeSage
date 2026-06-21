<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ChatDotRound, Check, Close, Loading } from '@element-plus/icons-vue'
import { verifyEmail } from '@/api/auth'

const route = useRoute()
const router = useRouter()

type Status = 'loading' | 'success' | 'error'
const status = ref<Status>('loading')
const errorMsg = ref('')

onMounted(async () => {
  const token = (route.query.token as string) || ''
  if (!token) {
    status.value = 'error'
    errorMsg.value = '验证链接缺少 token 参数'
    return
  }
  try {
    await verifyEmail(token)
    status.value = 'success'
  } catch (err: any) {
    status.value = 'error'
    errorMsg.value = err.response?.data?.message || '验证失败，链接可能已过期或无效'
  }
})
</script>

<template>
  <div class="flex min-h-screen w-full items-center justify-center bg-[#FAFAFA] p-6">
    <div class="w-full max-w-[420px] text-center animate-fade-in-up">
      <div class="flex items-center gap-3 font-semibold text-lg tracking-tight mb-12 justify-center">
        <div class="w-7 h-7 bg-[#111111] rounded-full flex items-center justify-center text-[#F3F2EE]">
          <el-icon :size="15"><ChatDotRound /></el-icon>
        </div>
        <span>CodeSage</span>
      </div>

      <!-- loading -->
      <template v-if="status === 'loading'">
        <div class="w-16 h-16 rounded-full bg-[#F3F2EE] flex items-center justify-center text-[#555555] mx-auto mb-6">
          <el-icon :size="28" class="animate-spin"><Loading /></el-icon>
        </div>
        <h2 class="font-serif text-2xl text-[#111111] mb-2">正在验证邮箱…</h2>
        <p class="text-[14px] text-[#777777]">请稍候</p>
      </template>

      <!-- success -->
      <template v-else-if="status === 'success'">
        <div class="w-16 h-16 rounded-full bg-[#111111] flex items-center justify-center text-white mx-auto mb-6">
          <el-icon :size="28"><Check /></el-icon>
        </div>
        <h2 class="font-serif text-3xl text-[#111111] mb-3">邮箱验证成功</h2>
        <p class="text-[14px] text-[#555555] mb-8">现在可以使用该邮箱登录 CodeSage 了</p>
        <button
          type="button"
          class="w-full h-12 bg-[#111111] hover:bg-[#333333] text-white rounded-full flex items-center justify-center gap-2 transition-all duration-300 shadow-sm font-medium text-[14px]"
          @click="router.push('/login')"
        >
          前往登录
        </button>
      </template>

      <!-- error -->
      <template v-else>
        <div class="w-16 h-16 rounded-full bg-[#F3F2EE] flex items-center justify-center text-[#555555] mx-auto mb-6">
          <el-icon :size="28"><Close /></el-icon>
        </div>
        <h2 class="font-serif text-3xl text-[#111111] mb-3">验证失败</h2>
        <p class="text-[14px] text-[#555555] mb-8 max-w-xs mx-auto">{{ errorMsg }}</p>
        <button
          type="button"
          class="w-full h-12 bg-[#111111] hover:bg-[#333333] text-white rounded-full flex items-center justify-center gap-2 transition-all duration-300 shadow-sm font-medium text-[14px]"
          @click="router.push('/register')"
        >
          重新注册
        </button>
      </template>
    </div>
  </div>
</template>
