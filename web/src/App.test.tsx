import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import App from './App'
import * as apiClient from './api/client'

// Mock the API client for TaskEntry page
vi.mock('./api/client', () => ({
  taskApi: {
    list: vi.fn(),
    create: vi.fn(),
  },
  valueApi: {
    list: vi.fn(),
  },
}))

describe('App', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Setup default mocks
    vi.mocked(apiClient.valueApi.list).mockResolvedValue({ 
      data: [],
      status: 200,
      statusText: 'OK',
      headers: {},
      config: {
        headers: {},
      } as never,
    })
    vi.mocked(apiClient.taskApi.list).mockResolvedValue({ 
      data: [],
      status: 200,
      statusText: 'OK',
      headers: {},
      config: {
        headers: {},
      } as never,
    })
  })
  it('renders without crashing', () => {
    render(<App />)
    // Check that the app title is rendered
    expect(screen.getByText('The Next Step')).toBeInTheDocument()
  })

  it('renders the default route (tasks page)', () => {
    render(<App />)
    // Should redirect to /tasks by default
    expect(screen.getByText('Task List')).toBeInTheDocument()
  })

  describe('Routing', () => {
    it('navigates to Values page', async () => {
      render(<App />)
      
      const valuesLinks = screen.getAllByText('Values')
      fireEvent.click(valuesLinks[0])
      
      await waitFor(() => {
        expect(screen.getByText('My Values')).toBeInTheDocument()
      })
    })

    it('navigates to Morning Planning page', async () => {
      render(<App />)
      
      const morningLinks = screen.getAllByText('Morning Planning')
      fireEvent.click(morningLinks[0])
      
      await waitFor(() => {
        const headings = screen.getAllByText('Morning Planning')
        // Should have the link and the page heading
        expect(headings.length).toBeGreaterThan(1)
      })
    })

    it('navigates to Evening Review page', async () => {
      render(<App />)
      
      const eveningLinks = screen.getAllByText('Evening Review')
      fireEvent.click(eveningLinks[0])
      
      await waitFor(() => {
        const headings = screen.getAllByText('Evening Review')
        // Should have the link and the page heading
        expect(headings.length).toBeGreaterThan(1)
      })
    })

    it('navigates to New Task page', async () => {
      render(<App />)
      
      const newTaskLinks = screen.getAllByText('New Task')
      fireEvent.click(newTaskLinks[0])
      
      await waitFor(() => {
        const headings = screen.getAllByText('New Task')
        // Should have the link and the page heading
        expect(headings.length).toBeGreaterThan(1)
      })
    })

    it('navigates back to Tasks page', async () => {
      render(<App />)
      
      // Navigate away
      const valuesLinks = screen.getAllByText('Values')
      fireEvent.click(valuesLinks[0])
      
      await waitFor(() => {
        expect(screen.getByText('My Values')).toBeInTheDocument()
      })

      // Navigate back
      const tasksLinks = screen.getAllByText('Tasks')
      fireEvent.click(tasksLinks[0])
      
      await waitFor(() => {
        expect(screen.getByText('Task List')).toBeInTheDocument()
      })
    })
  })

  describe('Navigation', () => {
    it('shows all navigation links', () => {
      render(<App />)
      
      expect(screen.getAllByText('Tasks').length).toBeGreaterThan(0)
      expect(screen.getAllByText('New Task').length).toBeGreaterThan(0)
      expect(screen.getAllByText('Values').length).toBeGreaterThan(0)
      expect(screen.getAllByText('Morning Planning').length).toBeGreaterThan(0)
      expect(screen.getAllByText('Evening Review').length).toBeGreaterThan(0)
      expect(screen.getAllByText('What Next').length).toBeGreaterThan(0)
    })
  })
})
