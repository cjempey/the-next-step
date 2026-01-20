// TypeScript types matching backend API schema for Tasks
export interface Task {
  id: number
  title: string
  description: string | null
  value_ids: number[]
  impact: 'A' | 'B' | 'C' | 'D'
  urgency: 1 | 2 | 3 | 4
  state: 'Ready' | 'In Progress' | 'Blocked' | 'Parked' | 'Completed' | 'Cancelled'
  due_date: string | null  // ISO 8601 timestamp
  recurrence: 'none' | 'daily' | 'weekly'
  completion_percentage: number | null
  notes: string | null
  created_at: string  // ISO 8601 timestamp
  updated_at: string  // ISO 8601 timestamp
  completed_at: string | null  // ISO 8601 timestamp, set when state becomes Completed
}

export interface TaskCreate {
  title: string
  description?: string | null
  value_ids?: number[]
  impact?: 'A' | 'B' | 'C' | 'D'
  urgency?: 1 | 2 | 3 | 4
  due_date?: string | null
  recurrence?: 'none' | 'daily' | 'weekly'
}
