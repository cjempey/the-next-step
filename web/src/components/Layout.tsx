import React, { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'

interface LayoutProps {
  children: React.ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()

  const isActive = (path: string) => location.pathname === path

  const navItems = [
    { path: '/tasks', label: 'Tasks' },
    { path: '/values', label: 'Values' },
    { path: '/morning-planning', label: 'Morning Planning' },
    { path: '/evening-review', label: 'Evening Review' },
    { path: '/what-next', label: 'What Next' },
  ]

  return (
    <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: '#f5f5f5' }}>
      {/* Sidebar - Desktop */}
      <aside
        style={{
          width: '250px',
          backgroundColor: 'white',
          borderRight: '1px solid #ddd',
          padding: '1rem',
          display: sidebarOpen ? 'block' : 'none',
        }}
        className="sidebar-desktop"
      >
        <nav>
          <ul style={{ listStyle: 'none', padding: 0 }}>
            {navItems.map((item) => (
              <li key={item.path} style={{ marginBottom: '0.5rem' }}>
                <Link
                  to={item.path}
                  onClick={() => setSidebarOpen(false)}
                  style={{
                    display: 'block',
                    padding: '0.75rem 1rem',
                    textDecoration: 'none',
                    color: isActive(item.path) ? '#0066cc' : '#333',
                    backgroundColor: isActive(item.path) ? '#e6f2ff' : 'transparent',
                    borderRadius: '4px',
                    fontWeight: isActive(item.path) ? 'bold' : 'normal',
                  }}
                >
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      </aside>

      {/* Main content area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {/* Header */}
        <header
          style={{
            padding: '1rem 2rem',
            backgroundColor: 'white',
            borderBottom: '1px solid #ddd',
            display: 'flex',
            alignItems: 'center',
            gap: '1rem',
          }}
        >
          {/* Hamburger menu button */}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            aria-label="Toggle navigation menu"
            style={{
              display: 'block',
              padding: '0.5rem',
              backgroundColor: 'transparent',
              border: 'none',
              cursor: 'pointer',
              fontSize: '1.5rem',
            }}
            className="hamburger-button"
          >
            ☰
          </button>
          <h1 style={{ margin: 0, fontSize: '1.5rem' }}>The Next Step</h1>
        </header>

        {/* Page content */}
        <main style={{ flex: 1, overflowY: 'auto' }}>{children}</main>
      </div>

      {/* Overlay for mobile when sidebar is open */}
      {sidebarOpen && (
        <div
          onClick={() => setSidebarOpen(false)}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            zIndex: 998,
          }}
          className="sidebar-overlay"
        />
      )}

      {/* Sidebar - Mobile (positioned absolutely) */}
      {sidebarOpen && (
        <aside
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            bottom: 0,
            width: '250px',
            backgroundColor: 'white',
            borderRight: '1px solid #ddd',
            padding: '1rem',
            zIndex: 999,
            overflowY: 'auto',
          }}
          className="sidebar-mobile"
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h2 style={{ margin: 0, fontSize: '1.2rem' }}>Menu</h2>
            <button
              onClick={() => setSidebarOpen(false)}
              aria-label="Close navigation menu"
              style={{
                padding: '0.5rem',
                backgroundColor: 'transparent',
                border: 'none',
                cursor: 'pointer',
                fontSize: '1.5rem',
              }}
            >
              ✕
            </button>
          </div>
          <nav>
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {navItems.map((item) => (
                <li key={item.path} style={{ marginBottom: '0.5rem' }}>
                  <Link
                    to={item.path}
                    onClick={() => setSidebarOpen(false)}
                    style={{
                      display: 'block',
                      padding: '0.75rem 1rem',
                      textDecoration: 'none',
                      color: isActive(item.path) ? '#0066cc' : '#333',
                      backgroundColor: isActive(item.path) ? '#e6f2ff' : 'transparent',
                      borderRadius: '4px',
                      fontWeight: isActive(item.path) ? 'bold' : 'normal',
                    }}
                  >
                    {item.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        </aside>
      )}

      <style>{`
        /* Desktop sidebar - always visible on larger screens */
        @media (min-width: 768px) {
          .sidebar-desktop {
            display: block !important;
            position: static !important;
          }
          .sidebar-mobile {
            display: none !important;
          }
          .sidebar-overlay {
            display: none !important;
          }
          .hamburger-button {
            display: none !important;
          }
        }

        /* Mobile sidebar - hidden by default, shown when menu is open */
        @media (max-width: 767px) {
          .sidebar-desktop {
            display: none !important;
          }
        }
      `}</style>
    </div>
  )
}
