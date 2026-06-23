<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft, Plus, User as UserIcon, Cpu,
  Check, View, Hide, Star, Coin,
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useProviders } from '@/composables/useProviders'
import { useResponsive } from '@/composables/useResponsive'
import type { Provider } from '@/api/providers'
// 复用供应商卡片组件：分离展示逻辑 + hover 阴影上浮效果
import ProviderCard from '@/components/ProviderCard.vue'

const router = useRouter()
const auth = useAuthStore()

// 移动端检测：用于侧栏改顶栏 / 弹窗宽度 / 内边距适配
const { isMobile } = useResponsive()

const {
  providers, loading, saving, presets,
  createProvider, updateProvider, deleteProvider, toggleProvider,
} = useProviders()

// ---- 侧边导航 ----
const activeTab = ref<'account' | 'providers'>('providers')

// ---- 供应商编辑弹窗 ----
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const form = ref({
  provider_name: '',
  llm_api_key: '',
  llm_base_url: '',
  llm_model: '',
  embedding_model: '',
  embedding_dim: 1024,
})
const showApiKey = ref(false)

const isEditing = computed(() => editingId.value !== null)
const dialogTitle = computed(() => isEditing.value ? '编辑供应商' : '添加供应商')

function openCreateDialog() {
  editingId.value = null
  form.value = {
    provider_name: '',
    llm_api_key: '',
    llm_base_url: '',
    llm_model: '',
    embedding_model: '',
    embedding_dim: 1024,
  }
  showApiKey.value = false
  dialogVisible.value = true
}

function openEditDialog(p: Provider) {
  editingId.value = p.id
  form.value = {
    provider_name: p.provider_name,
    llm_api_key: '', // 编辑时不回填真实 key，用户不修改就留空
    llm_base_url: p.llm_base_url,
    llm_model: p.llm_model,
    embedding_model: p.embedding_model,
    embedding_dim: p.embedding_dim,
  }
  showApiKey.value = false
  dialogVisible.value = true
}

function applyPreset(preset: typeof presets[0]) {
  form.value.provider_name = preset.provider_name
  form.value.llm_base_url = preset.llm_base_url
  form.value.llm_model = preset.llm_model
  form.value.embedding_model = preset.embedding_model
  form.value.embedding_dim = preset.embedding_dim
}

async function onSave() {
  // 基础校验
  const f = form.value
  if (!f.provider_name.trim()) { ElMessage.warning('请填写供应商名称'); return }
  if (!isEditing.value && !f.llm_api_key.trim()) { ElMessage.warning('请填写 API Key'); return }
  if (!f.llm_base_url.trim()) { ElMessage.warning('请填写 Base URL'); return }
  if (!f.llm_model.trim()) { ElMessage.warning('请填写 LLM 模型名称'); return }
  if (!f.embedding_model.trim()) { ElMessage.warning('请填写 Embedding 模型名称'); return }
  if (!f.embedding_dim || f.embedding_dim < 1) { ElMessage.warning('Embedding 维度必须大于 0'); return }

  if (isEditing.value) {
    const updateData: Record<string, any> = {
      provider_name: f.provider_name,
      llm_base_url: f.llm_base_url,
      llm_model: f.llm_model,
      embedding_model: f.embedding_model,
      embedding_dim: f.embedding_dim,
    }
    // API Key 仅在用户填写了新值时才更新
    if (f.llm_api_key.trim()) {
      updateData.llm_api_key = f.llm_api_key
    }
    const ok = await updateProvider(editingId.value!, updateData)
    if (ok) dialogVisible.value = false
  } else {
    const ok = await createProvider(f)
    if (ok) dialogVisible.value = false
  }
}

async function onToggle(p: Provider) {
  await toggleProvider(p.id)
}

async function onDelete(p: Provider) {
  await deleteProvider(p.id)
}

async function onLogout() {
  await auth.logout()
  ElMessage.success('已登出')
  router.push('/login')
}

const profileForm = ref({ username: auth.user?.username || '' })
const avatarUploading = ref(false)
const avatarInput = ref<HTMLInputElement | null>(null)
const maskedEmail = computed(() => {
  const e = auth.user?.email || ''
  if (!e) return ''
  const [name, domain] = e.split('@')
  return domain ? `${name[0]}***@${domain}` : e
})
const displayName = computed(() => auth.user?.username || maskedEmail.value || 'CodeSage 用户')
// 头像 URL 加时间戳破浏览器缓存，确保更新后立即刷新
const avatarUrl = computed(() => {
  const url = auth.user?.avatar_url
  return url ? (url.includes('?') ? `${url}&_t=${Date.now()}` : `${url}?_t=${Date.now()}`) : ''
})
const avatarInitial = computed(() => displayName.value.slice(0, 1).toUpperCase())
watch(() => auth.user?.username, (username) => {
  profileForm.value.username = username || ''
})

async function saveProfile() {
  const username = profileForm.value.username.trim()
  if (!username) {
    ElMessage.warning('请填写用户名')
    return
  }
  try {
    await auth.updateProfile(username)
    ElMessage.success('用户名已更新')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '保存失败，请稍后重试')
  }
}

async function onAvatarChange(file: File) {
  if (!file.type.startsWith('image/')) {
    ElMessage.warning('请选择图片文件')
    return
  }
  avatarUploading.value = true
  try {
    await auth.uploadAvatar(file)
    ElMessage.success('头像已更新')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '头像上传失败')
  } finally {
    avatarUploading.value = false
  }
}

function onAvatarInput(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) onAvatarChange(file)
  input.value = ''
}
</script>

<template>
  <div class="flex flex-col md:flex-row h-screen w-screen bg-[#FAFAFA] text-[#111111] overflow-hidden antialiased font-sans">

    <!-- 左侧导航（桌面端） -->
    <aside v-if="!isMobile" class="w-[280px] bg-[#F3F2EE] flex flex-col shrink-0">
      <div class="p-6 flex items-center justify-between h-20">
        <button @click="router.push('/chat')" class="flex items-center gap-2 text-[13px] text-[#777] hover:text-[#111] transition-colors">
          <el-icon :size="16"><ArrowLeft /></el-icon>
          <span>返回对话</span>
        </button>
      </div>

      <div class="px-6 mb-6">
        <h1 class="font-serif text-2xl tracking-tight text-[#111]">设置</h1>
        <p class="text-[12px] text-[#999] mt-1">管理你的账户与模型配置</p>
      </div>

      <nav class="flex-1 px-3 space-y-1">
        <button
          @click="activeTab = 'account'"
          :class="['w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all text-[14px]', activeTab === 'account' ? 'bg-white text-[#111] font-medium shadow-sm' : 'text-[#666] hover:bg-[#E8E6E1]']"
        >
          <el-icon :size="18"><UserIcon /></el-icon>
          <span>账户信息</span>
        </button>
        <button
          @click="activeTab = 'providers'"
          :class="['w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all text-[14px]', activeTab === 'providers' ? 'bg-white text-[#111] font-medium shadow-sm' : 'text-[#666] hover:bg-[#E8E6E1]']"
        >
          <el-icon :size="18"><Cpu /></el-icon>
          <span>模型供应商</span>
          <span v-if="providers.length > 0" class="ml-auto text-[11px] px-2 py-0.5 rounded-full bg-[#E8E6E1] text-[#666]">{{ providers.length }}</span>
        </button>
      </nav>

      <div class="p-5 border-t border-[#E8E6E1]/50">
        <div class="flex items-center gap-3 mb-3">
          <el-avatar
            :size="36"
            :src="avatarUrl"
            :style="{ backgroundColor: avatarUrl ? 'transparent' : '#E8E6E1', color: '#555', fontSize: '14px', fontWeight: 600 }"
          >
            {{ displayName.slice(0, 1).toUpperCase() }}
          </el-avatar>
          <div class="flex flex-col min-w-0">
            <span class="text-[13px] font-semibold truncate">{{ displayName }}</span>
            <span class="text-[11px] text-[#777]">{{ auth.user?.email_verified ? '已验证' : '未验证' }}</span>
          </div>
        </div>
        <button class="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-full text-[12px] text-[#777] hover:text-[#111] hover:bg-[#E8E6E1] transition-colors" @click="onLogout">
          <span>退出登录</span>
        </button>
      </div>
    </aside>

    <!-- 顶部导航（移动端）：返回 + 标签切换 -->
    <header v-else class="shrink-0 bg-[#F3F2EE] border-b border-[#E8E6E1]/60">
      <div class="flex items-center justify-between px-4 h-14">
        <button @click="router.push('/chat')" class="flex items-center gap-1.5 text-[13px] text-[#777] hover:text-[#111] transition-colors">
          <el-icon :size="16"><ArrowLeft /></el-icon>
          <span>返回</span>
        </button>
        <h1 class="font-serif text-lg tracking-tight text-[#111]">设置</h1>
        <button @click="onLogout" class="text-[12px] text-[#777] hover:text-[#111] transition-colors">退出</button>
      </div>
      <!-- 顶部标签条 -->
      <nav class="flex px-2 pb-2 gap-1">
        <button
          @click="router.push('/database-admin')"
          class="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg transition-all text-[13px] text-[#666]"
        >
          <el-icon :size="15"><Coin /></el-icon>
          <span>数据库</span>
        </button>
        <button
          @click="activeTab = 'account'"
          :class="['flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg transition-all text-[13px]', activeTab === 'account' ? 'bg-white text-[#111] font-medium shadow-sm' : 'text-[#666]']"
        >
          <el-icon :size="15"><UserIcon /></el-icon>
          <span>账户</span>
        </button>
        <button
          @click="activeTab = 'providers'"
          :class="['flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg transition-all text-[13px]', activeTab === 'providers' ? 'bg-white text-[#111] font-medium shadow-sm' : 'text-[#666]']"
        >
          <el-icon :size="15"><Cpu /></el-icon>
          <span>供应商</span>
          <span v-if="providers.length > 0" class="text-[10px] px-1.5 py-0.5 rounded-full bg-[#E8E6E1] text-[#666]">{{ providers.length }}</span>
        </button>
      </nav>
    </header>

    <!-- 主内容区 -->
    <main class="flex-1 overflow-y-auto custom-scrollbar">
      <div class="max-w-3xl mx-auto px-4 py-6 sm:px-8 sm:py-12">

        <!-- 账户信息 -->
        <div v-if="activeTab === 'account'" class="animate-fade-in-up">
          <h2 class="font-serif text-3xl tracking-tight mb-2">账户信息</h2>
          <p class="text-[13px] text-[#999] mb-10">你的账户基础信息与安全状态</p>

          <div class="space-y-6">
            <div class="bg-white rounded-2xl border border-[#E8E6E1] p-6">
              <div class="flex items-center justify-between gap-4">
                <div class="flex items-center gap-4">
                  <div class="w-12 h-12 rounded-xl bg-[#111] text-white flex items-center justify-center">
                    <el-icon :size="22"><Coin /></el-icon>
                  </div>
                  <div>
                    <p class="text-[15px] font-semibold">PostgreSQL 数据库管理</p>
                    <p class="text-[12px] text-[#999] mt-0.5">查看 public 表、分页查询、按主键新增/编辑/删除记录</p>
                  </div>
                </div>
                <button
                  @click="router.push('/database-admin')"
                  class="shrink-0 px-5 py-2 rounded-full text-[13px] font-medium bg-[#111] text-white hover:bg-[#333] transition-colors"
                >
                  进入管理
                </button>
              </div>
            </div>

            <div class="bg-white rounded-2xl border border-[#E8E6E1] p-6">
              <div class="flex flex-col sm:flex-row sm:items-center gap-5 mb-6">
                <div class="relative group cursor-pointer" @click="avatarInput?.click()">
                  <el-avatar
                    :size="80"
                    :src="avatarUrl"
                    class="!rounded-2xl shadow-md ring-2 ring-[#E8E6E1] transition-all duration-300 group-hover:ring-[#111] group-hover:shadow-lg shrink-0"
                    :style="{ backgroundColor: avatarUrl ? 'transparent' : '#111', color: 'white', fontSize: '28px', fontWeight: 600 }"
                  >
                    {{ avatarInitial }}
                  </el-avatar>
                  <!-- hover 遮罩 -->
                  <div class="absolute inset-0 !rounded-2xl bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex items-center justify-center">
                    <span v-if="avatarUploading" class="text-white text-xs">上传中…</span>
                    <template v-else>
                      <el-icon :size="20" class="text-white"><Plus /></el-icon>
                      <span class="text-white text-xs ml-1 font-medium">更换</span>
                    </template>
                  </div>
                  <!-- 上传中 loading -->
                  <div v-if="avatarUploading" class="absolute inset-0 !rounded-2xl bg-white/60 flex items-center justify-center z-10">
                    <el-icon :size="24" class="animate-spin text-[#111]"><Operation /></el-icon>
                  </div>
                  <input ref="avatarInput" type="file" accept="image/png,image/jpeg,image/webp,image/gif" class="hidden" :disabled="avatarUploading" @change="onAvatarInput" />
                </div>
                <div class="flex-1 min-w-0">
                  <p class="text-[16px] font-semibold truncate">{{ displayName }}</p>
                  <p class="text-[12px] text-[#999] mt-1 truncate">{{ auth.user?.email }}</p>
                  <div class="mt-3 flex flex-wrap items-center gap-2">
                    <button class="px-4 py-2 rounded-full text-[12px] font-medium bg-[#111] text-white hover:bg-[#333] cursor-pointer transition-colors" @click="avatarInput?.click()">
                      更换头像
                    </button>
                    <button class="px-4 py-2 rounded-full text-[12px] font-medium bg-[#F3F2EE] text-[#666] hover:text-[#111] transition-colors" @click="saveProfile">保存用户名</button>
                  </div>
                </div>
              </div>

              <div class="space-y-4 pt-4 border-t border-[#F3F2EE]">
                <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                  <span class="text-[13px] text-[#666]">用户名</span>
                  <input v-model="profileForm.username" class="w-full sm:w-64 px-3 py-2 rounded-xl bg-[#FAFAFA] border border-[#E8E6E1] text-[13px] outline-none focus:border-[#111]" />
                </div>
                <div class="flex items-center justify-between">
                  <span class="text-[13px] text-[#666]">邮箱验证状态</span>
                  <span :class="['text-[12px] px-3 py-1 rounded-full font-medium', auth.user?.email_verified ? 'bg-[#E8F5E9] text-[#2E7D32]' : 'bg-[#FFF3E0] text-[#E65100]']">
                    {{ auth.user?.email_verified ? '已验证' : '未验证' }}
                  </span>
                </div>
                <div class="flex items-center justify-between">
                  <span class="text-[13px] text-[#666]">上次登录 IP</span>
                  <span class="text-[12px] text-[#999] font-mono">{{ auth.user?.last_login_ip || '—' }}</span>
                </div>
                <div class="flex items-center justify-between">
                  <span class="text-[13px] text-[#666]">账户 ID</span>
                  <span class="text-[12px] text-[#999] font-mono">#{{ auth.user?.id }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 模型供应商 -->
        <div v-else class="animate-fade-in-up">
          <div class="flex items-start justify-between gap-3 mb-2">
            <div class="min-w-0">
              <h2 class="font-serif text-2xl sm:text-3xl tracking-tight">模型供应商</h2>
              <p class="text-[12px] sm:text-[13px] text-[#999] mt-1">配置你的 AI 模型供应商，支持添加多个并切换启用</p>
            </div>
            <!-- 添加按钮：移动端仅图标 + 较窄内边距，桌面端带文字 -->
            <button
              @click="openCreateDialog"
              class="shrink-0 flex items-center gap-2 px-4 sm:px-5 py-2 sm:py-2.5 bg-[#111] text-white rounded-full text-[13px] font-medium hover:bg-[#333] transition-all shadow-sm hover:shadow-md"
            >
              <el-icon :size="15"><Plus /></el-icon>
              <span class="hidden sm:inline">添加供应商</span>
            </button>
          </div>

          <!-- 配置说明 -->
          <div class="mt-6 mb-8 p-4 bg-[#F3F2EE] rounded-xl border border-[#E8E6E1]/50">
            <p class="text-[12px] text-[#777] leading-relaxed">
              <span class="font-medium text-[#555]">提示：</span>
              每个供应商配置包含 LLM 和 Embedding 模型。启用后，对话与知识库检索将使用该配置。
              同时只能启用一个供应商；如未配置任何供应商，系统将回退到 <code class="px-1 py-0.5 bg-white rounded text-[11px] font-mono">.env</code> 环境变量中的默认配置。
            </p>
          </div>

          <!-- 供应商列表 -->
          <div v-if="loading" class="text-center text-[13px] text-[#999] py-12">加载中…</div>

          <div v-else-if="providers.length === 0" class="text-center py-16">
            <div class="w-16 h-16 rounded-full bg-[#F3F2EE] flex items-center justify-center text-[#CCC] mx-auto mb-4">
              <el-icon :size="28"><Cpu /></el-icon>
            </div>
            <p class="text-[14px] text-[#666] font-medium mb-1">暂无供应商配置</p>
            <p class="text-[12px] text-[#999] mb-6">添加你的第一个 AI 模型供应商以开始对话</p>
            <button
              @click="openCreateDialog"
              class="inline-flex items-center gap-2 px-6 py-2.5 bg-[#111] text-white rounded-full text-[13px] font-medium hover:bg-[#333] transition-all"
            >
              <el-icon :size="15"><Plus /></el-icon>
              <span>添加供应商</span>
            </button>
          </div>

          <!-- 供应商卡片列表：复用 ProviderCard 组件，hover 上浮阴影 + 移动端单列详情 -->
          <div v-else class="space-y-4">
            <ProviderCard
              v-for="p in providers"
              :key="p.id"
              :provider="p"
              @toggle="onToggle"
              @edit="openEditDialog"
              @delete="onDelete"
            />
          </div>
        </div>

      </div>
    </main>

    <!-- 添加/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      :width="isMobile ? '92%' : '560px'"
      class="provider-dialog"
      :close-on-click-modal="false"
    >
      <div class="space-y-5">
        <!-- 快速预设 -->
        <div v-if="!isEditing">
          <label class="block text-[12px] text-[#999] uppercase tracking-wider mb-2">快速选择预设</label>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="preset in presets"
              :key="preset.provider_name"
              @click="applyPreset(preset)"
              class="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[12px] bg-[#F3F2EE] text-[#666] hover:bg-[#111] hover:text-white transition-all"
            >
              <el-icon :size="11"><Star /></el-icon>
              <span>{{ preset.provider_name }}</span>
            </button>
          </div>
        </div>

        <!-- 供应商名称 -->
        <div>
          <label class="block text-[12px] text-[#999] uppercase tracking-wider mb-2">供应商名称</label>
          <input
            v-model="form.provider_name"
            type="text"
            placeholder="如：智谱 GLM"
            class="w-full px-4 py-2.5 bg-[#FAFAFA] border border-[#E8E6E1] rounded-xl text-[14px] outline-none focus:border-[#111] focus:bg-white transition-colors"
          />
        </div>

        <!-- API Key -->
        <div>
          <label class="block text-[12px] text-[#999] uppercase tracking-wider mb-2">
            API Key
            <span v-if="isEditing" class="text-[#BBB] normal-case tracking-normal ml-1">（留空表示不修改）</span>
          </label>
          <div class="relative">
            <input
              v-model="form.llm_api_key"
              :type="showApiKey ? 'text' : 'password'"
              :placeholder="isEditing ? '••••••••（不修改请留空）' : '请输入 API Key'"
              class="w-full px-4 py-2.5 pr-11 bg-[#FAFAFA] border border-[#E8E6E1] rounded-xl text-[14px] font-mono outline-none focus:border-[#111] focus:bg-white transition-colors"
            />
            <button
              @click="showApiKey = !showApiKey"
              class="absolute right-3 top-1/2 -translate-y-1/2 text-[#999] hover:text-[#111] transition-colors"
            >
              <el-icon :size="16"><component :is="showApiKey ? View : Hide" /></el-icon>
            </button>
          </div>
        </div>

        <!-- Base URL -->
        <div>
          <label class="block text-[12px] text-[#999] uppercase tracking-wider mb-2">Base URL</label>
          <input
            v-model="form.llm_base_url"
            type="text"
            placeholder="https://api.openai.com/v1"
            class="w-full px-4 py-2.5 bg-[#FAFAFA] border border-[#E8E6E1] rounded-xl text-[14px] font-mono outline-none focus:border-[#111] focus:bg-white transition-colors"
          />
        </div>

        <!-- 双列：LLM 模型 + Embedding 模型（移动端单列） -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="block text-[12px] text-[#999] uppercase tracking-wider mb-2">LLM 模型</label>
            <input
              v-model="form.llm_model"
              type="text"
              placeholder="glm-4.5-air"
              class="w-full px-4 py-2.5 bg-[#FAFAFA] border border-[#E8E6E1] rounded-xl text-[14px] font-mono outline-none focus:border-[#111] focus:bg-white transition-colors"
            />
          </div>
          <div>
            <label class="block text-[12px] text-[#999] uppercase tracking-wider mb-2">Embedding 模型</label>
            <input
              v-model="form.embedding_model"
              type="text"
              placeholder="embedding-3"
              class="w-full px-4 py-2.5 bg-[#FAFAFA] border border-[#E8E6E1] rounded-xl text-[14px] font-mono outline-none focus:border-[#111] focus:bg-white transition-colors"
            />
          </div>
        </div>

        <!-- Embedding 维度 -->
        <div>
          <label class="block text-[12px] text-[#999] uppercase tracking-wider mb-2">Embedding 维度</label>
          <input
            v-model.number="form.embedding_dim"
            type="number"
            min="1"
            max="8192"
            placeholder="1024"
            class="w-full px-4 py-2.5 bg-[#FAFAFA] border border-[#E8E6E1] rounded-xl text-[14px] font-mono outline-none focus:border-[#111] focus:bg-white transition-colors"
          />
          <p class="text-[11px] text-[#BBB] mt-1.5">常见值：OpenAI 1536 / 智谱 2048 / 百炼 1024</p>
        </div>
      </div>

      <template #footer>
        <div class="flex items-center justify-end gap-3 pt-2">
          <button
            @click="dialogVisible = false"
            class="px-5 py-2 rounded-full text-[13px] text-[#666] hover:text-[#111] hover:bg-[#F3F2EE] transition-colors"
          >
            取消
          </button>
          <button
            @click="onSave"
            :disabled="saving"
            class="flex items-center gap-2 px-6 py-2 rounded-full text-[13px] font-medium bg-[#111] text-white hover:bg-[#333] transition-all disabled:opacity-50"
          >
            <el-icon :size="14"><Check /></el-icon>
            <span>{{ saving ? '保存中…' : '保存' }}</span>
          </button>
        </div>
      </template>
    </el-dialog>

  </div>
</template>

<style scoped>
/* 弹窗标题样式 */
:deep(.provider-dialog .el-dialog__header) {
  padding: 24px 28px 0;
  margin-bottom: 0;
}
:deep(.provider-dialog .el-dialog__title) {
  font-size: 18px;
  font-weight: 600;
  color: #111;
}
:deep(.provider-dialog .el-dialog__body) {
  padding: 20px 28px;
}
:deep(.provider-dialog .el-dialog__footer) {
  padding: 0 28px 24px;
}
:deep(.provider-dialog .el-dialog) {
  border-radius: 20px;
  overflow: hidden;
}
</style>
