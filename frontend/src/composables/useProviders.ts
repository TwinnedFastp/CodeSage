/**
 * AI 供应商配置管理：列表 / 新增 / 编辑 / 删除 / 启用切换
 */
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as providersApi from '@/api/providers'
import type { Provider, ProviderCreateInput, ProviderUpdateInput } from '@/api/providers'

export function useProviders() {
  const providers = ref<Provider[]>([])
  const loading = ref(false)
  const saving = ref(false)

  // 常见的供应商预设（参考 Dify / LightRAG 配置风格）
  const presets = [
    {
      provider_name: '智谱 GLM',
      llm_base_url: 'https://open.bigmodel.cn/api/paas/v4',
      llm_model: 'glm-4.5-air',
      embedding_model: 'embedding-3',
      embedding_dim: 2048,
    },
    {
      provider_name: '阿里百炼',
      llm_base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
      llm_model: 'qwen-plus',
      embedding_model: 'text-embedding-v4',
      embedding_dim: 1024,
    },
    {
      provider_name: 'OpenAI',
      llm_base_url: 'https://api.openai.com/v1',
      llm_model: 'gpt-4o',
      embedding_model: 'text-embedding-3-small',
      embedding_dim: 1536,
    },
    {
      provider_name: 'DeepSeek',
      llm_base_url: 'https://api.deepseek.com/v1',
      llm_model: 'deepseek-chat',
      embedding_model: 'deepseek-chat',
      embedding_dim: 1024,
    },
    {
      provider_name: 'OpenRouter',
      llm_base_url: 'https://openrouter.ai/api/v1',
      llm_model: 'anthropic/claude-3.5-sonnet',
      embedding_model: 'openai/text-embedding-3-small',
      embedding_dim: 1536,
    },
  ]

  async function loadProviders() {
    loading.value = true
    try {
      providers.value = await providersApi.listProviders()
    } catch (err: any) {
      ElMessage.error(err.response?.data?.message || '加载供应商配置失败')
    } finally {
      loading.value = false
    }
  }

  async function createProvider(data: ProviderCreateInput): Promise<boolean> {
    saving.value = true
    try {
      await providersApi.createProvider(data)
      ElMessage.success('供应商配置已添加')
      await loadProviders()
      return true
    } catch (err: any) {
      ElMessage.error(err.response?.data?.message || '添加供应商失败')
      return false
    } finally {
      saving.value = false
    }
  }

  async function updateProvider(id: number, data: ProviderUpdateInput): Promise<boolean> {
    saving.value = true
    try {
      await providersApi.updateProvider(id, data)
      ElMessage.success('供应商配置已更新')
      await loadProviders()
      return true
    } catch (err: any) {
      ElMessage.error(err.response?.data?.message || '更新供应商失败')
      return false
    } finally {
      saving.value = false
    }
  }

  async function deleteProvider(id: number): Promise<boolean> {
    try {
      await ElMessageBox.confirm(
        '删除后该供应商配置将无法恢复，确定继续吗？',
        '删除供应商',
        {
          type: 'warning',
          confirmButtonText: '删除',
          cancelButtonText: '取消',
          confirmButtonClass: 'el-button--danger',
        },
      )
    } catch {
      return false
    }

    try {
      await providersApi.deleteProvider(id)
      ElMessage.success('已删除')
      await loadProviders()
      return true
    } catch (err: any) {
      ElMessage.error(err.response?.data?.message || '删除失败')
      return false
    }
  }

  async function toggleProvider(id: number): Promise<boolean> {
    try {
      await providersApi.toggleProvider(id)
      await loadProviders()
      return true
    } catch (err: any) {
      ElMessage.error(err.response?.data?.message || '切换状态失败')
      return false
    }
  }

  onMounted(() => { loadProviders() })

  return {
    providers, loading, saving, presets,
    loadProviders, createProvider, updateProvider, deleteProvider, toggleProvider,
  }
}
