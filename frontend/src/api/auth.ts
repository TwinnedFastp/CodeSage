import request from './request'
import type { User, TokenResponse } from '@/types'

export interface RegisterPayload {
  email: string
  password: string
}

export interface LoginPayload {
  email: string
  password: string
}

// 注册：返回后端 message + detail（开发模式含验证链接）
export async function register(payload: RegisterPayload): Promise<{ message: string; detail?: string; code?: string }> {
  const { data } = await request.post('/auth/register', payload)
  return data
}

// 邮箱验证
export async function verifyEmail(token: string): Promise<{ message: string }> {
  const { data } = await request.post('/auth/verify-email', { token })
  return data
}

// 登录
export async function login(payload: LoginPayload): Promise<TokenResponse> {
  const { data } = await request.post('/auth/login', payload)
  return data
}

// 登出
export async function logout(): Promise<void> {
  await request.post('/auth/logout')
}

// 刷新令牌
export async function refreshToken(refresh_token: string): Promise<TokenResponse> {
  const { data } = await request.post('/auth/refresh', { refresh_token })
  return data
}

// 当前用户
export async function getMe(): Promise<User> {
  const { data } = await request.get('/auth/me')
  return data
}
