<script setup lang="ts">
import { ref, reactive } from 'vue'
import { Send, Eye, EyeOff } from '@element-plus/icons-vue'

const props = defineProps<{
  props: {
    title?: string
    fields?: Array<{
      type: 'input' | 'select' | 'textarea' | 'checkbox' | 'radio' | 'password'
      label: string
      name: string
      placeholder?: string
      options?: Array<{ label: string; value: string }>
      required?: boolean
      default?: string | boolean
    }>
    submitText?: string
  }
}>()

const emit = defineEmits<{
  (e: 'submit', payload: Record<string, any>): void
}>()

const formData = reactive<Record<string, any>>({})
const showPassword = reactive<Record<string, boolean>>({})
const errors = reactive<Record<string, string>>({})

// 初始化表单数据
props.props.fields?.forEach(field => {
  if (field.type === 'checkbox') {
    formData[field.name] = field.default || false
  } else {
    formData[field.name] = field.default || ''
  }
})

function togglePassword(fieldName: string) {
  showPassword[fieldName] = !showPassword[fieldName]
}

function validate(): boolean {
  let isValid = true
  Object.keys(errors).forEach(key => delete errors[key])
  
  props.props.fields?.forEach(field => {
    if (field.required && !formData[field.name]) {
      errors[field.name] = `${field.label} 必填`
      isValid = false
    }
  })
  return isValid
}

function handleSubmit() {
  if (validate()) {
    emit('submit', { ...formData })
    // 重置表单
    props.props.fields?.forEach(field => {
      if (field.type === 'checkbox') {
        formData[field.name] = false
      } else {
        formData[field.name] = ''
      }
    })
  }
}
</script>

<template>
  <div class="rounded-2xl bg-white border border-[#E8E6E1] p-5 shadow-[0_2px_12px_rgb(0,0,0,0.03)]">
    <h3 v-if="props.title" class="font-serif text-lg text-[#111] mb-4">{{ props.title }}</h3>
    
    <form @submit.prevent="handleSubmit" class="space-y-4">
      <template v-for="field in props.fields" :key="field.name">
        <!-- 输入框 -->
        <div v-if="field.type === 'input'" class="space-y-1.5">
          <label class="flex items-center gap-1.5 text-sm text-[#333]">
            {{ field.label }}
            <span v-if="field.required" class="text-[#EF4444]">*</span>
          </label>
          <el-input
            v-model="formData[field.name]"
            :placeholder="field.placeholder"
            :error="errors[field.name]"
            class="w-full"
          />
          <p v-if="errors[field.name]" class="text-xs text-[#EF4444]">{{ errors[field.name] }}</p>
        </div>

        <!-- 密码框 -->
        <div v-else-if="field.type === 'password'" class="space-y-1.5">
          <label class="flex items-center gap-1.5 text-sm text-[#333]">
            {{ field.label }}
            <span v-if="field.required" class="text-[#EF4444]">*</span>
          </label>
          <el-input
            v-model="formData[field.name]"
            :type="showPassword[field.name] ? 'text' : 'password'"
            :placeholder="field.placeholder"
            :error="errors[field.name]"
            class="w-full"
          >
            <template #suffix>
              <el-button text @click="togglePassword(field.name)">
                <el-icon><EyeOff v-if="showPassword[field.name]" /><Eye v-else /></el-icon>
              </el-button>
            </template>
          </el-input>
          <p v-if="errors[field.name]" class="text-xs text-[#EF4444]">{{ errors[field.name] }}</p>
        </div>

        <!-- 选择器 -->
        <div v-else-if="field.type === 'select'" class="space-y-1.5">
          <label class="flex items-center gap-1.5 text-sm text-[#333]">
            {{ field.label }}
            <span v-if="field.required" class="text-[#EF4444]">*</span>
          </label>
          <el-select
            v-model="formData[field.name]"
            :placeholder="field.placeholder"
            :error="errors[field.name]"
            class="w-full"
          >
            <el-option
              v-for="opt in field.options"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
          <p v-if="errors[field.name]" class="text-xs text-[#EF4444]">{{ errors[field.name] }}</p>
        </div>

        <!-- 文本域 -->
        <div v-else-if="field.type === 'textarea'" class="space-y-1.5">
          <label class="flex items-center gap-1.5 text-sm text-[#333]">
            {{ field.label }}
            <span v-if="field.required" class="text-[#EF4444]">*</span>
          </label>
          <el-textarea
            v-model="formData[field.name]"
            :placeholder="field.placeholder"
            :rows="4"
            :error="errors[field.name]"
            class="w-full"
          />
          <p v-if="errors[field.name]" class="text-xs text-[#EF4444]">{{ errors[field.name] }}</p>
        </div>

        <!-- 复选框 -->
        <div v-else-if="field.type === 'checkbox'" class="flex items-center gap-2">
          <el-checkbox v-model="formData[field.name]" />
          <label class="text-sm text-[#333]">{{ field.label }}</label>
        </div>

        <!-- 单选框 -->
        <div v-else-if="field.type === 'radio'" class="space-y-2">
          <label class="flex items-center gap-1.5 text-sm text-[#333]">
            {{ field.label }}
            <span v-if="field.required" class="text-[#EF4444]">*</span>
          </label>
          <div class="flex flex-wrap gap-4">
            <label
              v-for="opt in field.options"
              :key="opt.value"
              class="flex items-center gap-1.5 cursor-pointer"
            >
              <el-radio v-model="formData[field.name]" :value="opt.value" />
              <span class="text-sm text-[#333]">{{ opt.label }}</span>
            </label>
          </div>
        </div>
      </template>

      <el-button
        type="primary"
        class="w-full"
        @click="handleSubmit"
      >
        <el-icon class="mr-1.5"><Send /></el-icon>
        {{ props.submitText || '提交' }}
      </el-button>
    </form>
  </div>
</template>