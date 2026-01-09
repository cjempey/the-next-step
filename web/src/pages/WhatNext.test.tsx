import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import WhatNext from './WhatNext'

describe('WhatNext Page', () => {
  it('renders without errors', () => {
    render(<WhatNext />)
    expect(screen.getByText('What Next?')).toBeInTheDocument()
  })

  it('displays the correct heading', () => {
    render(<WhatNext />)
    const heading = screen.getByRole('heading', { level: 1 })
    expect(heading).toHaveTextContent('What Next?')
  })

  it('displays the placeholder description', () => {
    render(<WhatNext />)
    expect(screen.getByText(/AI-powered suggestions for your next task/i)).toBeInTheDocument()
  })

  it('displays the coming soon message', () => {
    render(<WhatNext />)
    expect(screen.getByText(/Coming soon/i)).toBeInTheDocument()
  })
})
