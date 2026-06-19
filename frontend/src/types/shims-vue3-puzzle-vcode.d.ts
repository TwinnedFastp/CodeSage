/**
 * vue3-puzzle-vcode 类型声明
 * 该库 package.json 的 exports 字段未正确暴露 typings，
 * 因此这里手写一份与组件 Props/Events 对齐的声明。
 */
declare module 'vue3-puzzle-vcode' {
  import type { DefineComponent } from 'vue'

  interface VcodeProps {
    /** 是否显示验证码弹框 */
    show?: boolean
    /** "modal" 模态框形式 / "inside" 内嵌形式 */
    type?: 'modal' | 'inside'
    /** 主图区域宽度 px */
    canvasWidth?: number
    /** 主图区域高度 px */
    canvasHeight?: number
    /** 拼图块大小比例 0.2~2 */
    puzzleScale?: number
    /** 左下角滑块尺寸 px */
    sliderSize?: number
    /** 判断成功的误差范围 px */
    range?: number
    /** 自定义图片 */
    imgs?: unknown[]
    /** 验证成功提示文字 */
    successText?: string
    /** 验证失败提示文字 */
    failText?: string
    /** 滑动条文字 */
    sliderText?: string
    /** 根元素自定义 class */
    className?: string
    /** 层级 z-index */
    zIndex?: number
  }

  const Vcode: DefineComponent<VcodeProps>
  export default Vcode
}

declare module 'vue3-puzzle-vcode/css'
