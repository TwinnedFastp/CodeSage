/**
 * 响应式布局：移动端检测 + 侧边栏折叠 + 抽屉
 */
import { ref, onMounted, onBeforeUnmount } from 'vue'

export function useResponsive() {
  const isMobile = ref(false)
  const isSidebarCollapse = ref(false)
  const drawerVisible = ref(false)

  const checkMobile = () => { isMobile.value = window.innerWidth < 768 }

  onMounted(() => {
    checkMobile()
    window.addEventListener('resize', checkMobile)
  })

  onBeforeUnmount(() => {
    window.removeEventListener('resize', checkMobile)
  })

  return { isMobile, isSidebarCollapse, drawerVisible }
}
