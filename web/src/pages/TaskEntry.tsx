import { useState, useEffect, FormEvent, ReactNode } from 'react'
import axios from 'axios'
import {
  DndContext,
  DragEndEvent,
  DragOverlay,
  DragStartEvent,
  closestCenter,
  PointerSensor,
  useSensor,
  useSensors,
  useDraggable,
  useDroppable,
} from '@dnd-kit/core'
import { taskApi, valueApi } from '../api/client'
import { useStore } from '../store/useStore'
import type { Value } from '../types/value'
import type { Task, TaskCreate } from '../types/task'

export default function TaskEntry() {
  // Form state
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [impact, setImpact] = useState<'A' | 'B' | 'C' | 'D'>('B')
  const [urgency, setUrgency] = useState<1 | 2 | 3 | 4>(3)
  const [dueDate, setDueDate] = useState('')
  const [recurrence, setRecurrence] = useState<'none' | 'daily' | 'weekly'>('none')

  // Values state
  const [availableValues, setAvailableValues] = useState<Value[]>([])
  const [linkedValueIds, setLinkedValueIds] = useState<number[]>([])
  const [loadingValues, setLoadingValues] = useState(true)

  // Tasks state
  const { tasks, setTasks, addTask } = useStore()
  const [loadingTasks, setLoadingTasks] = useState(true)

  // UI state
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [activeId, setActiveId] = useState<number | null>(null)

  // Drag and drop sensors
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    })
  )

  // Load values on mount
  useEffect(() => {
    const loadValues = async () => {
      try {
        const response = await valueApi.list(false) // Only active values
        setAvailableValues(response.data)
      } catch (err) {
        console.error('Failed to load values:', err)
      } finally {
        setLoadingValues(false)
      }
    }
    loadValues()
  }, [])

  // Load tasks on mount
  useEffect(() => {
    const loadTasks = async () => {
      try {
        const response = await taskApi.list()
        setTasks(response.data)
      } catch (err) {
        console.error('Failed to load tasks:', err)
      } finally {
        setLoadingTasks(false)
      }
    }
    loadTasks()
  }, [setTasks])

  const handleDragStart = (event: DragStartEvent) => {
    setActiveId(event.active.id as number)
  }

  const handleDragEnd = (event: DragEndEvent) => {
    setActiveId(null)
    const { active, over } = event

    if (!over) return

    const valueId = active.id as number
    const dropZone = over.id as string

    if (dropZone === 'linked-values') {
      // Add to linked values if not already there
      if (!linkedValueIds.includes(valueId)) {
        setLinkedValueIds([...linkedValueIds, valueId])
      }
    } else if (dropZone === 'available-values') {
      // Remove from linked values
      setLinkedValueIds(linkedValueIds.filter((id) => id !== valueId))
    }
  }

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError(null)
    setSuccessMessage(null)

    // Validate required fields
    if (!title.trim()) {
      setError('Task title is required')
      return
    }

    if (title.trim().length > 255) {
      setError('Task title must be 255 characters or less')
      return
    }

    try {
      const taskData: TaskCreate = {
        title: title.trim(),
        description: description.trim() || null,
        value_ids: linkedValueIds,
        impact,
        urgency,
        due_date: dueDate || null,
        recurrence,
      }

      const response = await taskApi.create(taskData)
      const newTask: Task = response.data

      // Add to store
      addTask(newTask)

      // Clear form
      setTitle('')
      setDescription('')
      setImpact('B')
      setUrgency(3)
      setDueDate('')
      setRecurrence('none')
      setLinkedValueIds([])

      // Show success message
      setSuccessMessage('Task created successfully')
      setTimeout(() => setSuccessMessage(null), 3000)
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.data?.detail) {
        setError(err.response.data.detail)
      } else {
        setError(err instanceof Error ? err.message : 'Failed to create task')
      }
    }
  }

  const getValueById = (id: number): Value | undefined => {
    return availableValues.find((v) => v.id === id)
  }

  const unlinkedValues = availableValues.filter((v) => !linkedValueIds.includes(v.id))
  const linkedValues = linkedValueIds.map((id) => getValueById(id)).filter(Boolean) as Value[]

  // Sort tasks by impact+urgency lexicographically
  const sortedTasks = [...tasks].sort((a, b) => {
    const aKey = `${a.impact}${a.urgency}`
    const bKey = `${b.impact}${b.urgency}`
    return aKey.localeCompare(bKey)
  })

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - 80px)', gap: '2rem', padding: '2rem' }}>
      {/* Left Column: Task Entry Form */}
      <div style={{ flex: '1', maxWidth: '600px', overflowY: 'auto' }}>
        <h1>New Task</h1>

        {error && (
          <div
            style={{
              padding: '1rem',
              marginBottom: '1rem',
              backgroundColor: '#fee',
              border: '1px solid #fcc',
              borderRadius: '4px',
              color: '#c33',
            }}
          >
            {error}
          </div>
        )}

        {successMessage && (
          <div
            style={{
              padding: '1rem',
              marginBottom: '1rem',
              backgroundColor: '#efe',
              border: '1px solid #cfc',
              borderRadius: '4px',
              color: '#3c3',
            }}
          >
            {successMessage}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {/* Task Title */}
          <div style={{ marginBottom: '1.5rem' }}>
            <label htmlFor="title" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
              Task Title *
            </label>
            <input
              type="text"
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g., Water the plants"
              maxLength={255}
              style={{
                width: '100%',
                padding: '0.75rem',
                border: '1px solid #ccc',
                borderRadius: '4px',
                fontSize: '1rem',
              }}
            />
          </div>

          {/* Values */}
          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
              Values (optional)
            </label>
            {loadingValues ? (
              <p style={{ color: '#666', fontStyle: 'italic' }}>Loading values...</p>
            ) : availableValues.length === 0 ? (
              <p style={{ color: '#666', fontStyle: 'italic' }}>
                No values defined yet. Visit Values page to create some.
              </p>
            ) : (
              <DndContext
                sensors={sensors}
                collisionDetection={closestCenter}
                onDragStart={handleDragStart}
                onDragEnd={handleDragEnd}
              >
                <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem' }}>
                  {/* Available Values */}
                  <DroppableZone id="available-values">
                    <div
                      style={{
                        flex: '1',
                        padding: '1rem',
                        border: '2px dashed #ccc',
                        borderRadius: '4px',
                        minHeight: '100px',
                      }}
                    >
                      <p style={{ fontSize: '0.875rem', color: '#666', marginBottom: '0.5rem' }}>
                        Available Values
                      </p>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                        {unlinkedValues.map((value) => (
                          <DraggableValue key={value.id} value={value} />
                        ))}
                      </div>
                    </div>
                  </DroppableZone>

                  {/* Linked Values */}
                  <DroppableZone id="linked-values">
                    <div
                      style={{
                        flex: '1',
                        padding: '1rem',
                        border: '2px dashed #4CAF50',
                        borderRadius: '4px',
                        minHeight: '100px',
                        backgroundColor: '#f0f8f0',
                      }}
                    >
                      <p style={{ fontSize: '0.875rem', color: '#666', marginBottom: '0.5rem' }}>
                        Linked Values
                      </p>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                        {linkedValues.map((value) => (
                          <DraggableValue key={value.id} value={value} />
                        ))}
                      </div>
                    </div>
                  </DroppableZone>
                </div>

                <DragOverlay>
                  {activeId ? <ValuePillOverlay value={getValueById(activeId)} /> : null}
                </DragOverlay>
              </DndContext>
            )}
          </div>

          {/* Impact */}
          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
              Impact (optional, defaults to B)
            </label>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {(['A', 'B', 'C', 'D'] as const).map((level) => (
                <label key={level} style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                  <input
                    type="radio"
                    name="impact"
                    value={level}
                    checked={impact === level}
                    onChange={(e) => setImpact(e.target.value as 'A' | 'B' | 'C' | 'D')}
                    style={{ marginRight: '0.5rem' }}
                  />
                  <span>
                    <strong>{level}</strong>:{' '}
                    {level === 'A' && 'Directly advance values/goals'}
                    {level === 'B' && 'Moderately aligned with values'}
                    {level === 'C' && 'Minor alignment'}
                    {level === 'D' && 'Little or no impact on values'}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Urgency */}
          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
              Urgency (optional, defaults to 3)
            </label>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {([1, 2, 3, 4] as const).map((level) => (
                <label key={level} style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                  <input
                    type="radio"
                    name="urgency"
                    value={level}
                    checked={urgency === level}
                    onChange={(e) => setUrgency(Number(e.target.value) as 1 | 2 | 3 | 4)}
                    style={{ marginRight: '0.5rem' }}
                  />
                  <span>
                    <strong>{level}</strong>:{' '}
                    {level === 1 && 'Immediate due; high penalty if delayed'}
                    {level === 2 && 'Due soon (next few days)'}
                    {level === 3 && 'Can be deferred (next week)'}
                    {level === 4 && 'Long-term or optional'}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Due Date */}
          <div style={{ marginBottom: '1.5rem' }}>
            <label htmlFor="due_date" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
              Due Date (optional)
            </label>
            <input
              type="date"
              id="due_date"
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
              style={{
                padding: '0.75rem',
                border: '1px solid #ccc',
                borderRadius: '4px',
                fontSize: '1rem',
              }}
            />
          </div>

          {/* Recurrence */}
          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
              Recurrence (optional, defaults to none)
            </label>
            <p style={{ fontSize: '0.875rem', color: '#666', marginBottom: '0.5rem' }}>
              Recurring tasks auto-create next instance on completion
            </p>
            <div style={{ display: 'flex', gap: '1rem' }}>
              {(['none', 'daily', 'weekly'] as const).map((type) => (
                <label key={type} style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                  <input
                    type="radio"
                    name="recurrence"
                    value={type}
                    checked={recurrence === type}
                    onChange={(e) => setRecurrence(e.target.value as 'none' | 'daily' | 'weekly')}
                    style={{ marginRight: '0.5rem' }}
                  />
                  {type.charAt(0).toUpperCase() + type.slice(1)}
                </label>
              ))}
            </div>
          </div>

          {/* Description */}
          <div style={{ marginBottom: '1.5rem' }}>
            <label htmlFor="description" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
              Description/Notes (optional)
            </label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optional details about this task"
              rows={4}
              style={{
                width: '100%',
                padding: '0.75rem',
                border: '1px solid #ccc',
                borderRadius: '4px',
                fontSize: '1rem',
                fontFamily: 'inherit',
              }}
            />
          </div>

          {/* Form Actions */}
          <div style={{ display: 'flex', gap: '1rem' }}>
            <button
              type="submit"
              style={{
                padding: '0.75rem 2rem',
                backgroundColor: '#4CAF50',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                fontSize: '1rem',
                fontWeight: 'bold',
                cursor: 'pointer',
              }}
            >
              Save Task
            </button>
            <button
              type="button"
              onClick={() => window.history.back()}
              style={{
                padding: '0.75rem 2rem',
                backgroundColor: '#999',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                fontSize: '1rem',
                cursor: 'pointer',
              }}
            >
              Cancel
            </button>
          </div>
        </form>
      </div>

      {/* Right Column: Task List Preview */}
      <div
        style={{
          flex: '1',
          maxWidth: '600px',
          borderLeft: '1px solid #ddd',
          paddingLeft: '2rem',
          overflowY: 'auto',
        }}
      >
        <h2>Your Tasks</h2>
        {loadingTasks ? (
          <p style={{ color: '#666', fontStyle: 'italic' }}>Loading tasks...</p>
        ) : sortedTasks.length === 0 ? (
          <p style={{ color: '#666', fontStyle: 'italic' }}>No tasks yet. Create your first task!</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {sortedTasks.map((task) => (
              <div
                key={task.id}
                style={{
                  padding: '1rem',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  backgroundColor: '#f9f9f9',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'start', gap: '0.75rem', marginBottom: '0.5rem' }}>
                  <span
                    style={{
                      display: 'inline-block',
                      padding: '0.25rem 0.5rem',
                      backgroundColor: getImpactColor(task.impact),
                      color: 'white',
                      borderRadius: '4px',
                      fontSize: '0.875rem',
                      fontWeight: 'bold',
                      flexShrink: 0,
                    }}
                  >
                    {task.impact}{task.urgency}
                  </span>
                  <span style={{ fontWeight: 'bold', flex: 1 }}>{task.title}</span>
                </div>
                {task.value_ids.length > 0 && (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.25rem', marginTop: '0.5rem' }}>
                    {task.value_ids.map((valueId) => {
                      const value = getValueById(valueId)
                      return value ? (
                        <span
                          key={valueId}
                          style={{
                            display: 'inline-block',
                            padding: '0.125rem 0.5rem',
                            backgroundColor: '#e3f2fd',
                            color: '#1976d2',
                            borderRadius: '12px',
                            fontSize: '0.75rem',
                          }}
                        >
                          {value.statement}
                        </span>
                      ) : null
                    })}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

// Helper component for draggable values
function DraggableValue({ value }: { value: Value }) {
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
    id: value.id,
  })

  return (
    <div
      ref={setNodeRef}
      {...listeners}
      {...attributes}
      style={{
        padding: '0.5rem 1rem',
        backgroundColor: isDragging ? '#ccc' : '#2196F3',
        color: 'white',
        borderRadius: '20px',
        fontSize: '0.875rem',
        cursor: 'grab',
        opacity: isDragging ? 0.5 : 1,
      }}
    >
      {value.statement}
    </div>
  )
}

function ValuePillOverlay({ value }: { value: Value | undefined }) {
  if (!value) return null

  return (
    <div
      style={{
        padding: '0.5rem 1rem',
        backgroundColor: '#2196F3',
        color: 'white',
        borderRadius: '20px',
        fontSize: '0.875rem',
        boxShadow: '0 4px 8px rgba(0,0,0,0.2)',
      }}
    >
      {value.statement}
    </div>
  )
}

function getImpactColor(impact: string): string {
  switch (impact) {
    case 'A':
      return '#d32f2f' // Red
    case 'B':
      return '#f57c00' // Orange
    case 'C':
      return '#fbc02d' // Yellow
    case 'D':
      return '#7cb342' // Green
    default:
      return '#999'
  }
}

// Droppable zone component
function DroppableZone({ id, children }: { id: string; children: ReactNode }) {
  const { setNodeRef } = useDroppable({ id })
  return <div ref={setNodeRef}>{children}</div>
}
