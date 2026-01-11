import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import TaskEntry from './TaskEntry'
import * as apiClient from '../api/client'

// Mock the API client
vi.mock('../api/client', () => ({
  taskApi: {
    list: vi.fn(),
    create: vi.fn(),
  },
  valueApi: {
    list: vi.fn(),
  },
}))

// Mock the store
vi.mock('../store/useStore', () => ({
  useStore: vi.fn(() => ({
    tasks: [],
    setTasks: vi.fn(),
    addTask: vi.fn(),
  })),
}))

describe('TaskEntry Page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Setup default mocks - return Promises that resolve to AxiosResponse
    vi.mocked(apiClient.valueApi.list).mockResolvedValue({ 
      data: [],
      status: 200,
      statusText: 'OK',
      headers: {},
      config: {} as any,
    })
    vi.mocked(apiClient.taskApi.list).mockResolvedValue({ 
      data: [],
      status: 200,
      statusText: 'OK',
      headers: {},
      config: {} as any,
    })
  })

  it('renders without errors', async () => {
    render(
      <BrowserRouter>
        <TaskEntry />
      </BrowserRouter>
    )
    expect(screen.getByText('New Task')).toBeInTheDocument()
  })

  it('displays the correct heading', async () => {
    render(
      <BrowserRouter>
        <TaskEntry />
      </BrowserRouter>
    )
    const heading = screen.getByRole('heading', { level: 1, name: 'New Task' })
    expect(heading).toBeInTheDocument()
  })

  it('displays all required form fields', async () => {
    render(
      <BrowserRouter>
        <TaskEntry />
      </BrowserRouter>
    )

    // Check for all form fields
    expect(screen.getByLabelText(/Task Title/i)).toBeInTheDocument()
    expect(screen.getByText(/Values \(optional\)/i)).toBeInTheDocument()
    expect(screen.getByText(/Impact \(optional, defaults to B\)/i)).toBeInTheDocument()
    expect(screen.getByText(/Urgency \(optional, defaults to 3\)/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Due Date/i)).toBeInTheDocument()
    expect(screen.getByText(/Recurrence \(optional, defaults to none\)/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Description\/Notes/i)).toBeInTheDocument()
  })

  it('displays save and cancel buttons', async () => {
    render(
      <BrowserRouter>
        <TaskEntry />
      </BrowserRouter>
    )

    expect(screen.getByRole('button', { name: /Save Task/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Cancel/i })).toBeInTheDocument()
  })

  it('shows loading state for values', async () => {
    render(
      <BrowserRouter>
        <TaskEntry />
      </BrowserRouter>
    )

    // Should show loading initially
    expect(screen.getByText(/Loading values/i)).toBeInTheDocument()

    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByText(/Loading values/i)).not.toBeInTheDocument()
    })
  })

  it('shows message when no values exist', async () => {
    render(
      <BrowserRouter>
        <TaskEntry />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/No values defined yet/i)).toBeInTheDocument()
    })
  })

  it('displays task list preview section', async () => {
    render(
      <BrowserRouter>
        <TaskEntry />
      </BrowserRouter>
    )

    expect(screen.getByRole('heading', { level: 2, name: 'Your Tasks' })).toBeInTheDocument()
  })

  it('shows message when no tasks exist', async () => {
    render(
      <BrowserRouter>
        <TaskEntry />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/No tasks yet/i)).toBeInTheDocument()
    })
  })

  it('has default values for impact and urgency', async () => {
    render(
      <BrowserRouter>
        <TaskEntry />
      </BrowserRouter>
    )

    // Check that B is selected for impact (default)
    const impactB = screen.getByRole('radio', { name: /B: Moderately aligned/i })
    expect(impactB).toBeChecked()

    // Check that 3 is selected for urgency (default)
    const urgency3 = screen.getByRole('radio', { name: /3: Can be deferred/i })
    expect(urgency3).toBeChecked()

    // Check that "none" is selected for recurrence (default)
    const recurrenceNone = screen.getByRole('radio', { name: /None/i })
    expect(recurrenceNone).toBeChecked()
  })
})
