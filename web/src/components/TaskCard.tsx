import { useState } from 'react'
import type { Task } from '../types/task'
import { taskApi } from '../api/client'
import { getErrorMessage } from '../utils/errors'

interface TaskCardProps {
  task: Task
  onTaskUpdate?: (updatedTask: Task) => void
  onNextInstanceCreated?: (newTask: Task) => void
}

// State transition button configurations
const stateTransitions: Record<Task['state'], Array<{ label: string; newState: Task['state']; confirmRequired: boolean }>> = {
  'Ready': [
    { label: 'Start', newState: 'In Progress', confirmRequired: false },
    { label: 'Block', newState: 'Blocked', confirmRequired: false },
    { label: 'Park', newState: 'Parked', confirmRequired: false },
    { label: 'Cancel', newState: 'Cancelled', confirmRequired: true },
  ],
  'In Progress': [
    { label: 'Complete', newState: 'Completed', confirmRequired: false },
    { label: 'Block', newState: 'Blocked', confirmRequired: false },
    { label: 'Park', newState: 'Parked', confirmRequired: false },
    { label: 'Cancel', newState: 'Cancelled', confirmRequired: true },
    { label: 'Mark Ready', newState: 'Ready', confirmRequired: false },
  ],
  'Blocked': [
    { label: 'Unblock', newState: 'Ready', confirmRequired: false },
    { label: 'Park', newState: 'Parked', confirmRequired: false },
    { label: 'Cancel', newState: 'Cancelled', confirmRequired: true },
  ],
  'Parked': [
    { label: 'Resume', newState: 'Ready', confirmRequired: false },
    { label: 'Cancel', newState: 'Cancelled', confirmRequired: true },
  ],
  'Completed': [],
  'Cancelled': [],
}

export function TaskCard({ task, onTaskUpdate, onNextInstanceCreated }: TaskCardProps) {
  const [currentTask, setCurrentTask] = useState<Task>(task)
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showConfirmDialog, setShowConfirmDialog] = useState<Task['state'] | null>(null)

  const transitions = stateTransitions[currentTask.state] || []
  const isFinalState = currentTask.state === 'Completed' || currentTask.state === 'Cancelled'

  const handleTransition = async (newState: Task['state']) => {
    setIsProcessing(true)
    setError(null)

    // Store previous state for rollback on error
    const previousTask = currentTask

    try {
      // Optimistic UI update
      setCurrentTask({ ...currentTask, state: newState })

      // Call API
      const response = await taskApi.transition(currentTask.id, { new_state: newState })
      
      // Update with actual response
      setCurrentTask(response.data.task)
      
      // Notify parent of update
      if (onTaskUpdate) {
        onTaskUpdate(response.data.task)
      }

      // If a next instance was created (recurring task), notify parent
      if (response.data.next_instance && onNextInstanceCreated) {
        onNextInstanceCreated(response.data.next_instance)
      }
    } catch (err: unknown) {
      // Revert optimistic update on error
      setCurrentTask(previousTask)
      
      // Show error message
      setError(getErrorMessage(err))
      console.error('Error transitioning task:', err)
    } finally {
      setIsProcessing(false)
      setShowConfirmDialog(null)
    }
  }

  const handleTransitionClick = (newState: Task['state'], confirmRequired: boolean) => {
    if (confirmRequired) {
      setShowConfirmDialog(newState)
    } else {
      handleTransition(newState)
    }
  }

  const handleConfirm = () => {
    if (showConfirmDialog) {
      handleTransition(showConfirmDialog)
    }
  }

  const handleCancel = () => {
    setShowConfirmDialog(null)
  }

  // Format date for display
  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return null
    try {
      return new Date(dateStr).toLocaleDateString()
    } catch {
      return dateStr
    }
  }

  return (
    <div style={{
      border: '1px solid #ddd',
      borderRadius: '8px',
      padding: '1rem',
      marginBottom: '1rem',
      backgroundColor: '#fff',
      boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    }}>
      <div style={{ marginBottom: '0.75rem' }}>
        <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.25rem' }}>{currentTask.title}</h3>
        {currentTask.description && (
          <p style={{ margin: '0 0 0.5rem 0', color: '#666', fontSize: '0.9rem' }}>
            {currentTask.description}
          </p>
        )}
        <div style={{ display: 'flex', gap: '1rem', fontSize: '0.875rem', color: '#666' }}>
          <span>
            <strong>State:</strong>{' '}
            <span style={{
              padding: '0.25rem 0.5rem',
              borderRadius: '4px',
              backgroundColor: getStateColor(currentTask.state),
              color: '#fff',
            }}>
              {currentTask.state}
            </span>
          </span>
          <span><strong>Impact:</strong> {currentTask.impact}</span>
          <span><strong>Urgency:</strong> {currentTask.urgency}</span>
          {currentTask.due_date && (
            <span><strong>Due:</strong> {formatDate(currentTask.due_date)}</span>
          )}
          {currentTask.recurrence !== 'none' && (
            <span><strong>Recurs:</strong> {currentTask.recurrence}</span>
          )}
        </div>
        {currentTask.notes && (
          <p style={{ margin: '0.5rem 0 0 0', fontSize: '0.875rem', fontStyle: 'italic', color: '#888' }}>
            Note: {currentTask.notes}
          </p>
        )}
      </div>

      {error && (
        <div style={{
          padding: '0.75rem',
          marginBottom: '0.75rem',
          backgroundColor: '#fee',
          border: '1px solid #fcc',
          borderRadius: '4px',
          color: '#c33',
          fontSize: '0.875rem',
        }}>
          {error}
        </div>
      )}

      {!isFinalState && transitions.length > 0 && (
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          {transitions.map(({ label, newState, confirmRequired }) => (
            <button
              key={newState}
              onClick={() => handleTransitionClick(newState, confirmRequired)}
              disabled={isProcessing}
              style={{
                padding: '0.5rem 1rem',
                fontSize: '0.875rem',
                fontWeight: 'bold',
                border: confirmRequired ? '2px solid #d33' : '1px solid #007bff',
                borderRadius: '4px',
                backgroundColor: confirmRequired ? '#fff' : '#007bff',
                color: confirmRequired ? '#d33' : '#fff',
                cursor: isProcessing ? 'not-allowed' : 'pointer',
                opacity: isProcessing ? 0.6 : 1,
                minWidth: '80px',
                transition: 'all 0.2s',
              }}
              onMouseEnter={(e) => {
                if (!isProcessing) {
                  e.currentTarget.style.transform = 'translateY(-1px)'
                  e.currentTarget.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)'
                }
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)'
                e.currentTarget.style.boxShadow = 'none'
              }}
            >
              {isProcessing ? '...' : label}
            </button>
          ))}
        </div>
      )}

      {isFinalState && (
        <div style={{ 
          padding: '0.5rem', 
          fontSize: '0.875rem', 
          color: '#666',
          fontStyle: 'italic' 
        }}>
          {currentTask.state === 'Completed' && currentTask.completion_percentage && (
            <span>Completed {currentTask.completion_percentage}%</span>
          )}
          {currentTask.state === 'Completed' && !currentTask.completion_percentage && (
            <span>Task completed</span>
          )}
          {currentTask.state === 'Cancelled' && <span>Task cancelled</span>}
        </div>
      )}

      {/* Confirmation Dialog */}
      {showConfirmDialog && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
        }}>
          <div style={{
            backgroundColor: '#fff',
            padding: '2rem',
            borderRadius: '8px',
            maxWidth: '400px',
            boxShadow: '0 4px 6px rgba(0,0,0,0.3)',
          }}>
            <h3 style={{ margin: '0 0 1rem 0' }}>Confirm Action</h3>
            <p style={{ margin: '0 0 1.5rem 0', color: '#666' }}>
              Are you sure you want to cancel this task? This action cannot be undone.
            </p>
            <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
              <button
                onClick={handleCancel}
                style={{
                  padding: '0.5rem 1rem',
                  border: '1px solid #ccc',
                  borderRadius: '4px',
                  backgroundColor: '#fff',
                  color: '#333',
                  cursor: 'pointer',
                }}
              >
                No, go back
              </button>
              <button
                onClick={handleConfirm}
                disabled={isProcessing}
                style={{
                  padding: '0.5rem 1rem',
                  border: 'none',
                  borderRadius: '4px',
                  backgroundColor: '#d33',
                  color: '#fff',
                  cursor: isProcessing ? 'not-allowed' : 'pointer',
                  opacity: isProcessing ? 0.6 : 1,
                }}
              >
                {isProcessing ? 'Cancelling...' : 'Yes, cancel task'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// Helper function to get state-specific colors
function getStateColor(state: Task['state']): string {
  switch (state) {
    case 'Ready':
      return '#28a745' // Green
    case 'In Progress':
      return '#007bff' // Blue
    case 'Blocked':
      return '#dc3545' // Red
    case 'Parked':
      return '#ffc107' // Yellow/Orange
    case 'Completed':
      return '#6c757d' // Gray
    case 'Cancelled':
      return '#6c757d' // Gray
    default:
      return '#6c757d'
  }
}
