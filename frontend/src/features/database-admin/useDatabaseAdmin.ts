import { computed, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as databaseApi from './api'
import type { DatabaseColumn, DatabaseRowList, DatabaseTable } from './types'

export function useDatabaseAdmin() {
  const tables = ref<DatabaseTable[]>([])
  const selectedTable = ref<string>('')
  const rowData = ref<DatabaseRowList | null>(null)
  const loadingTables = ref(false)
  const loadingRows = ref(false)
  const saving = ref(false)
  const pageSize = ref(50)
  const currentPage = ref(1)
  const searchText = ref('')
  const editorVisible = ref(false)
  const editorMode = ref<'create' | 'edit'>('create')
  const form = reactive<Record<string, any>>({})
  const editingPrimaryKey = ref<Record<string, any>>({})
  const selectedRows = ref<Record<string, any>[]>([])

  const columns = computed<DatabaseColumn[]>(() => rowData.value?.columns || [])
  const primaryKeys = computed<string[]>(() => rowData.value?.primary_keys || [])
  const rows = computed(() => rowData.value?.rows || [])
  const total = computed(() => rowData.value?.total || 0)
  const selectedMeta = computed(() => tables.value.find(t => t.name === selectedTable.value) || null)

  async function loadTables() {
    loadingTables.value = true
    try {
      tables.value = await databaseApi.listTables()
      if (!selectedTable.value && tables.value.length > 0) {
        await selectTable(tables.value[0].name)
      }
    } catch (err: any) {
      ElMessage.error(err.response?.data?.detail || '加载数据表失败')
    } finally {
      loadingTables.value = false
    }
  }

  async function loadRows(resetPage = false) {
    if (!selectedTable.value) return
    if (resetPage) currentPage.value = 1
    loadingRows.value = true
    try {
      rowData.value = await databaseApi.listRows(selectedTable.value, {
        limit: pageSize.value,
        offset: (currentPage.value - 1) * pageSize.value,
        search: searchText.value || undefined,
      })
    } catch (err: any) {
      ElMessage.error(err.response?.data?.detail || '加载表数据失败')
    } finally {
      loadingRows.value = false
    }
  }

  async function selectTable(table: string) {
    selectedTable.value = table
    currentPage.value = 1
    searchText.value = ''
    await loadRows()
  }

  function openCreate() {
    editorMode.value = 'create'
    editingPrimaryKey.value = {}
    resetForm()
    editorVisible.value = true
  }

  function openEdit(row: Record<string, any>) {
    editorMode.value = 'edit'
    resetForm(row)
    editingPrimaryKey.value = pickPrimaryKey(row)
    editorVisible.value = true
  }

  async function saveRow() {
    if (!selectedTable.value) return
    saving.value = true
    try {
      const values = buildPayloadValues()
      if (editorMode.value === 'create') {
        const result = await databaseApi.createRow(selectedTable.value, { values })
        ElMessage.success(result.message)
      } else {
        const result = await databaseApi.updateRow(selectedTable.value, {
          primary_key: editingPrimaryKey.value,
          values,
        })
        ElMessage.success(result.message)
      }
      editorVisible.value = false
      await loadRows()
      await loadTables()
    } catch (err: any) {
      ElMessage.error(err.response?.data?.detail || '保存记录失败')
    } finally {
      saving.value = false
    }
  }

  async function removeRow(row: Record<string, any>) {
    if (!selectedTable.value) return
    if (primaryKeys.value.length === 0) {
      ElMessage.warning('该表没有主键，暂不支持删除')
      return
    }
    try {
      await ElMessageBox.confirm('删除后无法恢复，确定删除该记录吗？', '删除记录', {
        type: 'warning',
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        confirmButtonClass: 'el-button--danger',
      })
    } catch { return }

    try {
      const result = await databaseApi.deleteRow(selectedTable.value, { primary_key: pickPrimaryKey(row) })
      ElMessage.success(result.message)
      await loadRows()
      await loadTables()
    } catch (err: any) {
      ElMessage.error(err.response?.data?.detail || '删除记录失败')
    }
  }

  function resetForm(row?: Record<string, any>) {
    for (const key of Object.keys(form)) delete form[key]
    for (const col of columns.value) {
      if (editorMode.value === 'create' && col.column_default && !col.is_nullable) continue
      form[col.name] = row ? normalizeForInput(row[col.name]) : ''
    }
  }

  function pickPrimaryKey(row: Record<string, any>) {
    return Object.fromEntries(primaryKeys.value.map(key => [key, row[key]]))
  }

  function buildPayloadValues() {
    const values: Record<string, any> = {}
    for (const col of columns.value) {
      if (editorMode.value === 'edit' && col.is_primary_key) continue
      if (!(col.name in form)) continue
      values[col.name] = parseInputValue(form[col.name], col)
    }
    return values
  }

  function normalizeForInput(value: any) {
    if (value == null) return ''
    if (typeof value === 'object') return JSON.stringify(value, null, 2)
    return String(value)
  }

  function parseInputValue(value: any, col: DatabaseColumn) {
    if (value === '') return null
    if (col.data_type === 'boolean') return value === true || value === 'true'
    if ([
      'integer', 'bigint', 'smallint', 'numeric', 'real', 'double precision',
    ].includes(col.data_type)) return Number(value)
    if (col.data_type === 'json' || col.data_type === 'jsonb') {
      try { return JSON.parse(value) } catch { return value }
    }
    return value
  }

  function formatCell(value: any) {
    if (value == null) return 'NULL'
    if (typeof value === 'object') return JSON.stringify(value)
    return String(value)
  }

  function selectableRows(row: Record<string, any>): boolean {
    if (primaryKeys.value.length === 0) return false
    return primaryKeys.value.every((key) => row[key] != null)
  }

  async function removeRows(selected: Record<string, any>[]) {
    if (!selectedTable.value) return
    if (primaryKeys.value.length === 0) {
      ElMessage.warning('该表没有主键，暂不支持删除')
      return
    }
    let successCount = 0
    let failCount = 0
    for (const row of selected) {
      try {
        await databaseApi.deleteRow(selectedTable.value, { primary_key: pickPrimaryKey(row) })
        successCount++
      } catch (err: any) {
        failCount++
        console.warn('批量删除失败', row, err)
      }
    }
    if (successCount > 0) ElMessage.success(`成功删除 ${successCount} 条记录${failCount > 0 ? `，${failCount} 条失败` : ''}`)
    else if (failCount > 0) ElMessage.error('批量删除失败')
    await loadRows()
    await loadTables()
  }

  return {
    tables, selectedTable, selectedMeta, rowData, columns, primaryKeys, rows, total,
    loadingTables, loadingRows, saving, pageSize, currentPage, searchText,
    editorVisible, editorMode, form, selectedRows,
    selectableRows,
    loadTables, loadRows, selectTable, openCreate, openEdit, saveRow, removeRow, removeRows,
    formatCell,
  }
}
