import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { taskApi, valueApi } from '../api/client'
import { TaskCard } from '../components/TaskCard'
import type { Task } from '../types/task'
import type { Value } from '../types/value'
import { getErrorMessage } from '../utils/errors'

const TASK_STATES: Task['state'][] = ['Ready', 'In Progress', 'Blocked', 'Parked', 'Completed', 'Cancelled']

export default function TaskList() {
  const navigate = useNavigate()
  const [tasks, setTasks] = useState<Task[]>([])
  const [values, setValues] = useState<Value[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [notification, setNotification] = useState<string | null>(null)
  
  // Filter state
  const [selectedStates, setSelectedStates] = useState<Task['state'][]>(['Ready'])
  const [selectedValueIds, setSelectedValueIds] = useState<number[]>([])

  // Load values on mount
  useEffect(() => {
    const loadValues = async () => {
      try {
        const response = await valueApi.list(false)
        setValues(response.data)
      } catch (err) {
        console.error('Error loading values:', err)
        const message = `Failed to load values: ${getErrorMessage(err)}. Value filter may be unavailable.`
        setNotification(message)
      }
    }
    loadValues()
  }, [])

  // Cleanup timeout on unmount to prevent memory leak
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

  const loadTasks = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      
      // If no states are selected, show empty list
      if (selectedStates.length === 0) {
        setTasks([])
        setLoading(false)
        return
      }

      // Fetch tasks for all selected states in parallel to avoid sequential latency
      const requests = selectedStates.map((state) => {
        // Backend only supports filtering by a single state at a time;
        // value-based filtering is handled consistently on the client.
        const params: { state?: Task['state'] } = { state }
        return taskApi.list(params)
      })

      const responses = await Promise.all(requests)
      const allTasks: Task[] = responses.flatMap((response) => response.data)
      
      // If any values are selected, filter client-side
      let filteredTasks = allTasks
      if (selectedValueIds.length > 0) {
        filteredTasks = allTasks.filter(task =>
          task.value_ids.some(valueId => selectedValueIds.includes(valueId))
        )
      }
      
      // Remove duplicates (in case a task matches multiple criteria)
      const uniqueTasks = Array.from(
        new Map(filteredTasks.map(task => [task.id, task])).values()
      )
      
      setTasks(uniqueTasks)
    } catch (err: unknown) {
      setError(getErrorMessage(err))
      console.error('Error loading tasks:', err)
    } finally {
      setLoading(false)
    }
  }, [selectedStates, selectedValueIds])

  // Load tasks when filters change
  useEffect(() => {
    loadTasks()
  }, [loadTasks])

  const handleTaskUpdate = (updatedTask: Task) => {
    setTasks(prevTasks =>
      prevTasks.map(task => task.id === updatedTask.id ? updatedTask : task)
    )
  }

  const handleNextInstanceCreated = (newTask: Task) => {
    setTasks(prevTasks => [newTask, ...prevTasks])
    // Show a brief inline notification
    setNotification(`Next instance of recurring task created: ${newTask.title}`)
    // Timeout cleanup is handled by useEffect
  }

  const toggleStateFilter = (state: Task['state']) => {
    setSelectedStates(prev =>
      prev.includes(state)
        ? prev.filter(s => s !== state)
        : [...prev, state]
    )
  }

  const toggleValueFilter = (valueId: number) => {
    setSelectedValueIds(prev =>
      prev.includes(valueId)
        ? prev.filter(id => id !== valueId)
        : [...prev, valueId]
    )
  }

  const getValueById = (id: number): Value | undefined => {
    return values.find(v => v.id === id)
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
    <div style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h1 style={{ margin: 0 }}>Task List</h1>
        <button
          onClick={() => navigate('/tasks/new')}
          style={{
            padding: '0.75rem 1.5rem',
            backgroundColor: '#4CAF50',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            fontSize: '1rem',
            fontWeight: 'bold',
            cursor: 'pointer',
          }}
        >
          + Create Task
        </button>
      </div>
      
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
      
      {/* Filter Controls */}
      <div style={{
        padding: '1.5rem',
        backgroundColor: '#f9f9f9',
        border: '1px solid #ddd',
        borderRadius: '8px',
        marginBottom: '2rem',
      }}>
        <h2 style={{ fontSize: '1.1rem', marginTop: 0, marginBottom: '1rem' }}>Filters</h2>
        
        {/* State Filter */}
        <div style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ fontSize: '0.95rem', fontWeight: 'bold', marginBottom: '0.75rem' }}>
            Task State
          </h3>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {TASK_STATES.map(state => (
              <label
                key={state}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  padding: '0.5rem 0.75rem',
                  backgroundColor: selectedStates.includes(state) ? '#007bff' : '#fff',
                  color: selectedStates.includes(state) ? '#fff' : '#333',
                  border: '1px solid #007bff',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '0.875rem',
                  transition: 'all 0.2s',
                }}
              >
                <input
                  type="checkbox"
                  checked={selectedStates.includes(state)}
                  onChange={() => toggleStateFilter(state)}
                  style={{ marginRight: '0.5rem' }}
                />
                {state}
              </label>
            ))}
          </div>
        </div>
        
        {/* Value Filter */}
        {values.length > 0 && (
          <div>
            <h3 style={{ fontSize: '0.95rem', fontWeight: 'bold', marginBottom: '0.75rem' }}>
              Filter by Value
            </h3>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
              {values.map(value => (
                <label
                  key={value.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    padding: '0.5rem 0.75rem',
                    backgroundColor: selectedValueIds.includes(value.id) ? '#2196F3' : '#fff',
                    color: selectedValueIds.includes(value.id) ? '#fff' : '#333',
                    border: '1px solid #2196F3',
                    borderRadius: '20px',
                    cursor: 'pointer',
                    fontSize: '0.875rem',
                    transition: 'all 0.2s',
                  }}
                >
                  <input
                    type="checkbox"
                    checked={selectedValueIds.includes(value.id)}
                    onChange={() => toggleValueFilter(value.id)}
                    style={{ marginRight: '0.5rem' }}
                  />
                  {value.statement}
                </label>
              ))}
            </div>
          </div>
        )}
      </div>
      
      {/* Task List */}
      <div>
        <div style={{ marginBottom: '1rem', fontSize: '0.9rem', color: '#666' }}>
          Showing {tasks.length} task{tasks.length !== 1 ? 's' : ''}
        </div>
        
        {tasks.length === 0 ? (
          <div style={{
            padding: '3rem 2rem',
            textAlign: 'center',
            backgroundColor: '#f9f9f9',
            border: '2px dashed #ddd',
            borderRadius: '8px',
          }}>
            <p style={{ fontSize: '1.1rem', color: '#999', marginBottom: '1rem' }}>
              No tasks found with the selected filters.
            </p>
            <button
              onClick={() => navigate('/tasks/new')}
              style={{
                padding: '0.75rem 1.5rem',
                backgroundColor: '#4CAF50',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                fontSize: '1rem',
                fontWeight: 'bold',
                cursor: 'pointer',
              }}
            >
              Create Your First Task
            </button>
          </div>
        ) : (
          <div>
            {tasks.map(task => {
              // Get value objects for this task
              const taskValues = task.value_ids
                .map(id => getValueById(id))
                .filter((v): v is Value => v !== undefined)
              
              return (
                <div key={task.id} style={{ marginBottom: '1rem' }}>
                  <TaskCard
                    task={task}
                    onTaskUpdate={handleTaskUpdate}
                    onNextInstanceCreated={handleNextInstanceCreated}
                  />
                  {/* Display value pills below each task card */}
                  {taskValues.length > 0 && (
                    <div style={{
                      display: 'flex',
                      flexWrap: 'wrap',
                      gap: '0.5rem',
                      marginTop: '0.5rem',
                      paddingLeft: '1rem',
                    }}>
                      {taskValues.map(value => (
                        <span
                          key={value.id}
                          style={{
                            display: 'inline-block',
                            padding: '0.25rem 0.75rem',
                            backgroundColor: '#e3f2fd',
                            color: '#1976d2',
                            borderRadius: '12px',
                            fontSize: '0.8rem',
                          }}
                        >
                          {value.statement}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
