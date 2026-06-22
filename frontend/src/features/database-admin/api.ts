import request from '@/api/request'
import type {
  DatabaseMutationOut,
  DatabaseRowList,
  DatabaseTable,
  RowDeletePayload,
  RowPayload,
  RowUpdatePayload,
} from './types'

export function listTables(): Promise<DatabaseTable[]> {
  return request.get<DatabaseTable[]>('/database-admin/tables').then(r => r.data)
}

export function listRows(
  table: string,
  params: { limit: number; offset: number; search?: string },
): Promise<DatabaseRowList> {
  return request.get<DatabaseRowList>(`/database-admin/tables/${table}/rows`, { params }).then(r => r.data)
}

export function createRow(table: string, payload: RowPayload): Promise<DatabaseMutationOut> {
  return request.post<DatabaseMutationOut>(`/database-admin/tables/${table}/rows`, payload).then(r => r.data)
}

export function updateRow(table: string, payload: RowUpdatePayload): Promise<DatabaseMutationOut> {
  return request.put<DatabaseMutationOut>(`/database-admin/tables/${table}/rows`, payload).then(r => r.data)
}

export function deleteRow(table: string, payload: RowDeletePayload): Promise<DatabaseMutationOut> {
  return request.delete<DatabaseMutationOut>(`/database-admin/tables/${table}/rows`, { data: payload }).then(r => r.data)
}
