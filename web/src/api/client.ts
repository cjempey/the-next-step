// API client for communicating with backend
import axios from 'axios'
import type { Value, ValueCreate, ValueUpdate } from '../types/value'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

// Hardcoded JWT token for MVP (temporary until auth UI is built)
// To generate: Register a test user and login via backend API
const TEMP_AUTH_TOKEN = import.meta.env.VITE_AUTH_TOKEN || ''

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
  list: () => apiClient.get('/tasks'),
  create: (data: unknown) => apiClient.post('/tasks', data),
  get: (id: number) => apiClient.get(`/tasks/${id}`),
  update: (id: number, data: unknown) => apiClient.put(`/tasks/${id}`, data),
  delete: (id: number) => apiClient.delete(`/tasks/${id}`),
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
