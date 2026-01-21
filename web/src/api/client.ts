// API client for communicating with backend
import axios from 'axios'
import type { Value, ValueCreate, ValueUpdate } from '../types/value'
import type { Task, TaskCreate } from '../types/task'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

// Hardcoded JWT token for MVP (temporary until auth UI is built)
// To generate: Register a test user and login via backend API
const TEMP_AUTH_TOKEN = import.meta.env.VITE_AUTH_TOKEN || ''

// Warn developer if token is missing (better DX during setup)
if (!TEMP_AUTH_TOKEN) {
  console.warn(
    '⚠️ VITE_AUTH_TOKEN is not set. API requests will fail with 401 errors.\n' +
    'To fix this:\n' +
    '1. Copy web/.env.example to web/.env\n' +
    '2. Start the backend: cd backend && uv run uvicorn app.main:app --reload\n' +
    '3. Generate a token: cd backend && ./scripts/get_token.sh\n' +
    '4. Add the token to web/.env as VITE_AUTH_TOKEN=<your-token>\n' +
    '5. Restart the web dev server'
  )
}

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests if available
apiClient.interceptors.request.use((config) => {
  if (TEMP_AUTH_TOKEN) {
    config.headers.Authorization = `Bearer ${TEMP_AUTH_TOKEN}`
  }
  return config
})

// Task endpoints
export const taskApi = {
  list: (params?: { state?: Task['state']; value_id?: number }) => 
    apiClient.get<Task[]>('/tasks', { params }),
  create: (data: TaskCreate) => apiClient.post<Task>('/tasks', data),
  get: (id: number) => apiClient.get<Task>(`/tasks/${id}`),
  update: (id: number, data: unknown) => apiClient.put<Task>(`/tasks/${id}`, data),
  delete: (id: number) => apiClient.delete(`/tasks/${id}`),
  transition: (id: number, data: { new_state: Task['state']; notes?: string; completion_percentage?: number }) =>
    apiClient.post<{ task: Task; next_instance: Task | null }>(`/tasks/${id}/transition`, data),
}

// Value endpoints
export const valueApi = {
  list: (includeArchived = false) => 
    apiClient.get<Value[]>('/values', { params: { include_archived: includeArchived } }),
  create: (data: ValueCreate) => apiClient.post<Value>('/values', data),
  update: (id: number, data: ValueUpdate) => apiClient.put<Value>(`/values/${id}`, data),
  archive: (id: number) => apiClient.patch<Value>(`/values/${id}/archive`), // Sets archived = true
  delete: (id: number) => apiClient.delete(`/values/${id}`),
}

// Suggestion endpoints
export const suggestionApi = {
  getNext: (data: unknown) => apiClient.post('/suggestions/next', data),
  reject: (taskId: number) => apiClient.post(`/suggestions/${taskId}/reject`),
  break: () => apiClient.post('/suggestions/break'),
  suggestImpact: (taskTitle: string) =>
    apiClient.post('/suggestions/suggest-impact', { task_title: taskTitle }),
  suggestUrgency: (taskTitle: string) =>
    apiClient.post('/suggestions/suggest-urgency', { task_title: taskTitle }),
}

// Review endpoints
export const reviewApi = {
  generateCards: () => apiClient.post('/reviews/cards', {}),
  respondToCard: (cardId: string, responseOption: string) =>
    apiClient.post(`/reviews/cards/${cardId}/respond`, { response_option: responseOption }),
  getHistory: (days?: number) => apiClient.get('/reviews/history', { params: { days } }),
}
