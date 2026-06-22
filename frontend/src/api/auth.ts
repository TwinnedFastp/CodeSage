import request from './request'
import type { User, TokenResponse } from '@/types'

export interface RegisterPayload {
  email: string
  password: string
  username?: string
}

export interface LoginPayload {
  email: string
  password: string
}

// 注册：返回后端 message + detail（开发模式下含验证链接）
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

export async function getMe(): Promise<User> {
  const { data } = await request.get('/auth/me')
  return data
}

export interface UpdateMePayload {
  username: string
}

export async function updateMe(payload: UpdateMePayload): Promise<User> {
  const { data } = await request.put('/auth/me', payload)
  return data
}

export interface AvatarUploadPayload {
  filename: string
  content_type: string
}

export interface AvatarUploadResponse {
  upload_url: string
  object_key: string
  public_url: string
  expires_in: number
}

export interface AvatarCommitPayload {
  object_key: string
  avatar_url: string
}

export async function createAvatarUpload(payload: AvatarUploadPayload): Promise<AvatarUploadResponse> {
  const { data } = await request.post('/auth/me/avatar/upload', payload)
  return data
}

export async function commitAvatar(payload: AvatarCommitPayload): Promise<User> {
  const { data } = await request.post('/auth/me/avatar/commit', payload)
  return data
}
