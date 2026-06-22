export interface DatabaseColumn {
  name: string
  data_type: string
  is_nullable: boolean
  is_primary_key: boolean
  column_default?: string | null
}

export interface DatabaseTable {
  name: string
  row_count?: number | null
  columns: DatabaseColumn[]
}

export interface DatabaseRowList {
  table: string
  columns: DatabaseColumn[]
  primary_keys: string[]
  rows: Record<string, any>[]
  total: number
  limit: number
  offset: number
}

export interface DatabaseMutationOut {
  success: boolean
  message: string
}

export interface RowPayload {
  values: Record<string, any>
}

export interface RowUpdatePayload {
  primary_key: Record<string, any>
  values: Record<string, any>
}

export interface RowDeletePayload {
  primary_key: Record<string, any>
}
