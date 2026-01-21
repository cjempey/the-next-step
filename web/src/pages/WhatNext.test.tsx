import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import type { AxiosResponse } from 'axios'
import WhatNext from './WhatNext'
import { taskApi, valueApi, suggestionApi } from '../api/client'
import type { Task } from '../types/task'
import type { Value } from '../types/value'

// Mock react-router-dom
const mockNavigate = vi.fn()
vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
}))

// Mock API client
vi.mock('../api/client', () => ({
  taskApi: {
    list: vi.fn(),
    update: vi.fn(),
  },
  valueApi: {
    list: vi.fn(),
  },
  suggestionApi: {
    getNext: vi.fn(),
    reject: vi.fn(),
    break: vi.fn(),
  },
}))

// Helper to create mock axios response
const mockAxiosResponse = <T,>(data: T): AxiosResponse<T> => ({
  data,
  status: 200,
  statusText: 'OK',
  headers: {},
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  config: { headers: {} } as any,
})

// Mock data
const mockTask: Task = {
  id: 1,
  title: 'Test Task',
  description: null,
  impact: 'A',
  urgency: 1,
  state: 'Ready',
  value_ids: [1],
  due_date: null,
  recurrence: 'none',
  completion_percentage: null,
  notes: null,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  completed_at: null,
}

const mockInProgressTask: Task = {
  ...mockTask,
  id: 2,
  title: 'In Progress Task',
  state: 'In Progress',
}

const mockValue: Value = {
  id: 1,
  statement: 'Test Value',
  archived: false,
  created_at: new Date().toISOString(),
  archived_at: null,
}

describe('WhatNext Page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(valueApi.list).mockResolvedValue(mockAxiosResponse([mockValue]))
  })

  it('renders without errors when no in-progress tasks and has suggestion', async () => {
    vi.mocked(taskApi.list).mockResolvedValue(mockAxiosResponse([]))
    vi.mocked(suggestionApi.getNext).mockResolvedValue(mockAxiosResponse(mockTask))

    render(<WhatNext />)
    
    await waitFor(() => {
      expect(screen.getByText('What Next?')).toBeInTheDocument()
    })
  })

  it('displays In-Progress prompt when In-Progress tasks exist', async () => {
    vi.mocked(taskApi.list).mockResolvedValue(mockAxiosResponse([mockInProgressTask]))

    render(<WhatNext />)

    await waitFor(() => {
      expect(screen.getByText(/You were working on/i)).toBeInTheDocument()
      expect(screen.getByText(/In Progress Task/i)).toBeInTheDocument()
      expect(screen.getByText('Continue this')).toBeInTheDocument()
      expect(screen.getByText('Suggest something else')).toBeInTheDocument()
    })
  })

  it('navigates to In Progress view when Continue is clicked', async () => {
    vi.mocked(taskApi.list).mockResolvedValue(mockAxiosResponse([mockInProgressTask]))

    render(<WhatNext />)

    await waitFor(() => {
      expect(screen.getByText('Continue this')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Continue this'))
    expect(mockNavigate).toHaveBeenCalledWith('/tasks?state=In+Progress')
  })

  it('fetches suggestion when Suggest something else is clicked', async () => {
    vi.mocked(taskApi.list).mockResolvedValue(mockAxiosResponse([mockInProgressTask]))
    vi.mocked(suggestionApi.getNext).mockResolvedValue(mockAxiosResponse(mockTask))

    render(<WhatNext />)

    await waitFor(() => {
      expect(screen.getByText('Suggest something else')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Suggest something else'))

    await waitFor(() => {
      expect(suggestionApi.getNext).toHaveBeenCalled()
      expect(screen.getByText('How about working on this?')).toBeInTheDocument()
    })
  })

  it('displays suggestion with task details', async () => {
    vi.mocked(taskApi.list).mockResolvedValue(mockAxiosResponse([]))
    vi.mocked(suggestionApi.getNext).mockResolvedValue(mockAxiosResponse(mockTask))

    render(<WhatNext />)

    await waitFor(() => {
      expect(screen.getByText('Test Task')).toBeInTheDocument()
      expect(screen.getByText(/Impact: A/i)).toBeInTheDocument()
      expect(screen.getByText(/Urgency: 1/i)).toBeInTheDocument()
      expect(screen.getByText('Test Value')).toBeInTheDocument()
      expect(screen.getByText("I'll start this now")).toBeInTheDocument()
      expect(screen.getByText('Not now, suggest another')).toBeInTheDocument()
      expect(screen.getByText("I'll take a break")).toBeInTheDocument()
    })
  })

  it('starts task and navigates when Start is clicked', async () => {
    vi.mocked(taskApi.list).mockResolvedValue(mockAxiosResponse([]))
    vi.mocked(suggestionApi.getNext).mockResolvedValue(mockAxiosResponse(mockTask))
    vi.mocked(taskApi.update).mockResolvedValue(mockAxiosResponse({ ...mockTask, state: 'In Progress' }))

    render(<WhatNext />)

    await waitFor(() => {
      expect(screen.getByText("I'll start this now")).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText("I'll start this now"))

    await waitFor(() => {
      expect(taskApi.update).toHaveBeenCalledWith(mockTask.id, { state: 'In Progress' })
    })

    // Wait for navigation (happens after 1s delay)
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/tasks?state=In+Progress')
    }, { timeout: 2000 })
  })

  it('rejects task and fetches new suggestion', async () => {
    const secondTask = { ...mockTask, id: 3, title: 'Second Task' }
    vi.mocked(taskApi.list).mockResolvedValue(mockAxiosResponse([]))
    vi.mocked(suggestionApi.getNext)
      .mockResolvedValueOnce(mockAxiosResponse(mockTask))
      .mockResolvedValueOnce(mockAxiosResponse(secondTask))
    vi.mocked(suggestionApi.reject).mockResolvedValue(mockAxiosResponse({}))

    render(<WhatNext />)

    await waitFor(() => {
      expect(screen.getByText('Test Task')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Not now, suggest another'))

    await waitFor(() => {
      expect(suggestionApi.reject).toHaveBeenCalledWith(mockTask.id)
      expect(suggestionApi.getNext).toHaveBeenCalledTimes(2)
      expect(screen.getByText('Second Task')).toBeInTheDocument()
    })
  })

  it('clears rejections and navigates when taking break', async () => {
    vi.mocked(taskApi.list).mockResolvedValue(mockAxiosResponse([]))
    vi.mocked(suggestionApi.getNext).mockResolvedValue(mockAxiosResponse(mockTask))
    vi.mocked(suggestionApi.break).mockResolvedValue(mockAxiosResponse({}))

    render(<WhatNext />)

    await waitFor(() => {
      expect(screen.getByText("I'll take a break")).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText("I'll take a break"))

    await waitFor(() => {
      expect(suggestionApi.break).toHaveBeenCalled()
    })

    // Wait for navigation (happens after 1.5s delay)
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/tasks')
    }, { timeout: 2000 })
  })

  it('displays no suggestions state when none available', async () => {
    vi.mocked(taskApi.list).mockResolvedValue(mockAxiosResponse([]))
    vi.mocked(suggestionApi.getNext).mockRejectedValue(new Error('No tasks available'))

    render(<WhatNext />)

    await waitFor(() => {
      expect(screen.getByText(/No task suggestions available/i)).toBeInTheDocument()
      expect(screen.getByText('View all tasks')).toBeInTheDocument()
    })
  })

  it('displays error state on API failure', async () => {
    vi.mocked(taskApi.list).mockRejectedValue(new Error('API Error'))

    render(<WhatNext />)

    await waitFor(() => {
      expect(screen.getByText(/Error:/i)).toBeInTheDocument()
      expect(screen.getByText(/API Error/i)).toBeInTheDocument()
      expect(screen.getByText('Retry')).toBeInTheDocument()
    })
  })
})
