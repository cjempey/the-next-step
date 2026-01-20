import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { TaskCard } from './TaskCard'
import type { Task } from '../types/task'

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
  }

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
})
