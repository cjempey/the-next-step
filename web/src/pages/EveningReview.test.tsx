import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import EveningReview from './EveningReview'

describe('EveningReview Page', () => {
  it('renders without errors', () => {
    render(<EveningReview />)
    expect(screen.getByText('Evening Review')).toBeInTheDocument()
  })

  it('displays the correct heading', () => {
    render(<EveningReview />)
    const heading = screen.getByRole('heading', { level: 1 })
    expect(heading).toHaveTextContent('Evening Review')
  })

  it('displays the placeholder description', () => {
    render(<EveningReview />)
    expect(screen.getByText(/review completed tasks, and celebrate progress/i)).toBeInTheDocument()
  })

  it('displays the coming soon message', () => {
    render(<EveningReview />)
    expect(screen.getByText(/Coming soon/i)).toBeInTheDocument()
  })
})
