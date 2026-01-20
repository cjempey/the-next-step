import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import type { AxiosResponse } from 'axios'
import { TaskCard } from './TaskCard'
import type { Task } from '../types/task'
import * as apiClient from '../api/client'

// Mock the API client
vi.mock('../api/client', () => ({
  taskApi: {
    transition: vi.fn(),
  },
}))

describe('TaskCard', () => {
  const mockTask: Task = {
    id: 1,
    title: 'Test Task',
    description: 'Test description',
    value_ids: [],
    impact: 'B',
    urgency: 2,
    state: 'Ready',
    due_date: null,
    recurrence: 'none',
    completion_percentage: 0,
    notes: null,
    created_at: '2026-01-20T00:00:00Z',
    updated_at: '2026-01-20T00:00:00Z',
    completed_at: null,
  }

  const mockAxiosResponse = <T,>(data: T): AxiosResponse<T> => ({
    data,
    status: 200,
    statusText: 'OK',
    headers: {},
    config: {
      headers: {},
    } as AxiosResponse['config'],
  })

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders task information', () => {
    render(<TaskCard task={mockTask} />)
    
    expect(screen.getByText('Test Task')).toBeInTheDocument()
    expect(screen.getByText('Test description')).toBeInTheDocument()
    expect(screen.getByText('Ready')).toBeInTheDocument()
  })

  it('shows action buttons for Ready state', () => {
    render(<TaskCard task={mockTask} />)
    
    expect(screen.getByText('Start')).toBeInTheDocument()
    expect(screen.getByText('Block')).toBeInTheDocument()
    expect(screen.getByText('Park')).toBeInTheDocument()
    expect(screen.getByText('Cancel')).toBeInTheDocument()
  })

  it('shows different buttons for In Progress state', () => {
    const inProgressTask = { ...mockTask, state: 'In Progress' as const }
    render(<TaskCard task={inProgressTask} />)
    
    expect(screen.getByText('Complete')).toBeInTheDocument()
    expect(screen.getByText('Block')).toBeInTheDocument()
    expect(screen.getByText('Park')).toBeInTheDocument()
    expect(screen.getByText('Cancel')).toBeInTheDocument()
    expect(screen.getByText('Mark Ready')).toBeInTheDocument()
  })

  it('shows no buttons for Completed state', () => {
    const completedTask = { ...mockTask, state: 'Completed' as const }
    render(<TaskCard task={completedTask} />)
    
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
    expect(screen.getByText('Task completed')).toBeInTheDocument()
  })

  it('shows no buttons for Cancelled state', () => {
    const cancelledTask = { ...mockTask, state: 'Cancelled' as const }
    render(<TaskCard task={cancelledTask} />)
    
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
    expect(screen.getByText('Task cancelled')).toBeInTheDocument()
  })

  it('handles button click for non-destructive transition', async () => {
    const mockOnTaskUpdate = vi.fn()
    const updatedTask = { ...mockTask, state: 'In Progress' as const }
    
    vi.mocked(apiClient.taskApi.transition).mockResolvedValue(
      mockAxiosResponse({ task: updatedTask, next_instance: null })
    )

    render(<TaskCard task={mockTask} onTaskUpdate={mockOnTaskUpdate} />)
    
    const startButton = screen.getByText('Start')
    fireEvent.click(startButton)

    await waitFor(() => {
      expect(apiClient.taskApi.transition).toHaveBeenCalledWith(1, { new_state: 'In Progress' })
      expect(mockOnTaskUpdate).toHaveBeenCalledWith(updatedTask)
    })
  })

  it('shows confirmation dialog for Cancel button', async () => {
    render(<TaskCard task={mockTask} />)
    
    const cancelButton = screen.getByText('Cancel')
    fireEvent.click(cancelButton)

    await waitFor(() => {
      expect(screen.getByText('Confirm Action')).toBeInTheDocument()
      expect(screen.getByText(/Are you sure you want to cancel this task/i)).toBeInTheDocument()
    })
  })

  it('cancels task after confirmation', async () => {
    const mockOnTaskUpdate = vi.fn()
    const cancelledTask = { ...mockTask, state: 'Cancelled' as const }
    
    vi.mocked(apiClient.taskApi.transition).mockResolvedValue(
      mockAxiosResponse({ task: cancelledTask, next_instance: null })
    )

    render(<TaskCard task={mockTask} onTaskUpdate={mockOnTaskUpdate} />)
    
    // Click cancel button
    const cancelButton = screen.getByText('Cancel')
    fireEvent.click(cancelButton)

    // Confirm in dialog
    await waitFor(() => {
      expect(screen.getByText('Yes, cancel task')).toBeInTheDocument()
    })
    
    const confirmButton = screen.getByText('Yes, cancel task')
    fireEvent.click(confirmButton)

    await waitFor(() => {
      expect(apiClient.taskApi.transition).toHaveBeenCalledWith(1, { new_state: 'Cancelled' })
      expect(mockOnTaskUpdate).toHaveBeenCalledWith(cancelledTask)
    })
  })

  it('handles API error and shows error message', async () => {
    const errorMessage = 'Invalid transition from Ready to Completed'
    const errorObj = {
      response: { data: { detail: errorMessage } },
    }
    // Make it look like an Error for instanceof check
    Object.setPrototypeOf(errorObj, Error.prototype)
    
    vi.mocked(apiClient.taskApi.transition).mockRejectedValue(errorObj)

    render(<TaskCard task={mockTask} />)
    
    const startButton = screen.getByText('Start')
    fireEvent.click(startButton)

    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument()
    })

    // Verify task state was reverted (still shows Ready state buttons)
    expect(screen.getByText('Start')).toBeInTheDocument()
  })

  it('notifies parent when recurring task creates next instance', async () => {
    const mockOnNextInstanceCreated = vi.fn()
    const completedTask = { ...mockTask, state: 'Completed' as const }
    const nextInstance = { ...mockTask, id: 2, state: 'Ready' as const }
    
    vi.mocked(apiClient.taskApi.transition).mockResolvedValue(
      mockAxiosResponse({ task: completedTask, next_instance: nextInstance })
    )

    const inProgressTask = { ...mockTask, state: 'In Progress' as const }
    render(<TaskCard task={inProgressTask} onNextInstanceCreated={mockOnNextInstanceCreated} />)
    
    const completeButton = screen.getByText('Complete')
    fireEvent.click(completeButton)

    await waitFor(() => {
      expect(mockOnNextInstanceCreated).toHaveBeenCalledWith(nextInstance)
    })
  })

  it('syncs with prop changes', async () => {
    const { rerender } = render(<TaskCard task={mockTask} />)
    
    expect(screen.getByText('Ready')).toBeInTheDocument()

    const updatedTask = { ...mockTask, state: 'In Progress' as const }
    rerender(<TaskCard task={updatedTask} />)

    await waitFor(() => {
      expect(screen.getByText('In Progress')).toBeInTheDocument()
    })
  })
})
