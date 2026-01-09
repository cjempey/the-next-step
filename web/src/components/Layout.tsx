import React, { useState, useEffect, useRef } from 'react'
import Navigation from './Navigation'
import { HamburgerIcon, CloseIcon } from './Icons'
import styles from './Layout.module.css'

interface LayoutProps {
  children: React.ReactNode
}

export default function Layout({ children }: LayoutProps) {
  // Initialize sidebarOpen based on viewport to avoid flash on desktop
  const [sidebarOpen, setSidebarOpen] = useState(() => {
    if (typeof window !== 'undefined') {
      return window.innerWidth >= 768
    }
    return false
  })

  const [isMobile, setIsMobile] = useState(() => {
    if (typeof window !== 'undefined') {
      return window.innerWidth < 768
    }
    return false
  })

  const sidebarRef = useRef<HTMLDivElement>(null)
  const hamburgerButtonRef = useRef<HTMLButtonElement>(null)

  // Track viewport size for mobile/desktop detection
  useEffect(() => {
    const handleResize = () => {
      const mobile = window.innerWidth < 768
      setIsMobile(mobile)
      // On desktop, keep sidebar open
      if (!mobile) {
        setSidebarOpen(true)
      }
    }

    handleResize()
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  // Handle Escape key to close mobile sidebar
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && sidebarOpen && isMobile) {
        setSidebarOpen(false)
        hamburgerButtonRef.current?.focus()
      }
    }

    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [sidebarOpen, isMobile])

  // Focus trapping in mobile sidebar
  useEffect(() => {
    if (!sidebarOpen || !isMobile) return

    const sidebar = sidebarRef.current
    if (!sidebar) return

    const focusableElements = sidebar.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    )
    const firstElement = focusableElements[0]
    const lastElement = focusableElements[focusableElements.length - 1]

    const handleTabKey = (event: KeyboardEvent) => {
      if (event.key !== 'Tab') return

      if (event.shiftKey) {
        if (document.activeElement === firstElement) {
          lastElement?.focus()
          event.preventDefault()
        }
      } else {
        if (document.activeElement === lastElement) {
          firstElement?.focus()
          event.preventDefault()
        }
      }
    }

    document.addEventListener('keydown', handleTabKey)
    firstElement?.focus()

    return () => document.removeEventListener('keydown', handleTabKey)
  }, [sidebarOpen, isMobile])

  const handleCloseSidebar = () => {
    if (isMobile) {
      setSidebarOpen(false)
      hamburgerButtonRef.current?.focus()
    }
  }

  return (
    <div className={styles.layout}>
      {/* Sidebar - Desktop */}
      <aside className={styles.sidebarDesktop}>
        <Navigation onNavigate={() => setSidebarOpen(false)} />
      </aside>

      {/* Main content area */}
      <div className={styles.mainContent}>
        {/* Header */}
        <header className={styles.header}>
          {/* Hamburger menu button */}
          <button
            ref={hamburgerButtonRef}
            onClick={() => setSidebarOpen(!sidebarOpen)}
            aria-label="Toggle navigation menu"
            aria-expanded={sidebarOpen}
            className={styles.hamburgerButton}
          >
            <HamburgerIcon />
          </button>
          <h1 className={styles.headerTitle}>The Next Step</h1>
        </header>

        {/* Page content */}
        <main className={styles.pageContent}>{children}</main>
      </div>

      {/* Overlay for mobile when sidebar is open */}
      {sidebarOpen && isMobile && (
        <div
          onClick={handleCloseSidebar}
          className={styles.overlay}
          role="button"
          tabIndex={-1}
          aria-label="Close navigation menu"
        />
      )}

      {/* Sidebar - Mobile (positioned absolutely) */}
      {sidebarOpen && isMobile && (
        <aside ref={sidebarRef} className={styles.sidebarMobile} role="dialog" aria-modal="true" aria-label="Navigation menu">
          <div className={styles.mobileHeader}>
            <h2 className={styles.mobileTitle}>Menu</h2>
            <button onClick={handleCloseSidebar} aria-label="Close navigation menu" className={styles.closeButton}>
              <CloseIcon />
            </button>
          </div>
          <Navigation onNavigate={handleCloseSidebar} />
        </aside>
      )}
    </div>
  )
}
