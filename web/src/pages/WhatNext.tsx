import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { suggestionApi, taskApi, valueApi } from '../api/client'
import type { Task } from '../types/task'
import type { Value } from '../types/value'
import { getErrorMessage } from '../utils/errors'

type FlowState = 'checking-in-progress' | 'suggesting' | 'no-suggestions' | 'taking-break'

export default function WhatNext() {
  const navigate = useNavigate()
  const [flowState, setFlowState] = useState<FlowState>('checking-in-progress')
  const [inProgressTasks, setInProgressTasks] = useState<Task[]>([])
  const [currentSuggestion, setCurrentSuggestion] = useState<Task | null>(null)
  const [values, setValues] = useState<Value[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [notification, setNotification] = useState<string | null>(null)

  // Auto-dismiss notifications after 5 seconds
  useEffect(() => {
    let notificationTimeout: ReturnType<typeof setTimeout> | null = null
    
    if (notification) {
      notificationTimeout = setTimeout(() => setNotification(null), 5000)
    }
    
    return () => {
      if (notificationTimeout) {
        clearTimeout(notificationTimeout)
      }
    }
  }, [notification])

  // Load values (for displaying value pills)
  useEffect(() => {
    const loadValues = async () => {
      try {
        const response = await valueApi.list(false)
        setValues(response.data)
      } catch (err) {
        console.error('Error loading values:', err)
      }
    }
    loadValues()
  }, [])

  const fetchSuggestion = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await suggestionApi.getNext({})
      setCurrentSuggestion(response.data)
      setFlowState('suggesting')
    } catch (err) {
      const message = getErrorMessage(err)
      if (message.includes('No tasks available') || message.includes('no suggestions')) {
        setFlowState('no-suggestions')
      } else {
        setError(message)
      }
    } finally {
      setLoading(false)
    }
  }, [])

  // Check for In-Progress tasks on mount
  const checkInProgress = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await taskApi.list({ state: 'In Progress' })
      const tasks = response.data
      
      if (tasks.length > 0) {
        setInProgressTasks(tasks)
        setFlowState('checking-in-progress')
      } else {
        // No in-progress tasks, go straight to suggestion
        await fetchSuggestion()
      }
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [fetchSuggestion])

  useEffect(() => {
    checkInProgress()
  }, [checkInProgress])

  const handleContinueInProgress = () => {
    navigate('/tasks?state=In+Progress')
  }

  const handleSuggestAnother = async () => {
    await fetchSuggestion()
  }

  const handleStartTask = async () => {
    if (!currentSuggestion) return
    
    try {
      setLoading(true)
      await taskApi.update(currentSuggestion.id, { state: 'In Progress' })
      setNotification("Okay, let's go. I'll check in with you later.")
      
      // Navigate after brief delay to show notification
      setTimeout(() => {
        navigate('/tasks?state=In+Progress')
      }, 1000)
    } catch (err) {
      setError(getErrorMessage(err))
      setLoading(false)
    }
  }

  const handleReject = async () => {
    if (!currentSuggestion) return
    
    try {
      setLoading(true)
      await suggestionApi.reject(currentSuggestion.id)
      await fetchSuggestion()
    } catch (err) {
      setError(getErrorMessage(err))
      setLoading(false)
    }
  }

  const handleTakeBreak = async () => {
    try {
      setLoading(true)
      await suggestionApi.break()
      setNotification("Take your time. Come back when you're ready.")
      setFlowState('taking-break')
      
      // Navigate after brief delay to show notification
      setTimeout(() => {
        navigate('/tasks')
      }, 1500)
    } catch (err) {
      setError(getErrorMessage(err))
      setLoading(false)
    }
  }

  const getValueNames = (valueIds: number[] | undefined): string[] => {
    if (!valueIds || valueIds.length === 0) {
      return []
    }
    return valueIds
      .map(id => values.find(v => v.id === id)?.statement)
      .filter((name): name is string => name !== undefined)
  }

  const getImpactColor = (impact: Task['impact']): string => {
    switch (impact) {
      case 'A': return '#d32f2f' // Red
      case 'B': return '#f57c00' // Orange
      case 'C': return '#fbc02d' // Yellow
      case 'D': return '#388e3c' // Green
    }
  }

  const getUrgencyColor = (urgency: Task['urgency']): string => {
    switch (urgency) {
      case 1: return '#d32f2f' // Red
      case 2: return '#f57c00' // Orange
      case 3: return '#fbc02d' // Yellow
      case 4: return '#388e3c' // Green
    }
  }

  // Render loading state
  if (loading) {
    return (
      <div style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto', textAlign: 'center' }}>
        <h1>What Next?</h1>
        <p style={{ color: '#666', marginTop: '2rem' }}>Loading suggestions...</p>
      </div>
    )
  }

  // Render error state
  if (error) {
    return (
      <div style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
        <h1>What Next?</h1>
        <div style={{
          backgroundColor: '#fee',
          border: '1px solid #fcc',
          borderRadius: '4px',
          padding: '1rem',
          marginTop: '1rem',
          color: '#c33',
        }}>
          <strong>Error:</strong> {error}
        </div>
        <button
          onClick={() => window.location.reload()}
          style={{
            marginTop: '1rem',
            padding: '0.5rem 1rem',
            backgroundColor: '#007bff',
            color: '#fff',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
          }}
        >
          Retry
        </button>
      </div>
    )
  }

  // Notification banner
  const notificationBanner = notification && (
    <div style={{
      backgroundColor: '#d4edda',
      border: '1px solid #c3e6cb',
      borderRadius: '4px',
      padding: '1rem',
      marginBottom: '1rem',
      color: '#155724',
    }}>
      {notification}
    </div>
  )

  // State: checking-in-progress
  if (flowState === 'checking-in-progress' && inProgressTasks.length > 0) {
    const task = inProgressTasks[0] // Show first in-progress task
    return (
      <div style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
        <h1>What Next?</h1>
        {notificationBanner}
        <div style={{
          backgroundColor: '#fff3cd',
          border: '1px solid #ffeaa7',
          borderRadius: '8px',
          padding: '1.5rem',
          marginTop: '1rem',
        }}>
          <p style={{ fontSize: '1.1rem', marginBottom: '1rem', color: '#856404' }}>
            You were working on <strong>{task.title}</strong>. Continue with that, or would you like a different suggestion?
          </p>
          <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}>
            <button
              onClick={handleContinueInProgress}
              style={{
                flex: 1,
                padding: '0.75rem 1.5rem',
                backgroundColor: '#4CAF50',
                color: '#fff',
                border: 'none',
                borderRadius: '4px',
                fontSize: '1rem',
                cursor: 'pointer',
                transition: 'transform 0.1s',
              }}
              onMouseEnter={(e) => e.currentTarget.style.transform = 'translateY(-1px)'}
              onMouseLeave={(e) => e.currentTarget.style.transform = 'translateY(0)'}
            >
              Continue this
            </button>
            <button
              onClick={handleSuggestAnother}
              style={{
                flex: 1,
                padding: '0.75rem 1.5rem',
                backgroundColor: '#007bff',
                color: '#fff',
                border: 'none',
                borderRadius: '4px',
                fontSize: '1rem',
                cursor: 'pointer',
                transition: 'transform 0.1s',
              }}
              onMouseEnter={(e) => e.currentTarget.style.transform = 'translateY(-1px)'}
              onMouseLeave={(e) => e.currentTarget.style.transform = 'translateY(0)'}
            >
              Suggest something else
            </button>
          </div>
        </div>
      </div>
    )
  }

  // State: suggesting
  if (flowState === 'suggesting' && currentSuggestion) {
    const valueNames = getValueNames(currentSuggestion.value_ids)
    
    return (
      <div style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
        <h1>What Next?</h1>
        {notificationBanner}
        <div style={{
          backgroundColor: '#fff',
          border: '1px solid #ddd',
          borderRadius: '8px',
          padding: '2rem',
          marginTop: '1rem',
        }}>
          <p style={{ fontSize: '1.1rem', color: '#666', marginBottom: '1.5rem' }}>
            How about working on this?
          </p>
          
          {/* Task title */}
          <h2 style={{ fontSize: '1.5rem', marginBottom: '1rem', color: '#333' }}>
            {currentSuggestion.title}
          </h2>
          
          {/* Impact and Urgency badges */}
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
            <span style={{
              padding: '0.25rem 0.75rem',
              borderRadius: '12px',
              fontSize: '0.875rem',
              fontWeight: 'bold',
              backgroundColor: getImpactColor(currentSuggestion.impact),
              color: '#fff',
            }}>
              Impact: {currentSuggestion.impact}
            </span>
            <span style={{
              padding: '0.25rem 0.75rem',
              borderRadius: '12px',
              fontSize: '0.875rem',
              fontWeight: 'bold',
              backgroundColor: getUrgencyColor(currentSuggestion.urgency),
              color: '#fff',
            }}>
              Urgency: {currentSuggestion.urgency}
            </span>
          </div>
          
          {/* Value pills */}
          {valueNames.length > 0 && (
            <div style={{ marginBottom: '1.5rem' }}>
              <p style={{ fontSize: '0.875rem', color: '#666', marginBottom: '0.5rem' }}>
                Linked to values:
              </p>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                {valueNames.map((name, idx) => (
                  <span
                    key={idx}
                    style={{
                      padding: '0.25rem 0.75rem',
                      borderRadius: '12px',
                      fontSize: '0.875rem',
                      backgroundColor: '#e3f2fd',
                      color: '#1976d2',
                    }}
                  >
                    {name}
                  </span>
                ))}
              </div>
            </div>
          )}
          
          {/* Due date (if set) */}
          {currentSuggestion.due_date && (
            <p style={{ fontSize: '0.875rem', color: '#666', marginBottom: '1.5rem' }}>
              Due: {new Date(currentSuggestion.due_date).toLocaleDateString()}
            </p>
          )}
          
          {/* Action buttons */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginTop: '2rem' }}>
            <button
              onClick={handleStartTask}
              style={{
                padding: '1rem 1.5rem',
                backgroundColor: '#4CAF50',
                color: '#fff',
                border: 'none',
                borderRadius: '4px',
                fontSize: '1.1rem',
                fontWeight: 'bold',
                cursor: 'pointer',
                transition: 'transform 0.1s',
              }}
              onMouseEnter={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
              onMouseLeave={(e) => e.currentTarget.style.transform = 'translateY(0)'}
            >
              I&apos;ll start this now
            </button>
            
            <button
              onClick={handleReject}
              style={{
                padding: '0.75rem 1.5rem',
                backgroundColor: '#fff',
                color: '#007bff',
                border: '1px solid #007bff',
                borderRadius: '4px',
                fontSize: '1rem',
                cursor: 'pointer',
                transition: 'all 0.1s',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#007bff'
                e.currentTarget.style.color = '#fff'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = '#fff'
                e.currentTarget.style.color = '#007bff'
              }}
            >
              Not now, suggest another
            </button>
            
            <button
              onClick={handleTakeBreak}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: 'transparent',
                color: '#666',
                border: 'none',
                fontSize: '0.9rem',
                cursor: 'pointer',
                textDecoration: 'underline',
              }}
              onMouseEnter={(e) => e.currentTarget.style.color = '#999'}
              onMouseLeave={(e) => e.currentTarget.style.color = '#666'}
            >
              I&apos;ll take a break
            </button>
          </div>
        </div>
      </div>
    )
  }

  // State: no-suggestions
  if (flowState === 'no-suggestions') {
    return (
      <div style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto', textAlign: 'center' }}>
        <h1>What Next?</h1>
        <div style={{
          backgroundColor: '#f8f9fa',
          border: '1px solid #dee2e6',
          borderRadius: '8px',
          padding: '2rem',
          marginTop: '2rem',
        }}>
          <p style={{ fontSize: '1.1rem', color: '#666', marginBottom: '1rem' }}>
            No task suggestions available right now.
          </p>
          <p style={{ fontSize: '0.95rem', color: '#999' }}>
            All available tasks have been reviewed, or there are no tasks matching your current priorities.
          </p>
          <button
            onClick={() => navigate('/tasks')}
            style={{
              marginTop: '1.5rem',
              padding: '0.75rem 1.5rem',
              backgroundColor: '#007bff',
              color: '#fff',
              border: 'none',
              borderRadius: '4px',
              fontSize: '1rem',
              cursor: 'pointer',
            }}
          >
            View all tasks
          </button>
        </div>
      </div>
    )
  }

  // Fallback (should not reach here)
  return (
    <div style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
      <h1>What Next?</h1>
      <p>Loading...</p>
    </div>
  )
}
