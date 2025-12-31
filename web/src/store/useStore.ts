import { create } from 'zustand'

interface Task {
  id: number
  title: string
  description?: string
  impact: string
  urgency: number
  state: string
  completion_percentage?: number
  notes?: string
  created_at: string
}

interface Value {
  id: number
  statement: string
  archived: boolean
}

interface AppState {
  tasks: Task[]
  values: Value[]
  setTasks: (tasks: Task[]) => void
  setValues: (values: Value[]) => void
  addTask: (task: Task) => void
  updateTask: (task: Task) => void
  removeTask: (id: number) => void
}

export const useStore = create<AppState>((set) => ({
  tasks: [],
  values: [],
  setTasks: (tasks) => set({ tasks }),
  setValues: (values) => set({ values }),
  addTask: (task) => set((state) => ({ tasks: [...state.tasks, task] })),
  updateTask: (task) => set((state) => ({
    tasks: state.tasks.map((t) => (t.id === task.id ? task : t)),
  })),
  removeTask: (id) => set((state) => ({
    tasks: state.tasks.filter((t) => t.id !== id),
  })),
}))
