import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import type { AxiosResponse } from 'axios'
import TaskList from './TaskList'
import * as apiClient from '../api/client'
import type { Task } from '../types/task'
import type { Value } from '../types/value'

// Mock react-router-dom
const mockNavigate = vi.fn()
vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
}))

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
  valueApi: {
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

  const mockValue: Value = {
    id: 1,
    statement: 'Test Value',
    archived: false,
    created_at: '2026-01-20T00:00:00Z',
    archived_at: null,
  }

  beforeEach(() => {
    vi.clearAllMocks()
    // Default mock for valueApi.list to return empty array
    vi.mocked(apiClient.valueApi.list).mockResolvedValue(mockAxiosResponse([]))
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
      expect(screen.getByText(/No tasks found with the selected filters/i)).toBeInTheDocument()
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
      expect(screen.getByTestId('task-card-1')).toBeInTheDocument()
    })

    // Simulate task update
    const updateButton = screen.getByText('Update Task')
    fireEvent.click(updateButton)

    await waitFor(() => {
      // Check that Completed appears in the task card (not in filter)
      const taskCard = screen.getByTestId('task-card-1')
      expect(taskCard).toHaveTextContent('Completed')
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

  it('displays Create Task button', async () => {
    vi.mocked(apiClient.taskApi.list).mockResolvedValue(mockAxiosResponse([]))
    
    render(<TaskList />)
    
    await waitFor(() => {
      expect(screen.getByText('+ Create Task')).toBeInTheDocument()
    })
  })

  it('navigates to task creation page when Create Task button is clicked', async () => {
    vi.mocked(apiClient.taskApi.list).mockResolvedValue(mockAxiosResponse([]))
    
    render(<TaskList />)
    
    await waitFor(() => {
      expect(screen.getByText('+ Create Task')).toBeInTheDocument()
    })

    const createButton = screen.getByText('+ Create Task')
    fireEvent.click(createButton)

    expect(mockNavigate).toHaveBeenCalledWith('/tasks/new')
  })

  it('displays state filter checkboxes', async () => {
    vi.mocked(apiClient.taskApi.list).mockResolvedValue(mockAxiosResponse([]))
    
    render(<TaskList />)
    
    await waitFor(() => {
      expect(screen.getByText('Task State')).toBeInTheDocument()
      expect(screen.getByLabelText(/Ready/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/In Progress/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Completed/i)).toBeInTheDocument()
    })
  })

  it('filters tasks by state when checkbox is clicked', async () => {
    const readyTask = mockTask
    const completedTask = { ...mockTask, id: 2, state: 'Completed' as Task['state'], title: 'Completed Task' }
    
    // Initial load with Ready filter
    vi.mocked(apiClient.taskApi.list).mockResolvedValue(mockAxiosResponse([readyTask]))
    
    render(<TaskList />)
    
    await waitFor(() => {
      expect(screen.getByTestId('task-card-1')).toBeInTheDocument()
    })

    // Check the Completed checkbox
    vi.mocked(apiClient.taskApi.list).mockResolvedValue(mockAxiosResponse([completedTask]))
    const completedCheckbox = screen.getByLabelText(/Completed/i)
    fireEvent.click(completedCheckbox)

    await waitFor(() => {
      // Should now show both tasks (Ready and Completed)
      expect(apiClient.taskApi.list).toHaveBeenCalledWith({ state: 'Ready' })
      expect(apiClient.taskApi.list).toHaveBeenCalledWith({ state: 'Completed' })
    })
  })

  it('displays value filter when values exist', async () => {
    vi.mocked(apiClient.valueApi.list).mockResolvedValue(mockAxiosResponse([mockValue]))
    vi.mocked(apiClient.taskApi.list).mockResolvedValue(mockAxiosResponse([]))
    
    render(<TaskList />)
    
    await waitFor(() => {
      expect(screen.getByText('Filter by Value')).toBeInTheDocument()
      expect(screen.getByLabelText(/Test Value/i)).toBeInTheDocument()
    })
  })

  it('displays value pills for tasks with linked values', async () => {
    const taskWithValue = { ...mockTask, value_ids: [1] }
    vi.mocked(apiClient.valueApi.list).mockResolvedValue(mockAxiosResponse([mockValue]))
    vi.mocked(apiClient.taskApi.list).mockResolvedValue(mockAxiosResponse([taskWithValue]))
    
    render(<TaskList />)
    
    await waitFor(() => {
      // Look for value pill (with smaller font size), not the filter checkbox
      const valuePills = screen.getAllByText('Test Value')
      expect(valuePills.length).toBeGreaterThanOrEqual(1)
      // Verify at least one is a pill (with the specific styling)
      const pill = valuePills.find(el => 
        el.tagName === 'SPAN' && 
        el.style.fontSize === '0.8rem'
      )
      expect(pill).toBeInTheDocument()
    })
  })

  it('displays task count', async () => {
    const tasks = [mockTask, { ...mockTask, id: 2, title: 'Task 2' }]
    vi.mocked(apiClient.taskApi.list).mockResolvedValue(mockAxiosResponse(tasks))
    
    render(<TaskList />)
    
    await waitFor(() => {
      expect(screen.getByText('Showing 2 tasks')).toBeInTheDocument()
    })
  })

  it('filters tasks by value when value checkbox is clicked', async () => {
    const taskWithValue1 = { ...mockTask, value_ids: [1] }
    const taskWithValue2 = { ...mockTask, id: 2, title: 'Task 2', value_ids: [2] }
    const value2: Value = { ...mockValue, id: 2, statement: 'Value 2' }
    
    vi.mocked(apiClient.valueApi.list).mockResolvedValue(mockAxiosResponse([mockValue, value2]))
    vi.mocked(apiClient.taskApi.list).mockResolvedValue(mockAxiosResponse([taskWithValue1, taskWithValue2]))
    
    render(<TaskList />)
    
    await waitFor(() => {
      expect(screen.getByTestId('task-card-1')).toBeInTheDocument()
      expect(screen.getByTestId('task-card-2')).toBeInTheDocument()
    })

    // Click on value filter for "Test Value" (value_id: 1)
    const valueCheckbox = screen.getByLabelText(/Test Value/i)
    fireEvent.click(valueCheckbox)

    await waitFor(() => {
      // Should only show task 1 now (has value_id 1)
      expect(screen.getByTestId('task-card-1')).toBeInTheDocument()
      expect(screen.queryByTestId('task-card-2')).not.toBeInTheDocument()
    })
  })

  it('handles multiple value filters correctly (client-side filtering)', async () => {
    // Test that client-side value filtering works when multiple values are selected
    const task1 = { ...mockTask, id: 101, title: 'Has Value 1', value_ids: [1], completed_at: null }
    const task2 = { ...mockTask, id: 102, title: 'Has Value 2', value_ids: [2], completed_at: null }
    const value2: Value = { ...mockValue, id: 2, statement: 'Value 2' }
    
    vi.mocked(apiClient.valueApi.list).mockResolvedValue(mockAxiosResponse([mockValue, value2]))
    vi.mocked(apiClient.taskApi.list).mockResolvedValue(
      mockAxiosResponse([task1, task2])
    )
    
    render(<TaskList />)
    
    // Wait for tasks to load (no value filters, so both show)
    await waitFor(() => {
      expect(screen.getByText('Has Value 1')).toBeInTheDocument()
      expect(screen.getByText('Has Value 2')).toBeInTheDocument()
    })

    // Select first value filter - should show only task 1
    const value1Checkbox = screen.getByLabelText(/Test Value/i)
    fireEvent.click(value1Checkbox)

    await waitFor(() => {
      expect(screen.getByText('Has Value 1')).toBeInTheDocument()
      expect(screen.queryByText('Has Value 2')).not.toBeInTheDocument()
    })

    // Select second value filter - should show both tasks (OR logic)
    const value2Checkbox = screen.getByLabelText(/Value 2/i)
    fireEvent.click(value2Checkbox)

    await waitFor(() => {
      expect(screen.getByText('Has Value 1')).toBeInTheDocument()
      expect(screen.getByText('Has Value 2')).toBeInTheDocument()
    })
  })

  it('removes duplicate tasks when fetching multiple states', async () => {
    // Simulate a scenario where the same task is returned from multiple state queries
    const duplicateTask = mockTask
    
    // First render with Ready filter (default)
    vi.mocked(apiClient.taskApi.list).mockResolvedValueOnce(mockAxiosResponse([duplicateTask]))
    
    render(<TaskList />)
    
    await waitFor(() => {
      expect(screen.getByTestId('task-card-1')).toBeInTheDocument()
    })

    // When clicking In Progress, it will make 2 API calls: one for Ready, one for In Progress
    // Both return the same task to simulate a potential duplicate
    vi.mocked(apiClient.taskApi.list)
      .mockResolvedValueOnce(mockAxiosResponse([duplicateTask]))  // Ready
      .mockResolvedValueOnce(mockAxiosResponse([duplicateTask]))  // In Progress

    const inProgressCheckbox = screen.getByLabelText(/In Progress/i)
    fireEvent.click(inProgressCheckbox)

    await waitFor(() => {
      // Should only show the task once, not twice (deduplication working)
      const taskCards = screen.getAllByTestId(/task-card-/)
      expect(taskCards).toHaveLength(1)
    })
  })

  it('shows empty state when all state filters are unchecked', async () => {
    vi.mocked(apiClient.taskApi.list).mockResolvedValue(mockAxiosResponse([mockTask]))
    
    render(<TaskList />)
    
    await waitFor(() => {
      expect(screen.getByTestId('task-card-1')).toBeInTheDocument()
    })

    // Uncheck the Ready filter (the only one checked by default)
    const readyCheckbox = screen.getByLabelText(/Ready/i)
    fireEvent.click(readyCheckbox)

    await waitFor(() => {
      // Should show empty state
      expect(screen.queryByTestId('task-card-1')).not.toBeInTheDocument()
      expect(screen.getByText(/No tasks found with the selected filters/i)).toBeInTheDocument()
    })
  })

  it('shows notification when values fail to load', async () => {
    const errorMessage = 'Network error'
    vi.mocked(apiClient.valueApi.list).mockRejectedValue(new Error(errorMessage))
    vi.mocked(apiClient.taskApi.list).mockResolvedValue(mockAxiosResponse([]))
    
    render(<TaskList />)
    
    await waitFor(() => {
      expect(screen.getByText(/Failed to load values/i)).toBeInTheDocument()
      expect(screen.getByText(/Value filter may be unavailable/i)).toBeInTheDocument()
    })
  })
})
