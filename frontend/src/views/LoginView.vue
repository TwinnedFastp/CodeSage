<script setup lang="ts">
import { ChatDotRound, ArrowRight, View } from '@element-plus/icons-vue'
import PuzzleVerify from '@/components/PuzzleVerify.vue'
import { useLoginForm } from '@/composables/useLoginForm'

const {
  formRef, form, rules, submitting,
  rememberMe, errorMsg, captchaKey,
  onCaptchaVerified, onSubmit,
} = useLoginForm()
</script>

<template>
  <div class="flex min-h-screen w-full bg-[#FAFAFA]">
    <!-- 左侧品牌区 -->
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

    <!-- 右侧表单区 -->
    <main class="flex-1 flex items-center justify-center p-6 md:p-12">
      <div class="w-full max-w-[400px] animate-fade-in-up">
        <!-- 移动端品牌头 -->
        <div class="lg:hidden flex items-center gap-3 font-semibold text-lg tracking-tight mb-10">
          <div class="w-7 h-7 bg-[#111111] rounded-full flex items-center justify-center text-[#F3F2EE]"><el-icon :size="15"><ChatDotRound /></el-icon></div>
          <span>CodeSage</span>
        </div>

        <h2 class="font-serif text-3xl text-[#111111] mb-1">登录</h2>
        <p class="text-[14px] text-[#777777] mb-8">使用注册邮箱继续</p>

        <!-- 错误提示条 -->
        <div v-if="errorMsg" class="mb-4 px-4 py-3 rounded-xl bg-red-50 border border-red-200 text-[13px] text-red-600 flex items-start gap-2 animate-shake">
          <el-icon :size="16" class="shrink-0 mt-0.5"><View /></el-icon>
          <span>{{ errorMsg }}</span>
        </div>

        <el-form :ref="formRef" :model="form" :rules="rules" label-position="top" class="codesage-form" @submit.prevent="onSubmit">
          <el-form-item label="邮箱" prop="email">
            <el-input v-model="form.email" type="email" placeholder="you@example.com" size="large" autocomplete="email" />
          </el-form-item>

          <el-form-item label="密码" prop="password">
            <el-input v-model="form.password" type="password" placeholder="••••••••" size="large" show-password autocomplete="current-password" @keyup.enter="onSubmit" />
          </el-form-item>

          <!-- 拼图验证 -->
          <el-form-item class="captcha-item"><PuzzleVerify :key="captchaKey" @verified="onCaptchaVerified" /></el-form-item>

          <!-- 记住我 -->
          <label class="flex items-center gap-2 cursor-pointer select-none mb-4 group" @click="rememberMe = !rememberMe">
            <div :class="['w-4 h-4 rounded-md border-2 flex items-center justify-center transition-all', rememberMe ? 'bg-[#111111] border-[#111111]' : 'border-[#D1CFCA] group-hover:border-[#999]']">
              <el-icon v-if="rememberMe" :size="11" color="#fff"><View /></el-icon>
            </div>
            <span class="text-[13px]" :class="rememberMe ? 'text-[#111111] font-medium' : 'text-[#999999]'">记住我（7天免登录）</span>
          </label>

          <button
            type="button"
            :disabled="submitting"
            class="w-full h-12 mt-2 bg-[#111111] hover:bg-[#333333] text-white rounded-full flex items-center justify-center gap-2 transition-all duration-300 shadow-sm disabled:opacity-60 disabled:cursor-not-allowed font-medium text-[14px]"
            @click="onSubmit"
          >
            <span v-if="!submitting">登录</span>
            <span v-else class="flex items-center gap-2">
              <svg class="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" stroke-dasharray="32 32" stroke-linecap="round"/></svg>
              登录中…
            </span>
            <el-icon v-if="!submitting" :size="16"><ArrowRight /></el-icon>
          </button>
        </el-form>

        <p class="text-center text-[13px] text-[#777777] mt-8">
          还没有账号？
          <router-link to="/register" class="text-[#111111] font-semibold hover:underline ml-1">立即注册</router-link>
        </p>

        <!-- 安全提示 -->
        <p class="text-center text-[11px] text-[#BBBBBB] mt-6 leading-relaxed">
          🔒 你的密码经过加密存储，我们无法查看原始内容
        </p>
      </div>
    </main>
  </div>
</template>

<style scoped>
:deep(.codesage-form .el-form-item__label) { font-size: 13px; font-weight: 500; color: #555555; padding-bottom: 6px; }
:deep(.codesage-form .el-input__wrapper) { border-radius: 14px !important; padding: 4px 16px; background: #ffffff; }
.captcha-item { margin-bottom: 4px; }
:deep(.captcha-item .el-form-item__content) { line-height: normal; }

/* 错误提示动画 */
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  20% { transform: translateX(-6px); }
  40% { transform: translateX(6px); }
  60% { transform: translateX(-4px); }
  80% { transform: translateX(4px); }
}
.animate-shake {
  animation: shake 0.5s ease-in-out;
}
</style>
