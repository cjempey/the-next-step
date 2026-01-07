import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from './App'

describe('App', () => {
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
})
