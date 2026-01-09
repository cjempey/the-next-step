import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import MorningPlanning from './MorningPlanning'

describe('MorningPlanning Page', () => {
  it('renders without errors', () => {
    render(<MorningPlanning />)
    expect(screen.getByText('Morning Planning')).toBeInTheDocument()
  })

  it('displays the correct heading', () => {
    render(<MorningPlanning />)
    const heading = screen.getByRole('heading', { level: 1 })
    expect(heading).toHaveTextContent('Morning Planning')
  })

  it('displays the placeholder description', () => {
    render(<MorningPlanning />)
    expect(screen.getByText(/planning tasks and setting intentions aligned with your values/i)).toBeInTheDocument()
  })

  it('displays the coming soon message', () => {
    render(<MorningPlanning />)
    expect(screen.getByText(/Coming soon/i)).toBeInTheDocument()
  })
})
