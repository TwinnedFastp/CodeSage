<script setup lang="ts">
import { ChatDotRound, ArrowRight, Check, View } from '@element-plus/icons-vue'
import PuzzleVerify from '@/components/PuzzleVerify.vue'
import { useRegisterForm } from '@/composables/useRegisterForm'

const {
  formRef, form, rules, submitting, registeredEmail, devVerifyLink,
  errorMsg, captchaKey,
  strength, strengthLabel, strengthColor,
  onCaptchaVerified, onSubmit, goLogin, handleVerifyClick,
} = useRegisterForm()
</script>

<template>
  <div class="flex min-h-screen w-full bg-[#FAFAFA]">
    <aside class="hidden lg:flex flex-col justify-between w-[44%] bg-[#F3F2EE] p-12 relative overflow-hidden">
      <div class="absolute -bottom-16 -right-8 font-serif text-[260px] leading-none text-[#111111]/[0.04] select-none pointer-events-none">Code</div>
      <div class="flex items-center gap-3 font-semibold text-lg tracking-tight relative z-10">
        <div class="w-7 h-7 bg-[#111111] rounded-full flex items-center justify-center text-[#F3F2EE]"><el-icon :size="15"><ChatDotRound /></el-icon></div>
        <span>CodeSage</span>
      </div>
      <div class="relative z-10 max-w-md">
        <h1 class="font-serif text-5xl leading-[1.1] text-[#111111] mb-6">开启一段<br />会记住你的工程对话。</h1>
        <p class="text-[15px] text-[#555555] leading-relaxed">注册后，CodeSage 会逐步建立你的长期偏好与事实记忆，让每一次对话都比上一次更懂你。</p>
      </div>
      <p class="relative z-10 text-[12px] text-[#999999] tracking-wide">© 2026 CodeSage · 你的代码工程师</p>
    </aside>

    <main class="flex-1 flex items-center justify-center p-6 md:p-12">
      <div class="w-full max-w-[420px] animate-fade-in-up">
        <!-- 注册成功态 -->
        <div v-if="registeredEmail" class="text-center py-8">
          <div class="w-16 h-16 rounded-full bg-[#111111] flex items-center justify-center text-white mx-auto mb-6"><el-icon :size="28"><Check /></el-icon></div>
          <h2 class="font-serif text-3xl text-[#111111] mb-3">注册成功</h2>
          <p class="text-[14px] text-[#555555] leading-relaxed mb-6 max-w-sm mx-auto">验证邮件已发送至 <span class="font-semibold text-[#111111]">{{ registeredEmail }}</span>，请在 24 小时内完成邮箱验证后登录。</p>
          <div v-if="devVerifyLink" class="mb-8 p-4 rounded-xl bg-[#F3F2EE] text-left">
            <p class="text-[12px] font-medium text-[#999999] uppercase tracking-widest mb-2">开发模式验证链接</p>
            <a :href="devVerifyLink" target="_blank" class="block text-[13px] text-[#111111] break-all hover:underline leading-relaxed" @click="handleVerifyClick">{{ devVerifyLink }}</a>
            <p class="text-[11px] text-[#999999] mt-2">点击链接完成验证，或复制到浏览器地址栏打开</p>
          </div>
          <button type="button" class="w-full h-12 bg-[#111111] hover:bg-[#333333] text-white rounded-full flex items-center justify-center gap-2 transition-all duration-300 shadow-sm font-medium text-[14px]" @click="goLogin">前往登录<el-icon :size="16"><ArrowRight /></el-icon></button>
        </div>

        <!-- 表单态 -->
        <div v-else>
          <div class="lg:hidden flex items-center gap-3 font-semibold text-lg tracking-tight mb-10">
            <div class="w-7 h-7 bg-[#111111] rounded-full flex items-center justify-center text-[#F3F2EE]"><el-icon :size="15"><ChatDotRound /></el-icon></div>
            <span>CodeSage</span>
          </div>
          <h2 class="font-serif text-3xl text-[#111111] mb-1">创建账号</h2>
          <p class="text-[14px] text-[#777777] mb-8">仅支持邮箱注册</p>

          <!-- 错误提示条 -->
          <div v-if="errorMsg" class="mb-4 px-4 py-3 rounded-xl bg-red-50 border border-red-200 text-[13px] text-red-600 flex items-start gap-2 animate-shake">
            <el-icon :size="16" class="shrink-0 mt-0.5"><View /></el-icon>
            <span>{{ errorMsg }}</span>
          </div>

          <el-form :ref="formRef" :model="form" :rules="rules" label-position="top" class="codesage-form" @submit.prevent>
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="form.email" type="email" placeholder="you@example.com" size="large" autocomplete="email" />
            </el-form-item>
            <el-form-item label="密码" prop="password">
              <el-input v-model="form.password" type="password" placeholder="至少 8 位，含大小写/数字/特殊字符" size="large" show-password autocomplete="new-password" />
              <div v-if="form.password" class="w-full flex items-center gap-3 mt-2">
                <div class="flex-1 h-[5px] rounded-full bg-[#E8E6E1] overflow-hidden">
                  <div class="h-full transition-all duration-300 ease-out" :style="{ width: `${(strength / 5) * 100}%`, background: strengthColor }"></div>
                </div>
                <span class="text-[11px] font-medium w-8 shrink-0" :style="{ color: strengthColor }">{{ strengthLabel }}</span>
              </div>
            </el-form-item>
            <el-form-item label="确认密码" prop="confirmPassword">
              <el-input v-model="form.confirmPassword" type="password" placeholder="再次输入密码" size="large" show-password autocomplete="new-password" @keyup.enter="onSubmit" />
            </el-form-item>
            <el-form-item class="captcha-item"><PuzzleVerify :key="captchaKey" @verified="onCaptchaVerified" /></el-form-item>
            <button
              type="button"
              :disabled="submitting"
              class="w-full h-12 mt-2 bg-[#111111] hover:bg-[#333333] text-white rounded-full flex items-center justify-center gap-2 transition-all duration-300 shadow-sm disabled:opacity-60 disabled:cursor-not-allowed font-medium text-[14px]"
              @click="onSubmit"
            >
              <span v-if="!submitting">创建账号</span>
              <span v-else class="flex items-center gap-2">
                <svg class="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" stroke-dasharray="32 32" stroke-linecap="round"/></svg>
                创建中…
              </span>
              <el-icon v-if="!submitting" :size="16"><ArrowRight /></el-icon>
            </button>
          </el-form>
          <p class="text-center text-[13px] text-[#777777] mt-8">已有账号？<router-link to="/login" class="text-[#111111] font-semibold hover:underline">直接登录</router-link></p>

          <!-- 安全提示 -->
          <p class="text-center text-[11px] text-[#BBBBBB] mt-6 leading-relaxed">
            🔒 密码经 bcrypt 加密存储，注册后需邮箱验证方可登录
          </p>
        </div>
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
