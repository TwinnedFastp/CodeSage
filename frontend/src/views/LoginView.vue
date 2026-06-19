<script setup lang="ts">
import { ChatDotRound, ArrowRight } from '@element-plus/icons-vue'
import PuzzleVerify from '@/components/PuzzleVerify.vue'
import { useLoginForm } from '@/composables/useLoginForm'

const {
  formRef, form, rules, submitting,
  onCaptchaVerified, onSubmit,
} = useLoginForm()
</script>

<template>
  <div class="flex min-h-screen w-full bg-[#FAFAFA]">
    <aside class="hidden lg:flex flex-col justify-between w-[44%] bg-[#F3F2EE] p-12 relative overflow-hidden">
      <div class="absolute -bottom-16 -left-8 font-serif text-[280px] leading-none text-[#111111]/[0.04] select-none pointer-events-none">Sage</div>
      <div class="flex items-center gap-3 font-semibold text-lg tracking-tight relative z-10">
        <div class="w-7 h-7 bg-[#111111] rounded-full flex items-center justify-center text-[#F3F2EE]"><el-icon :size="15"><ChatDotRound /></el-icon></div>
        <span>CodeSage</span>
      </div>
      <div class="relative z-10 max-w-md">
        <h1 class="font-serif text-5xl leading-[1.1] text-[#111111] mb-6">欢迎回来，<br />继续你的工程对话。</h1>
        <p class="text-[15px] text-[#555555] leading-relaxed">登录后即可访问你的专属会话历史、长期偏好与任务记忆——CodeSage 会记住你上次的思考脉络。</p>
      </div>
      <p class="relative z-10 text-[12px] text-[#999999] tracking-wide">© 2026 CodeSage · 你的代码工程师</p>
    </aside>

    <main class="flex-1 flex items-center justify-center p-6 md:p-12">
      <div class="w-full max-w-[400px] animate-fade-in-up">
        <div class="lg:hidden flex items-center gap-3 font-semibold text-lg tracking-tight mb-10">
          <div class="w-7 h-7 bg-[#111111] rounded-full flex items-center justify-center text-[#F3F2EE]"><el-icon :size="15"><ChatDotRound /></el-icon></div>
          <span>CodeSage</span>
        </div>
        <h2 class="font-serif text-3xl text-[#111111] mb-1">登录</h2>
        <p class="text-[14px] text-[#777777] mb-8">使用注册邮箱继续</p>

        <el-form :ref="formRef" :model="form" :rules="rules" label-position="top" class="codesage-form" @submit.prevent="onSubmit">
          <el-form-item label="邮箱" prop="email">
            <el-input v-model="form.email" type="email" placeholder="you@example.com" size="large" autocomplete="email" />
          </el-form-item>
          <el-form-item label="密码" prop="password">
            <el-input v-model="form.password" type="password" placeholder="••••••••" size="large" show-password autocomplete="current-password" @keyup.enter="onSubmit" />
          </el-form-item>
          <el-form-item class="captcha-item"><PuzzleVerify @verified="onCaptchaVerified" /></el-form-item>
          <button type="button" :disabled="submitting" class="w-full h-12 mt-2 bg-[#111111] hover:bg-[#333333] text-white rounded-full flex items-center justify-center gap-2 transition-all duration-300 shadow-sm disabled:opacity-60 disabled:cursor-not-allowed font-medium text-[14px]" @click="onSubmit">
            <span v-if="!submitting">登录</span><span v-else>登录中…</span>
            <el-icon v-if="!submitting" :size="16"><ArrowRight /></el-icon>
          </button>
        </el-form>
        <p class="text-center text-[13px] text-[#777777] mt-8">还没有账号？<router-link to="/register" class="text-[#111111] font-semibold hover:underline">立即注册</router-link></p>
      </div>
    </main>
  </div>
</template>

<style scoped>
:deep(.codesage-form .el-form-item__label) { font-size: 13px; font-weight: 500; color: #555555; padding-bottom: 6px; }
:deep(.codesage-form .el-input__wrapper) { border-radius: 14px !important; padding: 4px 16px; background: #ffffff; }
.captcha-item { margin-bottom: 4px; }
:deep(.captcha-item .el-form-item__content) { line-height: normal; }
</style>
