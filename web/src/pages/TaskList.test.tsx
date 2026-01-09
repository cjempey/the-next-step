import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import TaskList from './TaskList'

describe('TaskList Page', () => {
  it('renders without errors', () => {
    render(<TaskList />)
    expect(screen.getByText('Task List')).toBeInTheDocument()
  })

  it('displays the correct heading', () => {
    render(<TaskList />)
    const heading = screen.getByRole('heading', { level: 1 })
    expect(heading).toHaveTextContent('Task List')
  })

  it('displays the placeholder description', () => {
    render(<TaskList />)
    expect(screen.getByText(/View and manage your daily tasks/i)).toBeInTheDocument()
  })

  it('displays the coming soon message', () => {
    render(<TaskList />)
    expect(screen.getByText(/Coming soon/i)).toBeInTheDocument()
  })
})
