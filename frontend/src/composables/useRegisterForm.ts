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
  const form = reactive({ email: '', username: '', password: '', confirmPassword: '' })
  const submitting = ref(false)
  const registeredEmail = ref('')
  const devVerifyLink = ref('')
  const captchaVerified = ref(false)
  const errorMsg = ref('')
  const captchaKey = ref(0)

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
    username: [
      { required: true, message: '请输入用户名', trigger: 'blur' },
      { min: 2, max: 64, message: '用户名长度需在 2-64 字符之间', trigger: 'blur' },
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

  function onCaptchaVerified(val: boolean) {
    captchaVerified.value = val
    if (val) errorMsg.value = ''
  }

  async function onSubmit() {
    if (submitting.value) return
    errorMsg.value = ''
    if (!formRef.value) return

    const valid = await formRef.value.validate().catch(() => false)
    if (!valid) return
    if (!captchaVerified.value) {
      ElMessage.warning('请先完成拼图验证')
      return
    }

    submitting.value = true
    try {
      const resp = await register({
        email: form.email.trim(),
        username: form.username.trim(),
        password: form.password,
      })
      registeredEmail.value = form.email.trim()
      if (resp.detail) {
        const match = resp.detail.match(/(http[^)]+verify-email\?token=[^"]+)/)
        if (match) devVerifyLink.value = match[1]
      }
      ElMessage.success(resp.message || '注册成功')
    } catch (err: any) {
      const status = err.response?.status
      const detail = err.response?.data?.detail || err.response?.data?.message || ''
      const msg = detail || err.message || '注册失败，请稍后重试'
      errorMsg.value = msg

      if (status === 409) {
        ElMessage.error('该邮箱已注册，请直接登录')
      } else if (err.code === 'ERR_NETWORK') {
        ElMessage.error('无法连接到服务器，请确认后端已启动')
      } else if (status && status >= 500) {
        ElMessage.error('服务器异常，请稍后重试')
      } else {
        ElMessage.error(msg)
      }

      captchaVerified.value = false
      captchaKey.value++
    } finally {
      submitting.value = false
    }
  }

  function goLogin() {
    router.push('/login')
  }

  function handleVerifyClick(e: MouseEvent) {
    if (devVerifyLink.value.includes('verify-email')) {
      e.preventDefault()
      const url = new URL(devVerifyLink.value)
      router.replace({ path: '/verify-email', query: { token: url.searchParams.get('token') || '' } })
    }
  }

  return {
    formRef,
    form,
    rules,
    submitting,
    registeredEmail,
    devVerifyLink,
    captchaVerified,
    errorMsg,
    captchaKey,
    strength,
    strengthLabel,
    strengthColor,
    onCaptchaVerified,
    onSubmit,
    goLogin,
    handleVerifyClick,
  }
}
