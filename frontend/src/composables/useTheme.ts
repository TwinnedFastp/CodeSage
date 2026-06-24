import { ref, computed, onMounted, onUnmounted } from 'vue'

/**
 * 主题管理 Composable
 * 支持 light / dark / system 三种模式
 * 持久化到 localStorage（key: codesage-theme）
 */
type Theme = 'light' | 'dark' | 'system'

const STORAGE_KEY = 'codesage-theme'
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)')

const theme = ref<Theme>(loadStoredTheme())
const systemIsDark = ref(prefersDark.matches)

let mediaWatcher: MediaQueryList | null = null

/** 读取 localStorage 中的主题偏好（无则默认 system） */
function loadStoredTheme(): Theme {
  const stored = localStorage.getItem(STORAGE_KEY)
  if (stored === 'light' || stored === 'dark' || stored === 'system') return stored
  return 'system'
}

/** 应用主题到 DOM：设置 <html data-theme> + class="dark"（驱动 Element Plus 暗黑模式） */
function applyTheme(value: Theme) {
  const root = document.documentElement
  if (value === 'system') {
    const dark = systemIsDark.value
    root.dataset.theme = dark ? 'dark' : 'light'
    root.classList.toggle('dark', dark)
  } else {
    root.dataset.theme = value
    root.classList.toggle('dark', value === 'dark')
  }
}

/** 切换主题时添加过渡 class，结束后移除（避免日常动画受影响） */
function enableTransition() {
  document.documentElement.classList.add('theme-transition')
  // 过渡结束后移除，避免影响高性能场景（如流式打字）
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      document.documentElement.classList.remove('theme-transition')
    })
  })
}

export function useTheme() {
  /** 切换主题 */
  function setTheme(value: Theme) {
    theme.value = value
    localStorage.setItem(STORAGE_KEY, value)
    enableTransition()
    applyTheme(value)
  }

  /** 切换到下一个模式：light → dark → system → light */
  function toggleNext() {
    const cycle: Theme[] = ['light', 'dark', 'system']
    const idx = cycle.indexOf(theme.value)
    setTheme(cycle[(idx + 1) % cycle.length])
  }

  /** 当前是否是暗色 */
  const isDark = computed(() => {
    if (theme.value === 'system') return systemIsDark.value
    return theme.value === 'dark'
  })

  /** 当前主题标签（用于 UI 展示） */
  const themeLabel = computed(() => {
    return { light: '浅色', dark: '暗色', system: '跟随系统' }[theme.value]
  })

  // 初始化时应用一次
  applyTheme(theme.value)

  onMounted(() => {
    // 监听系统主题变化（仅 system 模式需要）
    mediaWatcher = prefersDark
    mediaWatcher.onchange = (e: MediaQueryListEvent) => {
      systemIsDark.value = e.matches
      if (theme.value === 'system') {
        applyTheme('system')
      }
    }
  })

  onUnmounted(() => {
    if (mediaWatcher) {
      mediaWatcher.onchange = null
    }
  })

  return {
    theme,
    isDark,
    themeLabel,
    setTheme,
    toggleNext,
  }
}
