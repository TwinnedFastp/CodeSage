<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Coin, RefreshRight, Plus, Edit, Delete, Search,
  ArrowLeft, Monitor,
} from '@element-plus/icons-vue'
import { useDatabaseAdmin } from '@/features/database-admin/useDatabaseAdmin'

const router = useRouter()
const {
  tables, selectedTable, selectedMeta, rowData, columns, primaryKeys, rows, total,
  loadingTables, loadingRows, saving, pageSize, currentPage, searchText,
  editorVisible, editorMode, form,
  loadTables, loadRows, selectTable, openCreate, openEdit, saveRow, removeRow,
  formatCell,
} = useDatabaseAdmin()

const tableCount = computed(() => tables.value.length)
const currentRowCount = computed(() => rowData.value?.total ?? selectedMeta.value?.row_count ?? 0)
const currentColumnCount = computed(() => columns.value.length)
const currentPkCount = computed(() => primaryKeys.value.length)

function goChat() {
  router.push('/chat')
}

function goSettings() {
  router.push('/settings')
}

async function refreshAll() {
  await loadTables()
  await loadRows()
  ElMessage.success('已刷新数据库视图')
}

async function onSearch() {
  await loadRows(true)
}

async function onPageChange(page: number) {
  currentPage.value = page
  await loadRows()
}

async function onSizeChange(size: number) {
  pageSize.value = size
  currentPage.value = 1
  await loadRows()
}

function isBooleanColumn(type: string) {
  return type === 'boolean'
}

function isNumberColumn(type: string) {
  return ['integer', 'bigint', 'smallint', 'numeric', 'real', 'double precision'].includes(type)
}

function isJsonColumn(type: string) {
  return ['json', 'jsonb'].includes(type)
}

function isDateColumn(type: string) {
  return ['timestamp without time zone', 'timestamp with time zone', 'date'].includes(type)
}

onMounted(() => {
  loadTables()
})
</script>

<template>
  <div class="flex h-screen w-screen bg-[#FAFAFA] text-[#111111] overflow-hidden font-sans">
    <!-- 左侧数据库目录 -->
    <aside class="w-[300px] bg-[#F3F2EE] border-r border-[#E8E6E1] flex flex-col shrink-0">
      <div class="p-6 flex items-center justify-between h-20">
        <div class="flex items-center gap-3">
          <div class="w-7 h-7 rounded-full bg-[#111111] text-white flex items-center justify-center">
            <el-icon :size="14"><Coin /></el-icon>
          </div>
          <div>
            <h1 class="font-serif text-[20px] tracking-tight">数据库管理</h1>
            <p class="text-[11px] text-[#999]">PostgreSQL 表数据 CRUD</p>
          </div>
        </div>
        <button @click="goChat" class="p-2 rounded-full hover:bg-white/80 transition-colors text-[#555]" title="返回聊天">
          <el-icon :size="18"><ArrowLeft /></el-icon>
        </button>
      </div>

      <!-- 小图标目录 -->
      <div class="px-5 pb-4">
        <div class="grid grid-cols-3 gap-2 p-2 rounded-2xl bg-white border border-[#E8E6E1] shadow-[0_4px_20px_rgb(0,0,0,0.04)]">
          <button class="flex flex-col items-center justify-center gap-1 py-3 rounded-xl bg-[#111] text-white shadow-sm" title="数据库管���">
            <el-icon :size="16"><Coin /></el-icon>
            <span class="text-[10px]">数据库</span>
          </button>
          <button @click="goChat" class="flex flex-col items-center justify-center gap-1 py-3 rounded-xl text-[#666] hover:bg-[#F3F2EE] transition-colors" title="返回聊天">
            <el-icon :size="16"><Monitor /></el-icon>
            <span class="text-[10px]">聊天</span>
          </button>
          <button @click="goSettings" class="flex flex-col items-center justify-center gap-1 py-3 rounded-xl text-[#666] hover:bg-[#F3F2EE] transition-colors" title="系统设置">
            <el-icon :size="16"><RefreshRight /></el-icon>
            <span class="text-[10px]">设置</span>
          </button>
        </div>
      </div>

      <div class="px-5 pb-4">
        <button
          @click="refreshAll"
          class="w-full h-11 bg-[#111111] hover:bg-[#333333] text-white rounded-full flex items-center justify-center gap-2 transition-all duration-300 shadow-sm"
        >
          <el-icon><RefreshRight /></el-icon>
          <span class="text-sm font-medium">刷新元数据</span>
        </button>
      </div>

      <div class="px-5 mb-3">
        <div class="text-[12px] text-[#999] uppercase tracking-[0.18em] mb-2">数据库表</div>
        <div class="text-[11px] text-[#BBB] mb-3">点击表名即可查看 / 新增 / 编辑 / 删除记录</div>
      </div>

      <div class="flex-1 overflow-y-auto px-3 pb-4 custom-scrollbar space-y-1">
        <div v-if="loadingTables" class="px-4 py-4 text-[12px] text-[#999]">加载表结构中…</div>
        <button
          v-for="table in tables"
          :key="table.name"
          @click="selectTable(table.name)"
          :class="[
            'w-full text-left px-4 py-3 rounded-xl border transition-all',
            selectedTable === table.name
              ? 'bg-white border-[#111] shadow-[0_8px_24px_rgb(0,0,0,0.08)]'
              : 'bg-transparent border-transparent hover:bg-white hover:border-[#E8E6E1]',
          ]"
        >
          <div class="flex items-start justify-between gap-2">
            <div class="min-w-0">
              <div class="font-medium text-[13px] truncate">{{ table.name }}</div>
              <div class="text-[11px] text-[#999] mt-1">
                <span>{{ table.row_count ?? 0 }} 行</span>
                <span class="mx-1.5">·</span>
                <span>{{ table.columns.length }} 列</span>
              </div>
            </div>
            <el-icon :size="14" class="text-[#BBB] shrink-0"><Monitor /></el-icon>
          </div>
        </button>
        <div v-if="!loadingTables && tables.length === 0" class="px-4 py-10 text-center text-[12px] text-[#999]">
          当前数据库暂无可管理的表
        </div>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="flex-1 overflow-y-auto custom-scrollbar">
      <div class="max-w-[1400px] mx-auto px-4 sm:px-8 py-6 sm:py-8">
        <!-- 头部 -->
        <div class="flex items-start justify-between gap-4 mb-6">
          <div>
            <h2 class="font-serif text-3xl tracking-tight">{{ selectedTable || '请选择一张表' }}</h2>
            <p class="text-[13px] text-[#999] mt-1">像若依那样管理表数据，但保持 CodeSage 的杂志风视觉。</p>
          </div>
          <div class="flex items-center gap-2">
            <button @click="goChat" class="px-4 py-2 rounded-full text-[13px] text-[#666] hover:text-[#111] hover:bg-[#F3F2EE] transition-colors">
              返回聊天
            </button>
            <button @click="openCreate" :disabled="!selectedTable" class="px-4 py-2 rounded-full text-[13px] font-medium bg-[#111] text-white hover:bg-[#333] transition-colors disabled:opacity-40 disabled:cursor-not-allowed">
              <span class="inline-flex items-center gap-2"><Plus :size="14" />新增记录</span>
            </button>
          </div>
        </div>

        <!-- 概览卡 -->
        <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
          <div class="bg-white border border-[#E8E6E1] rounded-2xl p-4 shadow-[0_6px_24px_rgb(0,0,0,0.04)]">
            <div class="text-[11px] text-[#999] uppercase tracking-[0.18em]">表数量</div>
            <div class="mt-2 text-2xl font-semibold">{{ tableCount }}</div>
          </div>
          <div class="bg-white border border-[#E8E6E1] rounded-2xl p-4 shadow-[0_6px_24px_rgb(0,0,0,0.04)]">
            <div class="text-[11px] text-[#999] uppercase tracking-[0.18em]">当前表行数</div>
            <div class="mt-2 text-2xl font-semibold">{{ currentRowCount }}</div>
          </div>
          <div class="bg-white border border-[#E8E6E1] rounded-2xl p-4 shadow-[0_6px_24px_rgb(0,0,0,0.04)]">
            <div class="text-[11px] text-[#999] uppercase tracking-[0.18em]">字段数</div>
            <div class="mt-2 text-2xl font-semibold">{{ currentColumnCount }}</div>
          </div>
          <div class="bg-white border border-[#E8E6E1] rounded-2xl p-4 shadow-[0_6px_24px_rgb(0,0,0,0.04)]">
            <div class="text-[11px] text-[#999] uppercase tracking-[0.18em]">主键数</div>
            <div class="mt-2 text-2xl font-semibold">{{ currentPkCount }}</div>
          </div>
        </div>

        <!-- 过滤条 -->
        <div class="bg-white border border-[#E8E6E1] rounded-2xl p-4 mb-6 shadow-[0_6px_24px_rgb(0,0,0,0.04)]">
          <div class="flex flex-col lg:flex-row lg:items-center gap-3">
            <div class="flex-1 flex items-center gap-2 px-4 py-2.5 rounded-full border border-[#E8E6E1] bg-[#FAFAFA]">
              <el-icon :size="16" class="text-[#999]"><Search /></el-icon>
              <input
                v-model="searchText"
                @keyup.enter="onSearch"
                class="w-full bg-transparent outline-none text-[14px]"
                placeholder="搜索文本列内容"
              />
            </div>
            <div class="flex items-center gap-2 ml-auto">
              <button @click="loadRows(true)" class="px-4 py-2.5 rounded-full text-[13px] text-[#666] hover:text-[#111] hover:bg-[#F3F2EE] transition-colors">重置</button>
              <button @click="onSearch" class="px-4 py-2.5 rounded-full text-[13px] font-medium bg-[#111] text-white hover:bg-[#333] transition-colors">查询</button>
            </div>
          </div>
        </div>

        <!-- 数据表格 -->
        <div class="bg-white border border-[#E8E6E1] rounded-2xl overflow-hidden shadow-[0_10px_30px_rgb(0,0,0,0.04)]">
          <div v-if="!selectedTable" class="p-12 text-center text-[#999]">
            请选择左侧的一张表开始管理数据
          </div>
          <template v-else>
            <el-table
              v-loading="loadingRows"
              :data="rows"
              border
              stripe
              style="width: 100%"
              class="database-table"
            >
              <el-table-column
                v-for="col in columns"
                :key="col.name"
                :prop="col.name"
                :label="col.name"
                min-width="180"
                show-overflow-tooltip
              >
                <template #default="scope">
                  <span class="font-mono text-[12px] text-[#333]">{{ formatCell(scope.row[col.name]) }}</span>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="180" fixed="right">
                <template #default="scope">
                  <div class="flex items-center gap-2">
                    <button @click="openEdit(scope.row)" class="px-3 py-1.5 rounded-full text-[12px] text-[#666] hover:text-[#111] hover:bg-[#F3F2EE] transition-colors inline-flex items-center gap-1">
                      <el-icon :size="12"><Edit /></el-icon><span>编辑</span>
                    </button>
                    <button @click="removeRow(scope.row)" class="px-3 py-1.5 rounded-full text-[12px] text-[#666] hover:text-[#D32F2F] hover:bg-[#FFEBEE] transition-colors inline-flex items-center gap-1">
                      <el-icon :size="12"><Delete /></el-icon><span>删除</span>
                    </button>
                  </div>
                </template>
              </el-table-column>
            </el-table>

            <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-3 px-4 py-4 border-t border-[#F3F2EE]">
              <div class="text-[12px] text-[#999]">
                当前第 {{ currentPage }} 页，共 {{ total }} 条记录
              </div>
              <el-pagination
                layout="prev, pager, next, sizes, jumper"
                :total="total"
                :page-size="pageSize"
                :current-page="currentPage"
                :page-sizes="[20, 50, 100, 200]"
                background
                small
                @current-change="onPageChange"
                @size-change="onSizeChange"
              />
            </div>
          </template>
        </div>
      </div>
    </main>

    <!-- 新增 / 编辑抽屉 -->
    <el-drawer
      v-model="editorVisible"
      :title="editorMode === 'create' ? '新增记录' : '编辑记录'"
      direction="rtl"
      size="520px"
      :with-header="true"
      class="database-editor-drawer"
    >
      <div class="px-1">
        <div class="mb-4 text-[12px] text-[#999] leading-relaxed">
          {{ selectedTable }} · {{ editorMode === 'create' ? '填写字段后提交插入' : '修改字段后提交更新' }}
        </div>

        <div class="space-y-4 max-h-[calc(100vh-180px)] overflow-y-auto pr-1 custom-scrollbar">
          <div v-for="col in columns" :key="col.name" class="space-y-2">
            <label class="block text-[12px] text-[#999] uppercase tracking-wider">
              {{ col.name }}
              <span v-if="col.is_primary_key" class="ml-1 text-[#D32F2F]">PK</span>
              <span v-if="col.column_default" class="ml-1 text-[#BBB] normal-case tracking-normal">默认值：{{ col.column_default }}</span>
            </label>

            <el-input-number
              v-if="isNumberColumn(col.data_type)"
              v-model="form[col.name]"
              class="w-full"
              :disabled="editorMode === 'edit' && col.is_primary_key"
              :controls="false"
              :placeholder="col.name"
            />
            <el-switch
              v-else-if="isBooleanColumn(col.data_type)"
              v-model="form[col.name]"
              :disabled="editorMode === 'edit' && col.is_primary_key"
              inline-prompt
              active-text="true"
              inactive-text="false"
            />
            <el-input
              v-else-if="isJsonColumn(col.data_type)"
              v-model="form[col.name]"
              type="textarea"
              :rows="5"
              :disabled="editorMode === 'edit' && col.is_primary_key"
              placeholder='{"key":"value"}'
            />
            <el-input
              v-else-if="isDateColumn(col.data_type)"
              v-model="form[col.name]"
              :disabled="editorMode === 'edit' && col.is_primary_key"
              placeholder="2026-06-22 10:00:00"
            />
            <el-input
              v-else
              v-model="form[col.name]"
              :disabled="editorMode === 'edit' && col.is_primary_key"
              :type="col.name.includes('password') || col.name.includes('secret') ? 'password' : 'text'"
              :placeholder="col.is_primary_key && editorMode === 'edit' ? '主键不可编辑' : col.name"
            />
          </div>
        </div>

        <div class="flex items-center justify-end gap-3 pt-5 mt-5 border-t border-[#F3F2EE]">
          <button
            @click="editorVisible = false"
            class="px-5 py-2 rounded-full text-[13px] text-[#666] hover:text-[#111] hover:bg-[#F3F2EE] transition-colors"
          >
            取消
          </button>
          <button
            @click="saveRow"
            :disabled="saving"
            class="px-6 py-2 rounded-full text-[13px] font-medium bg-[#111] text-white hover:bg-[#333] transition-colors disabled:opacity-50"
          >
            {{ saving ? '保存中…' : '保存' }}
          </button>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<style scoped>
.database-table :deep(.el-table__header th) {
  background: #f3f2ee;
  color: #111;
  font-weight: 600;
}
.database-table :deep(.el-table__cell) {
  padding-top: 12px;
  padding-bottom: 12px;
}
.database-editor-drawer :deep(.el-drawer__header) {
  margin-bottom: 0;
  padding: 24px 24px 16px;
  font-size: 18px;
  font-weight: 600;
}
.database-editor-drawer :deep(.el-drawer__body) {
  padding: 0 24px 24px;
}
</style>
