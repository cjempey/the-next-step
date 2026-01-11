import { Link, useLocation } from 'react-router-dom'

interface NavigationProps {
  onNavigate?: () => void
}

const navItems = [
  { path: '/tasks', label: 'Tasks' },
  { path: '/tasks/new', label: 'New Task' },
  { path: '/values', label: 'Values' },
  { path: '/morning-planning', label: 'Morning Planning' },
  { path: '/evening-review', label: 'Evening Review' },
  { path: '/what-next', label: 'What Next' },
]

export default function Navigation({ onNavigate }: NavigationProps) {
  const location = useLocation()

  const isActive = (path: string) => location.pathname === path

  return (
    <nav>
      <ul style={{ listStyle: 'none', padding: 0 }}>
        {navItems.map((item) => (
          <li key={item.path} style={{ marginBottom: '0.5rem' }}>
            <Link
              to={item.path}
              onClick={onNavigate}
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
  )
}
