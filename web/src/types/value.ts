// TypeScript types matching backend API schema for Values
export interface Value {
  id: number
  statement: string
  archived: boolean  // Computed from archived_at (for convenience)
  created_at: string // ISO 8601 timestamp
  archived_at?: string | null // ISO 8601 timestamp, null for active values
}

export interface ValueCreate {
  statement: string
}

// ValueUpdate uses same schema as ValueCreate (backend accepts ValueCreate for both)
export type ValueUpdate = ValueCreate
