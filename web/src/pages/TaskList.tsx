import { useState, useEffect } from 'react'
import { taskApi } from '../api/client'
import { TaskCard } from '../components/TaskCard'
import type { Task } from '../types/task'
import { getErrorMessage } from '../utils/errors'

export default function TaskList() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [notification, setNotification] = useState<string | null>(null)

  useEffect(() => {
    loadTasks()
  }, [])

  const loadTasks = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await taskApi.list()
      setTasks(response.data)
    } catch (err: unknown) {
      setError(getErrorMessage(err))
      console.error('Error loading tasks:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleTaskUpdate = (updatedTask: Task) => {
    setTasks(prevTasks =>
      prevTasks.map(task => task.id === updatedTask.id ? updatedTask : task)
    )
  }

  const handleNextInstanceCreated = (newTask: Task) => {
    setTasks(prevTasks => [newTask, ...prevTasks])
    // Show a brief inline notification
    setNotification(`Next instance of recurring task created: ${newTask.title}`)
    // Auto-dismiss after 5 seconds
    setTimeout(() => setNotification(null), 5000)
  }

  if (loading) {
    return (
      <div style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
        <h1>Task List</h1>
        <p>Loading tasks...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
        <h1>Task List</h1>
        <div style={{
          padding: '1rem',
          backgroundColor: '#fee',
          border: '1px solid #fcc',
          borderRadius: '4px',
          color: '#c33',
        }}>
          {error}
        </div>
        <button
          onClick={loadTasks}
          style={{
            marginTop: '1rem',
            padding: '0.5rem 1rem',
            border: '1px solid #007bff',
            borderRadius: '4px',
            backgroundColor: '#007bff',
            color: '#fff',
            cursor: 'pointer',
          }}
        >
          Retry
        </button>
      </div>
    )
  }

  return (
    <div style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
      <h1>Task List</h1>
      <p style={{ color: '#666', marginBottom: '2rem' }}>
        View and manage your daily tasks aligned with your values.
      </p>
      
      {notification && (
        <div style={{
          padding: '1rem',
          marginBottom: '1rem',
          backgroundColor: '#d4edda',
          border: '1px solid #c3e6cb',
          borderRadius: '4px',
          color: '#155724',
        }}>
          {notification}
        </div>
      )}
      
      {tasks.length === 0 ? (
        <p style={{ color: '#999', fontStyle: 'italic' }}>
          No tasks yet. Create your first task to get started.
        </p>
      ) : (
        <div>
          {tasks.map(task => (
            <TaskCard
              key={task.id}
              task={task}
              onTaskUpdate={handleTaskUpdate}
              onNextInstanceCreated={handleNextInstanceCreated}
            />
          ))}
        </div>
      )}
    </div>
  )
}
