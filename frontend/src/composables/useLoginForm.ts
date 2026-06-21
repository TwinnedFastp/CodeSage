/**
 * 登录表单逻辑：校验 + 提交 + 拼图验证门控 + 记住我
 */
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

export function useLoginForm() {
  const router = useRouter()
  const route = useRoute()
  const auth = useAuthStore()

  const formRef = ref<FormInstance>()
  const form = reactive({ email: '', password: '' })
  const submitting = ref(false)
  const captchaVerified = ref(false)
  const rememberMe = ref(false)
  const errorMsg = ref('')
  // 拼图验证码组件的 key，变更后强制重新挂载以重置内部状态
  const captchaKey = ref(0)

  // 页面加载时检查是否有缓存的邮箱（记住我）
  onMounted(() => {
    const savedEmail = localStorage.getItem('codesage_login_email')
    if (savedEmail) form.email = savedEmail
    rememberMe.value = !!localStorage.getItem('codesage_remember_me')
  })

  const rules: FormRules = {
    email: [
      { required: true, message: '请输入邮箱', trigger: 'blur' },
      { type: 'email', message: '邮箱格式不合法', trigger: 'blur' },
    ],
    password: [
      { required: true, message: '请输入密码', trigger: 'blur' },
      { min: 8, message: '密码至少 8 位', trigger: 'blur' },
    ],
  }

  function onCaptchaVerified(val: boolean) {
    captchaVerified.value = val
    if (val) errorMsg.value = '' // 验证通过时清除之前的错误提示
  }

  async function onSubmit() {
    console.log('[Login] onSubmit triggered, submitting:', submitting.value)

    // 防重入：避免 click + submit 双重触发
    if (submitting.value) {
      console.log('[Login] 已在提交中，跳过')
      return
    }
    errorMsg.value = ''

    if (!formRef.value) {
      console.error('[Login] formRef 不存在!')
      return
    }

    // 前端预校验
    console.log('[Login] 开始表单验证...')
    const valid = await formRef.value.validate().catch((err) => {
      console.warn('[Login] 表单验证失败:', err)
      return false
    })
    if (!valid) {
      console.log('[Login] 验证未通过，终止提交')
      return
    }

    if (!captchaVerified.value) {
      console.log('[Login] 验证码未通过, captchaVerified:', captchaVerified.value)
      ElMessage.warning('请先完成拼图验证')
      return
    }

    console.log('[Login] 开始提交登录请求...', { email: form.email.trim() })
    submitting.value = true
    try {
      await auth.login(form.email.trim(), form.password)
      // 记住我：保存邮箱
      if (rememberMe.value) {
        localStorage.setItem('codesage_login_email', form.email.trim())
        localStorage.setItem('codesage_remember_me', '1')
      } else {
        localStorage.removeItem('codesage_login_email')
        localStorage.removeItem('codesage_remember_me')
      }
      ElMessage.success('登录成功')
      router.replace((route.query.redirect as string) || '/chat')
    } catch (err: any) {
      const detail = err.response?.data?.detail || err.response?.data?.message || ''
      const msg = detail || err.message || '登录失败，请稍后重试'
      errorMsg.value = msg
      // 区分不同错误类型给出友好提示
      if (err.response?.status === 401) {
        ElMessage.error('邮箱或密码不正确')
      } else if (err.response?.status === 403) {
        ElMessage.error(msg || '账号已被锁定，请 15 分钟后再试')
      } else if (err.code === 'ERR_NETWORK') {
        ElMessage.error('无法连接到服务器，请确认后端已启动')
      } else {
        ElMessage.error(msg)
      }
      // 登录失败后刷新验证码（安全考虑）：强制 PuzzleVerify 重新挂载
      captchaVerified.value = false
      captchaKey.value++
    } finally {
      submitting.value = false
    }
  }

  return {
    formRef, form, rules, submitting, captchaVerified,
    rememberMe, errorMsg, captchaKey,
    onCaptchaVerified, onSubmit,
  }
}
