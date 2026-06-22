import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as authApi from '@/api/auth'
import type { User } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const accessToken = ref<string>(localStorage.getItem('access_token') || '')
  const refreshToken = ref<string>(localStorage.getItem('refresh_token') || '')
  const loading = ref(false)

  const isLoggedIn = computed(() => !!accessToken.value)

  function setTokens(access: string, refresh: string) {
    accessToken.value = access
    refreshToken.value = refresh
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
  }

  function clearTokens() {
    accessToken.value = ''
    refreshToken.value = ''
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    user.value = null
  }

  async function login(email: string, password: string) {
    loading.value = true
    try {
      const resp = await authApi.login({ email, password })
      setTokens(resp.access_token, resp.refresh_token)
      await fetchMe()
    } finally {
      loading.value = false
    }
  }

  async function fetchMe() {
    if (!accessToken.value) return
    try {
      user.value = await authApi.getMe()
    } catch {
      clearTokens()
    }
  }

  async function logout() {
    try {
      await authApi.logout()
    } catch {
      // 忽略网络错误，本地清 token 即可
    } finally {
      clearTokens()
    }
  }

  async function updateProfile(username: string) {
    if (!user.value) return
    user.value = await authApi.updateMe({ username })
  }

  async function uploadAvatar(file: File) {
    if (!user.value) return
    const upload = await authApi.createAvatarUpload({
      filename: file.name,
      content_type: file.type || 'image/png',
    })
    const resp = await fetch(upload.upload_url, {
      method: 'PUT',
      headers: {
        'Content-Type': file.type || 'image/png',
      },
      body: file,
    })
    if (!resp.ok) throw new Error('头像上传失败')
    user.value = await authApi.commitAvatar({
      object_key: upload.object_key,
      avatar_url: upload.public_url,
    })
  }

  return { user, accessToken, refreshToken, loading, isLoggedIn, login, logout, fetchMe, setTokens, clearTokens, updateProfile, uploadAvatar }
})
