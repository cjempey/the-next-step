// TypeScript types matching backend API schema for Values
export interface Value {
  id: number
  statement: string
  archived: boolean
  created_at: string // ISO 8601 timestamp
  updated_at: string // ISO 8601 timestamp
}

export interface ValueCreate {
  statement: string
}

// ValueUpdate uses same schema as ValueCreate (backend accepts ValueCreate for both)
export type ValueUpdate = ValueCreate
