/**
 * 注册表单逻辑：校验 + 密码强度 + 提交 + 开发模式验证链接
 */
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules, FormItemRule } from 'element-plus'
import { register } from '@/api/auth'

export function useRegisterForm() {
  const router = useRouter()
  const formRef = ref<FormInstance>()
  const form = reactive({ email: '', password: '', confirmPassword: '' })
  const submitting = ref(false)
  const registeredEmail = ref('')
  const devVerifyLink = ref('')
  const captchaVerified = ref(false)

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
  const strengthColor = computed(() => ['#D9483F', '#E8854A', '#F0C042', '#6BAF6B', '#3A8A5E'][strength.value - 1] || '#E8E6E1')

  function onCaptchaVerified(val: boolean) { captchaVerified.value = val }

  async function onSubmit() {
    if (!formRef.value) return
    const valid = await formRef.value.validate().catch(() => false)
    if (!valid) return
    if (!captchaVerified.value) { ElMessage.warning('请先完成拼图验证'); return }

    submitting.value = true
    try {
      const resp = await register({ email: form.email.trim(), password: form.password })
      registeredEmail.value = form.email.trim()
      if (resp.detail) {
        const match = resp.detail.match(/(http[^)]+verify-email\?token=[^"]+)/)
        if (match) devVerifyLink.value = match[1]
      }
      ElMessage.success(resp.message || '注册成功')
    } catch (err: any) {
      ElMessage.error(err.response?.data?.message || '注册失败，请稍后重试')
    } finally {
      submitting.value = false
    }
  }

  function goLogin() { router.push('/login') }

  function handleVerifyClick(e: MouseEvent) {
    if (devVerifyLink.value.includes('verify-email')) {
      e.preventDefault()
      const url = new URL(devVerifyLink.value)
      router.replace({ path: '/verify-email', query: { token: url.searchParams.get('token') || '' } })
    }
  }

  return {
    formRef, form, rules, submitting, registeredEmail, devVerifyLink, captchaVerified,
    strength, strengthLabel, strengthColor,
    onCaptchaVerified, onSubmit, goLogin, handleVerifyClick,
  }
}
