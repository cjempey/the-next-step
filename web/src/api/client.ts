// API client for communicating with backend
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
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
  list: () => apiClient.get('/values'),
  create: (data: unknown) => apiClient.post('/values', data),
  update: (id: number, data: unknown) => apiClient.put(`/values/${id}`, data),
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
