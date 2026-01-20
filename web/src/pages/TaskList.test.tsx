import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import TaskList from './TaskList'
import * as apiClient from '../api/client'

// Mock the API client
vi.mock('../api/client', () => ({
  taskApi: {
    list: vi.fn(),
  },
}))

describe('TaskList Page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders without errors', async () => {
    vi.mocked(apiClient.taskApi.list).mockResolvedValue({ data: [] } as any)
    
    render(<TaskList />)
    
    await waitFor(() => {
      expect(screen.getByText('Task List')).toBeInTheDocument()
    })
  })

  it('displays the correct heading', async () => {
    vi.mocked(apiClient.taskApi.list).mockResolvedValue({ data: [] } as any)
    
    render(<TaskList />)
    const heading = await screen.findByRole('heading', { level: 1 })
    expect(heading).toHaveTextContent('Task List')
  })

  it('displays the placeholder description', async () => {
    vi.mocked(apiClient.taskApi.list).mockResolvedValue({ data: [] } as any)
    
    render(<TaskList />)
    await waitFor(() => {
      expect(screen.getByText(/View and manage your daily tasks/i)).toBeInTheDocument()
    })
  })

  it('displays no tasks message when list is empty', async () => {
    vi.mocked(apiClient.taskApi.list).mockResolvedValue({ data: [] } as any)
    
    render(<TaskList />)
    await waitFor(() => {
      expect(screen.getByText(/No tasks yet/i)).toBeInTheDocument()
    })
  })
})
