// TypeScript types matching backend API schema for Values
export interface Value {
  id: number
  statement: string
  archived: boolean
  created_at: string // ISO 8601 timestamp
}

export interface ValueCreate {
  statement: string
}

export interface ValueUpdate {
  statement: string
}
