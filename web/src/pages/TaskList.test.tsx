import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import type { AxiosResponse } from 'axios'
import TaskList from './TaskList'
import * as apiClient from '../api/client'
import type { Task } from '../types/task'

// Mock the TaskCard component to simplify testing
vi.mock('../components/TaskCard', () => ({
  TaskCard: ({ task, onTaskUpdate, onNextInstanceCreated }: { task: Task; onTaskUpdate?: (task: Task) => void; onNextInstanceCreated?: (task: Task) => void }) => (
    <div data-testid={`task-card-${task.id}`}>
      <div>{task.title}</div>
      <div>{task.state}</div>
      <button onClick={() => onTaskUpdate && onTaskUpdate({ ...task, state: 'Completed' })}>
        Update Task
      </button>
      <button onClick={() => onNextInstanceCreated && onNextInstanceCreated({ ...task, id: 999 })}>
        Create Next Instance
      </button>
    </div>
  ),
}))

// Mock the API client
vi.mock('../api/client', () => ({
  taskApi: {
    list: vi.fn(),
  },
}))

describe('TaskList Page', () => {
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

  beforeEach(() => {
    vi.clearAllMocks()
  })

  const mockAxiosResponse = <T,>(data: T): AxiosResponse<T> => ({
    data,
    status: 200,
    statusText: 'OK',
    headers: {},
    config: {
      headers: {},
    } as AxiosResponse['config'],
  })

  it('renders without errors', async () => {
    vi.mocked(apiClient.taskApi.list).mockResolvedValue(mockAxiosResponse([]))
    
    render(<TaskList />)
    
    await waitFor(() => {
      expect(screen.getByText('Task List')).toBeInTheDocument()
    })
  })

  it('displays the correct heading', async () => {
    vi.mocked(apiClient.taskApi.list).mockResolvedValue(mockAxiosResponse([]))
    
    render(<TaskList />)
    const heading = await screen.findByRole('heading', { level: 1 })
    expect(heading).toHaveTextContent('Task List')
  })

  it('displays the description', async () => {
    vi.mocked(apiClient.taskApi.list).mockResolvedValue(mockAxiosResponse([]))
    
    render(<TaskList />)
    
    await waitFor(() => {
      expect(screen.getByText(/View and manage your daily tasks/i)).toBeInTheDocument()
    })
  })

  it('displays no tasks message when list is empty', async () => {
    vi.mocked(apiClient.taskApi.list).mockResolvedValue(mockAxiosResponse([]))
    
    render(<TaskList />)
    
    await waitFor(() => {
      expect(screen.getByText(/No tasks yet/i)).toBeInTheDocument()
    })
  })

  it('renders tasks with TaskCard component', async () => {
    const tasks = [mockTask, { ...mockTask, id: 2, title: 'Second Task' }]
    vi.mocked(apiClient.taskApi.list).mockResolvedValue(mockAxiosResponse(tasks))
    
    render(<TaskList />)
    
    await waitFor(() => {
      expect(screen.getByTestId('task-card-1')).toBeInTheDocument()
      expect(screen.getByTestId('task-card-2')).toBeInTheDocument()
      expect(screen.getByText('Test Task')).toBeInTheDocument()
      expect(screen.getByText('Second Task')).toBeInTheDocument()
    })
  })

  it('displays error state with retry button', async () => {
    const errorMessage = 'Failed to load tasks'
    vi.mocked(apiClient.taskApi.list).mockRejectedValue(new Error(errorMessage))
    
    render(<TaskList />)
    
    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument()
      expect(screen.getByText('Retry')).toBeInTheDocument()
    })
  })

  it('retry button reloads tasks', async () => {
    // First call fails
    vi.mocked(apiClient.taskApi.list).mockRejectedValueOnce(new Error('Network error'))
    
    render(<TaskList />)
    
    await waitFor(() => {
      expect(screen.getByText('Retry')).toBeInTheDocument()
    })

    // Second call succeeds
    vi.mocked(apiClient.taskApi.list).mockResolvedValue(mockAxiosResponse([mockTask]))
    
    const retryButton = screen.getByText('Retry')
    fireEvent.click(retryButton)

    await waitFor(() => {
      expect(screen.getByTestId('task-card-1')).toBeInTheDocument()
    })
  })

  it('updates task in list when handleTaskUpdate is called', async () => {
    vi.mocked(apiClient.taskApi.list).mockResolvedValue(mockAxiosResponse([mockTask]))
    
    render(<TaskList />)
    
    await waitFor(() => {
      expect(screen.getByText('Ready')).toBeInTheDocument()
    })

    // Simulate task update
    const updateButton = screen.getByText('Update Task')
    fireEvent.click(updateButton)

    await waitFor(() => {
      expect(screen.getByText('Completed')).toBeInTheDocument()
    })
  })

  it('displays notification when recurring task creates next instance', async () => {
    vi.mocked(apiClient.taskApi.list).mockResolvedValue(mockAxiosResponse([mockTask]))
    
    render(<TaskList />)
    
    await waitFor(() => {
      expect(screen.getByTestId('task-card-1')).toBeInTheDocument()
    })

    // Simulate next instance creation
    const createNextButton = screen.getByText('Create Next Instance')
    fireEvent.click(createNextButton)

    await waitFor(() => {
      expect(screen.getByText(/Next instance of recurring task created/i)).toBeInTheDocument()
      expect(screen.getByTestId('task-card-999')).toBeInTheDocument()
    })
  })

  it('adds new task to beginning of list when next instance is created', async () => {
    const task2 = { ...mockTask, id: 2, title: 'Task 2' }
    vi.mocked(apiClient.taskApi.list).mockResolvedValue(mockAxiosResponse([mockTask, task2]))
    
    render(<TaskList />)
    
    await waitFor(() => {
      expect(screen.getByTestId('task-card-1')).toBeInTheDocument()
    })

    // Get all task cards before adding new one
    const taskCardsBefore = screen.getAllByTestId(/task-card-/)
    expect(taskCardsBefore).toHaveLength(2)

    // Simulate next instance creation (id 999)
    const createNextButton = screen.getAllByText('Create Next Instance')[0]
    fireEvent.click(createNextButton)

    await waitFor(() => {
      const taskCardsAfter = screen.getAllByTestId(/task-card-/)
      expect(taskCardsAfter).toHaveLength(3)
      // New task should be first in the list
      expect(taskCardsAfter[0]).toHaveAttribute('data-testid', 'task-card-999')
    })
  })
})
