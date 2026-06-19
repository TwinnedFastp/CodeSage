/**
 * 登录表单逻辑：校验 + 提交 + 拼图验证门控
 */
import { ref, reactive } from 'vue'
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

  const rules: FormRules = {
    email: [
      { required: true, message: '请输入邮箱', trigger: 'blur' },
      { type: 'email', message: '邮箱格式不合法', trigger: 'blur' },
    ],
    password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  }

  function onCaptchaVerified(val: boolean) {
    captchaVerified.value = val
  }

  async function onSubmit() {
    if (!formRef.value) return
    const valid = await formRef.value.validate().catch(() => false)
    if (!valid) return
    if (!captchaVerified.value) {
      ElMessage.warning('请先完成拼图验证')
      return
    }

    submitting.value = true
    try {
      await auth.login(form.email.trim(), form.password)
      ElMessage.success('登录成功')
      router.replace((route.query.redirect as string) || '/chat')
    } catch (err: any) {
      ElMessage.error(err.response?.data?.message || '登录失败，请稍后重试')
    } finally {
      submitting.value = false
    }
  }

  return { formRef, form, rules, submitting, captchaVerified, onCaptchaVerified, onSubmit }
}
