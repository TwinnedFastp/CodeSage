<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules, FormItemRule } from 'element-plus'
import { ChatDotRound, ArrowRight, Check } from '@element-plus/icons-vue'
import { register } from '@/api/auth'

const router = useRouter()

const formRef = ref<FormInstance>()
const form = reactive({
  email: '',
  password: '',
  confirmPassword: '',
})

// 密码复杂度：>=8 位，含大小写/数字/特殊字符
const passwordValidator: FormItemRule['validator'] = (_rule, value: string, callback) => {
  if (!value) return callback(new Error('请输入密码'))
  if (value.length < 8) return callback(new Error('密码长度不能少于 8 位'))
  if (!/[A-Z]/.test(value)) return callback(new Error('需包含大写字母'))
  if (!/[a-z]/.test(value)) return callback(new Error('需包含小写字母'))
  if (!/\d/.test(value)) return callback(new Error('需包含数字'))
  if (!/[^A-Za-z0-9]/.test(value)) return callback(new Error('需包含特殊字符'))
  callback()
}

const confirmValidator: FormItemRule['validator'] = (_rule, value: string, callback) => {
  if (!value) return callback(new Error('请再次输入密码'))
  if (value !== form.password) return callback(new Error('两次密码不一致'))
  callback()
}

const rules: FormRules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不合法', trigger: 'blur' },
  ],
  password: [{ required: true, validator: passwordValidator, trigger: 'blur' }],
  confirmPassword: [{ required: true, validator: confirmValidator, trigger: 'blur' }],
}

// 密码强度可视化
const strength = computed(() => {
  const p = form.password
  let score = 0
  if (p.length >= 8) score++
  if (/[A-Z]/.test(p)) score++
  if (/[a-z]/.test(p)) score++
  if (/\d/.test(p)) score++
  if (/[^A-Za-z0-9]/.test(p)) score++
  return score
})
const strengthLabel = computed(() => ['极弱', '弱', '一般', '良好', '强'][strength.value - 1] || '')
const strengthColor = computed(() => ['#D1CFCA', '#E8C7C7', '#E8E0C7', '#C7D8E8', '#111111'][strength.value] || '#D1CFCA')

const submitting = ref(false)
const registeredEmail = ref('')

async function onSubmit() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const resp = await register({ email: form.email.trim(), password: form.password })
    registeredEmail.value = form.email.trim()
    ElMessage.success(resp.message || '注册成功')
  } catch (err: any) {
    const msg = err.response?.data?.message || '注册失败，请稍后重试'
    ElMessage.error(msg)
  } finally {
    submitting.value = false
  }
}

function goLogin() {
  router.push('/login')
}
</script>

<template>
  <div class="flex min-h-screen w-full bg-[#FAFAFA]">
    <!-- 左侧品牌区 -->
    <aside class="hidden lg:flex flex-col justify-between w-[44%] bg-[#F3F2EE] p-12 relative overflow-hidden">
      <div class="absolute -bottom-16 -right-8 font-serif text-[260px] leading-none text-[#111111]/[0.04] select-none pointer-events-none">
        Code
      </div>

      <div class="flex items-center gap-3 font-semibold text-lg tracking-tight relative z-10">
        <div class="w-7 h-7 bg-[#111111] rounded-full flex items-center justify-center text-[#F3F2EE]">
          <el-icon :size="15"><ChatDotRound /></el-icon>
        </div>
        <span>CodeSage</span>
      </div>

      <div class="relative z-10 max-w-md">
        <h1 class="font-serif text-5xl leading-[1.1] text-[#111111] mb-6">
          开启一段<br />会记住你的工程对话。
        </h1>
        <p class="text-[15px] text-[#555555] leading-relaxed">
          注册后，CodeSage 会逐步建立你的长期偏好与事实记忆，让每一次对话都比上一次更懂你。
        </p>
      </div>

      <p class="relative z-10 text-[12px] text-[#999999] tracking-wide">
        © 2026 CodeSage · 你的代码工程师
      </p>
    </aside>

    <!-- 右侧表单区 -->
    <main class="flex-1 flex items-center justify-center p-6 md:p-12">
      <div class="w-full max-w-[420px] animate-fade-in-up">
        <!-- 注册成功态 -->
        <div v-if="registeredEmail" class="text-center py-8">
          <div class="w-16 h-16 rounded-full bg-[#111111] flex items-center justify-center text-white mx-auto mb-6">
            <el-icon :size="28"><Check /></el-icon>
          </div>
          <h2 class="font-serif text-3xl text-[#111111] mb-3">注册成功</h2>
          <p class="text-[14px] text-[#555555] leading-relaxed mb-8 max-w-sm mx-auto">
            验证邮件已发送至 <span class="font-semibold text-[#111111]">{{ registeredEmail }}</span>，请在 24 小时内完成邮箱验证后登录。
          </p>
          <button
            type="button"
            class="w-full h-12 bg-[#111111] hover:bg-[#333333] text-white rounded-full flex items-center justify-center gap-2 transition-all duration-300 shadow-sm font-medium text-[14px]"
            @click="goLogin"
          >
            前往登录
            <el-icon :size="16"><ArrowRight /></el-icon>
          </button>
        </div>

        <!-- 表单态 -->
        <div v-else>
          <div class="lg:hidden flex items-center gap-3 font-semibold text-lg tracking-tight mb-10">
            <div class="w-7 h-7 bg-[#111111] rounded-full flex items-center justify-center text-[#F3F2EE]">
              <el-icon :size="15"><ChatDotRound /></el-icon>
            </div>
            <span>CodeSage</span>
          </div>

          <h2 class="font-serif text-3xl text-[#111111] mb-1">创建账号</h2>
          <p class="text-[14px] text-[#777777] mb-8">仅支持邮箱注册</p>

          <el-form
            ref="formRef"
            :model="form"
            :rules="rules"
            label-position="top"
            class="codesage-form"
            @submit.prevent="onSubmit"
          >
            <el-form-item label="邮箱" prop="email">
              <el-input
                v-model="form.email"
                type="email"
                placeholder="you@example.com"
                size="large"
                autocomplete="email"
              />
            </el-form-item>

            <el-form-item label="密码" prop="password">
              <el-input
                v-model="form.password"
                type="password"
                placeholder="至少 8 位，含大小写/数字/特殊字符"
                size="large"
                show-password
                autocomplete="new-password"
              />
              <!-- 密码强度条 -->
              <div v-if="form.password" class="w-full flex items-center gap-2 mt-2">
                <div class="flex-1 h-1 rounded-full bg-[#E8E6E1] overflow-hidden">
                  <div
                    class="h-full transition-all duration-300"
                    :style="{ width: `${(strength / 5) * 100}%`, background: strengthColor }"
                  ></div>
                </div>
                <span class="text-[11px] text-[#777777] w-8">{{ strengthLabel }}</span>
              </div>
            </el-form-item>

            <el-form-item label="确认密码" prop="confirmPassword">
              <el-input
                v-model="form.confirmPassword"
                type="password"
                placeholder="再次输入密码"
                size="large"
                show-password
                autocomplete="new-password"
                @keyup.enter="onSubmit"
              />
            </el-form-item>

            <button
              type="button"
              :disabled="submitting"
              class="w-full h-12 mt-2 bg-[#111111] hover:bg-[#333333] text-white rounded-full flex items-center justify-center gap-2 transition-all duration-300 shadow-sm disabled:opacity-60 disabled:cursor-not-allowed font-medium text-[14px]"
              @click="onSubmit"
            >
              <span v-if="!submitting">创建账号</span>
              <span v-else>创建中…</span>
              <el-icon v-if="!submitting" :size="16"><ArrowRight /></el-icon>
            </button>
          </el-form>

          <p class="text-center text-[13px] text-[#777777] mt-8">
            已有账号？
            <router-link to="/login" class="text-[#111111] font-semibold hover:underline">直接登录</router-link>
          </p>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
:deep(.codesage-form .el-form-item__label) {
  font-size: 13px;
  font-weight: 500;
  color: #555555;
  padding-bottom: 6px;
}
:deep(.codesage-form .el-input__wrapper) {
  border-radius: 14px !important;
  padding: 4px 16px;
  background: #ffffff;
}
</style>
