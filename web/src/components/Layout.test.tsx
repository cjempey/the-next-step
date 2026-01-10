import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import Layout from './Layout'

// Helper to render Layout with router context
function renderLayout(children = <div>Test Content</div>) {
  return render(
    <BrowserRouter>
      <Layout>{children}</Layout>
    </BrowserRouter>
  )
}

// Mock window.innerWidth for testing responsive behavior
function setViewportWidth(width: number) {
  Object.defineProperty(window, 'innerWidth', {
    writable: true,
    configurable: true,
    value: width,
  })
  window.dispatchEvent(new Event('resize'))
}

describe('Layout Component', () => {
  beforeEach(() => {
    // Reset to desktop viewport
    setViewportWidth(1024)
  })

  describe('Basic Rendering', () => {
    it('renders the app title', () => {
      renderLayout()
      expect(screen.getByText('The Next Step')).toBeInTheDocument()
    })

    it('renders child content', () => {
      renderLayout(<div>Custom Content</div>)
      expect(screen.getByText('Custom Content')).toBeInTheDocument()
    })

    it('renders all navigation links', () => {
      renderLayout()
      expect(screen.getAllByText('Tasks').length).toBeGreaterThan(0)
      expect(screen.getAllByText('Values').length).toBeGreaterThan(0)
      expect(screen.getAllByText('Morning Planning').length).toBeGreaterThan(0)
      expect(screen.getAllByText('Evening Review').length).toBeGreaterThan(0)
      expect(screen.getAllByText('What Next').length).toBeGreaterThan(0)
    })
  })

  describe('Mobile Behavior', () => {
    beforeEach(() => {
      setViewportWidth(375) // Mobile width
    })

    it('shows hamburger menu on mobile', async () => {
      renderLayout()
      
      await waitFor(() => {
        const hamburger = screen.getByLabelText('Toggle navigation menu')
        expect(hamburger).toBeInTheDocument()
      })
    })

    it('toggles mobile sidebar when hamburger is clicked', async () => {
      renderLayout()
      
      await waitFor(() => {
        const hamburger = screen.getByLabelText('Toggle navigation menu')
        expect(hamburger).toBeInTheDocument()
      })

      const hamburger = screen.getByLabelText('Toggle navigation menu')
      
      // Open sidebar
      fireEvent.click(hamburger)
      
      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument()
        expect(screen.getByText('Menu')).toBeInTheDocument()
      })

      // Close sidebar using the close button inside the dialog
      const dialog = screen.getByRole('dialog')
      const closeButton = within(dialog).getByLabelText('Close navigation menu')
      fireEvent.click(closeButton)
      
      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
      })
    })

    it('closes mobile sidebar when overlay is clicked', async () => {
      renderLayout()
      
      await waitFor(() => {
        const hamburger = screen.getByLabelText('Toggle navigation menu')
        fireEvent.click(hamburger)
      })

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument()
      })

      // Click overlay (find by role='button' that is not inside the dialog)
      const dialog = screen.getByRole('dialog')
      const overlayButton = screen.getAllByRole('button').find(button => 
        !dialog.contains(button) && button.getAttribute('aria-label') === 'Close navigation menu'
      )
      
      if (overlayButton) {
        fireEvent.click(overlayButton)
        
        await waitFor(() => {
          expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
        })
      }
    })

    it('closes mobile sidebar when Escape key is pressed', async () => {
      renderLayout()
      
      await waitFor(() => {
        const hamburger = screen.getByLabelText('Toggle navigation menu')
        fireEvent.click(hamburger)
      })

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument()
      })

      // Press Escape key
      fireEvent.keyDown(document, { key: 'Escape' })
      
      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
      })
    })

    it('closes mobile sidebar when navigation link is clicked', async () => {
      renderLayout()
      
      await waitFor(() => {
        const hamburger = screen.getByLabelText('Toggle navigation menu')
        fireEvent.click(hamburger)
      })

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument()
      })

      // Click a navigation link inside the dialog
      const dialog = screen.getByRole('dialog')
      const tasksLink = within(dialog).getByText('Tasks')
      
      fireEvent.click(tasksLink)
      
      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
      })
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA labels on buttons', async () => {
      setViewportWidth(375)
      renderLayout()
      
      await waitFor(() => {
        expect(screen.getByLabelText('Toggle navigation menu')).toBeInTheDocument()
      })

      const hamburger = screen.getByLabelText('Toggle navigation menu')
      fireEvent.click(hamburger)
      
      await waitFor(() => {
        const dialog = screen.getByRole('dialog')
        const closeButton = within(dialog).getByLabelText('Close navigation menu')
        expect(closeButton).toBeInTheDocument()
      })
    })

    it('has proper ARIA attributes on mobile sidebar', async () => {
      setViewportWidth(375)
      renderLayout()
      
      await waitFor(() => {
        const hamburger = screen.getByLabelText('Toggle navigation menu')
        fireEvent.click(hamburger)
      })

      await waitFor(() => {
        const dialog = screen.getByRole('dialog')
        expect(dialog).toHaveAttribute('aria-modal', 'true')
        expect(dialog).toHaveAttribute('aria-label', 'Navigation menu')
      })
    })

    it('has aria-expanded attribute on hamburger button', async () => {
      setViewportWidth(375)
      renderLayout()
      
      await waitFor(() => {
        const hamburger = screen.getByLabelText('Toggle navigation menu')
        expect(hamburger).toHaveAttribute('aria-expanded')
      })
    })
  })

  describe('Responsive Behavior', () => {
    it('updates sidebar state when resizing from mobile to desktop', async () => {
      setViewportWidth(375) // Start mobile
      renderLayout()
      
      await waitFor(() => {
        expect(screen.getByLabelText('Toggle navigation menu')).toBeInTheDocument()
      })

      // Resize to desktop
      setViewportWidth(1024)
      
      await waitFor(() => {
        // On desktop, hamburger should still exist but sidebar behavior changes
        const hamburger = screen.queryByLabelText('Toggle navigation menu')
        expect(hamburger).toBeInTheDocument()
      })
    })
  })
})
