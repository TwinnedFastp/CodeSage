<script setup lang="ts">
import { ref } from 'vue'
import Vcode from 'vue3-puzzle-vcode'
import 'vue3-puzzle-vcode/css'
import { Lock, Check } from '@element-plus/icons-vue'

/**
 * 极简杂志风拼图验证码
 * - 内联触发器：未验证时可点击唤起拼图模态框
 * - 验证通过后变为「✓ 验证通过」状态，并向父级 emit verified
 */
const emit = defineEmits<{
  (e: 'verified', value: boolean): void
}>()

const show = ref(false)
const verified = ref(false)

function open() {
  if (verified.value) return
  show.value = true
}

function onSuccess() {
  verified.value = true
  show.value = false
  emit('verified', true)
}

function onClose() {
  show.value = false
}

function onFail() {
  // 验证失败保持未通过状态，组件内部会自动重置拼图
}

defineExpose({
  reset() {
    verified.value = false
    emit('verified', false)
  },
})
</script>

<template>
  <div
    class="puzzle-verify"
    :class="{ 'is-verified': verified }"
    role="button"
    tabindex="0"
    @click="open"
    @keyup.enter="open"
  >
    <span class="pv-icon">
      <el-icon v-if="verified" :size="15"><Check /></el-icon>
      <el-icon v-else :size="15"><Lock /></el-icon>
    </span>
    <span class="pv-text">{{ verified ? '验证通过' : '点击完成拼图验证' }}</span>
    <span v-if="!verified" class="pv-hint">人机验证</span>
  </div>

  <Vcode
    :show="show"
    class-name="codesage-puzzle"
    :canvas-width="310"
    :canvas-height="160"
    success-text="验证通过"
    fail-text="验证失败，请重试"
    slider-text="拖动滑块完成拼图"
    @success="onSuccess"
    @fail="onFail"
    @close="onClose"
  />
</template>

<style scoped>
.puzzle-verify {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  height: 48px;
  padding: 0 16px;
  border: 1px solid #e8e6e1;
  border-radius: 14px;
  background: #ffffff;
  cursor: pointer;
  transition: all 0.25s ease;
  user-select: none;
}
.puzzle-verify:hover {
  border-color: #111111;
}
.puzzle-verify:focus-visible {
  outline: none;
  border-color: #111111;
  box-shadow: 0 0 0 3px #11111114;
}
.puzzle-verify.is-verified {
  border-color: #111111;
  background: #111111;
  cursor: default;
}
.pv-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #999999;
  transition: color 0.25s ease;
}
.puzzle-verify:hover .pv-icon {
  color: #111111;
}
.is-verified .pv-icon {
  color: #f3f2ee;
}
.pv-text {
  font-size: 13.5px;
  color: #777777;
  letter-spacing: 0.01em;
  transition: color 0.25s ease;
}
.puzzle-verify:hover .pv-text {
  color: #111111;
}
.is-verified .pv-text {
  color: #f3f2ee;
  font-weight: 500;
}
.pv-hint {
  margin-left: auto;
  font-size: 11px;
  color: #b0b0b0;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.is-verified .pv-hint {
  display: none;
}
</style>

<!-- 模态框主题化：覆盖 vue3-puzzle-vcode 默认蓝绿配色为极简杂志风 -->
<style>
.codesage-puzzle .vue-auth-box_ {
  border-radius: 18px;
  padding: 24px;
  box-shadow: 0 24px 60px -12px #11111140;
  background: #fafafa;
}
.codesage-puzzle .auth-body_ {
  border-radius: 12px;
}
/* 成功/失败提示条 */
.codesage-puzzle .info-box_ {
  background-color: #111111 !important;
  font-size: 12px;
  letter-spacing: 0.04em;
}
.codesage-puzzle .info-box_.fail {
  background-color: #c0564a !important;
}
/* 滑动轨道 */
.codesage-puzzle .range-box {
  background-color: #f3f2ee !important;
  border-radius: 10px !important;
  box-shadow: none !important;
  height: 44px;
}
.codesage-puzzle .range-text {
  color: #b0b0b0 !important;
  font-size: 13px !important;
}
/* 已滑动填充 */
.codesage-puzzle .range-slider {
  background-color: #1111111a !important;
  border-radius: 10px !important;
}
.codesage-puzzle .range-slider .range-btn {
  border-radius: 10px !important;
  box-shadow: 0 1px 4px #11111126 !important;
}
.codesage-puzzle .range-slider .range-btn > div {
  border-color: #111111 !important;
}
.codesage-puzzle .range-slider .range-btn:hover > div:first-child,
.codesage-puzzle .range-slider .range-btn.isDown > div:first-child {
  border-right-color: #111111 !important;
}
.codesage-puzzle .range-slider .range-btn:hover > div:nth-child(2),
.codesage-puzzle .range-slider .range-btn.isDown > div:nth-child(2) {
  border-color: #111111 !important;
  border-right-color: #111111 !important;
}
.codesage-puzzle .range-slider .range-btn:hover > div:nth-child(3),
.codesage-puzzle .range-slider .range-btn.isDown > div:nth-child(3) {
  border-left-color: #111111 !important;
}
/* 遮罩层柔化 */
.codesage-puzzle.vue-puzzle-vcode {
  background-color: #11111166 !important;
}
</style>
