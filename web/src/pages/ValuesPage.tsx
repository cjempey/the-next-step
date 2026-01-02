import React, { useState, useEffect } from 'react'
import { valueApi } from '../api/client'
import type { Value, ValueCreate } from '../types/value'

export default function ValuesPage() {
  const [activeValues, setActiveValues] = useState<Value[]>([])
  const [archivedValues, setArchivedValues] = useState<Value[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [newValueStatement, setNewValueStatement] = useState('')
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editStatement, setEditStatement] = useState('')
  const [archiveConfirmId, setArchiveConfirmId] = useState<number | null>(null)

  useEffect(() => {
    loadValues()
  }, [])

  const loadValues = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // Fetch all values (active and archived)
      const response = await valueApi.list(true)
      const allValues = response.data
      
      // Separate active and archived
      setActiveValues(allValues.filter(v => !v.archived))
      setArchivedValues(allValues.filter(v => v.archived))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load values')
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const trimmed = newValueStatement.trim()
    
    if (!trimmed) {
      setError('Value statement cannot be empty')
      return
    }
    
    if (trimmed.length > 255) {
      setError('Value statement must be 255 characters or less')
      return
    }

    try {
      setError(null)
      const payload: ValueCreate = { statement: trimmed }
      await valueApi.create(payload)
      setNewValueStatement('')
      await loadValues()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create value')
    }
  }

  const handleStartEdit = (value: Value) => {
    setEditingId(value.id)
    setEditStatement(value.statement)
  }

  const handleCancelEdit = () => {
    setEditingId(null)
    setEditStatement('')
  }

  const handleSaveEdit = async (id: number) => {
    const trimmed = editStatement.trim()
    
    if (!trimmed) {
      setError('Value statement cannot be empty')
      return
    }
    
    if (trimmed.length > 255) {
      setError('Value statement must be 255 characters or less')
      return
    }

    try {
      setError(null)
      await valueApi.update(id, { statement: trimmed })
      setEditingId(null)
      setEditStatement('')
      await loadValues()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update value')
    }
  }

  const handleArchive = async (id: number) => {
    try {
      setError(null)
      await valueApi.archive(id)
      setArchiveConfirmId(null)
      await loadValues()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to archive value')
    }
  }

  if (loading) {
    return <div style={{ padding: '2rem' }}>Loading values...</div>
  }

  return (
    <div style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
      <h1>My Values</h1>
      <p style={{ color: '#666', marginBottom: '2rem' }}>
        What matters most to you? Define and prioritize your personal values.
      </p>

      {error && (
        <div style={{ 
          padding: '1rem', 
          marginBottom: '1rem', 
          backgroundColor: '#fee', 
          border: '1px solid #fcc',
          borderRadius: '4px',
          color: '#c00'
        }}>
          {error}
        </div>
      )}

      {/* Create New Value */}
      <form onSubmit={handleCreate} style={{ marginBottom: '2rem' }}>
        <h2>Add New Value</h2>
        <input
          type="text"
          value={newValueStatement}
          onChange={(e) => setNewValueStatement(e.target.value)}
          placeholder="e.g., I prioritize my health and wellbeing"
          maxLength={255}
          style={{
            width: '100%',
            padding: '0.75rem',
            fontSize: '1rem',
            border: '1px solid #ccc',
            borderRadius: '4px',
            marginBottom: '0.5rem'
          }}
        />
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <small style={{ color: '#666' }}>
            {newValueStatement.length}/255 characters
          </small>
          <button
            type="submit"
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: '#0066cc',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '1rem'
            }}
          >
            Add Value
          </button>
        </div>
      </form>

      {/* Active Values */}
      <section style={{ marginBottom: '3rem' }}>
        <h2>Active Values</h2>
        {activeValues.length === 0 ? (
          <p style={{ color: '#666', fontStyle: 'italic' }}>
            No active values yet. Add one above to get started.
          </p>
        ) : (
          <ul style={{ listStyle: 'none', padding: 0 }}>
            {activeValues.map((value) => (
              <li
                key={value.id}
                style={{
                  padding: '1rem',
                  marginBottom: '0.5rem',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  backgroundColor: '#fff'
                }}
              >
                {editingId === value.id ? (
                  // Edit mode
                  <div>
                    <input
                      type="text"
                      value={editStatement}
                      onChange={(e) => setEditStatement(e.target.value)}
                      maxLength={255}
                      style={{
                        width: '100%',
                        padding: '0.5rem',
                        fontSize: '1rem',
                        border: '1px solid #ccc',
                        borderRadius: '4px',
                        marginBottom: '0.5rem'
                      }}
                    />
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <button
                        onClick={() => handleSaveEdit(value.id)}
                        style={{
                          padding: '0.5rem 1rem',
                          backgroundColor: '#0066cc',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: 'pointer'
                        }}
                      >
                        Save
                      </button>
                      <button
                        onClick={handleCancelEdit}
                        style={{
                          padding: '0.5rem 1rem',
                          backgroundColor: '#ccc',
                          color: '#333',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: 'pointer'
                        }}
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  // View mode
                  <div>
                    <div style={{ marginBottom: '0.5rem', fontSize: '1.1rem' }}>
                      {value.statement}
                    </div>
                    <div style={{ display: 'flex', gap: '0.5rem', fontSize: '0.9rem' }}>
                      <button
                        onClick={() => handleStartEdit(value)}
                        style={{
                          padding: '0.25rem 0.75rem',
                          backgroundColor: '#f0f0f0',
                          border: '1px solid #ccc',
                          borderRadius: '4px',
                          cursor: 'pointer'
                        }}
                      >
                        Edit
                      </button>
                      {archiveConfirmId === value.id ? (
                        <>
                          <button
                            onClick={() => handleArchive(value.id)}
                            style={{
                              padding: '0.25rem 0.75rem',
                              backgroundColor: '#c00',
                              color: 'white',
                              border: 'none',
                              borderRadius: '4px',
                              cursor: 'pointer'
                            }}
                          >
                            Confirm Archive
                          </button>
                          <button
                            onClick={() => setArchiveConfirmId(null)}
                            style={{
                              padding: '0.25rem 0.75rem',
                              backgroundColor: '#ccc',
                              color: '#333',
                              border: 'none',
                              borderRadius: '4px',
                              cursor: 'pointer'
                            }}
                          >
                            Cancel
                          </button>
                        </>
                      ) : (
                        <button
                          onClick={() => setArchiveConfirmId(value.id)}
                          style={{
                            padding: '0.25rem 0.75rem',
                            backgroundColor: '#f0f0f0',
                            border: '1px solid #ccc',
                            borderRadius: '4px',
                            cursor: 'pointer'
                          }}
                        >
                          Archive
                        </button>
                      )}
                    </div>
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* Archived Values - Historical Journal */}
      <section>
        <h2>Your Journey</h2>
        <p style={{ color: '#666', fontSize: '0.9rem', marginBottom: '1rem' }}>
          A record of the values that shaped your path.
        </p>
        {archivedValues.length === 0 ? (
          <p style={{ color: '#666', fontStyle: 'italic' }}>
            No archived values yet. As you evolve, archived values will appear here as a record of your journey.
          </p>
        ) : (
          <ul style={{ listStyle: 'none', padding: 0 }}>
            {archivedValues.map((value) => (
              <li
                key={value.id}
                style={{
                  padding: '1rem',
                  marginBottom: '0.5rem',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  backgroundColor: '#f9f9f9',
                  fontStyle: 'italic',
                  color: '#666'
                }}
              >
                From {new Date(value.created_at).toLocaleDateString()} to{' '}
                <span style={{ color: '#999' }}>(archive date not tracked)</span>, you valued{' '}
                <strong style={{ color: '#333', fontStyle: 'normal' }}>
                  &quot;{value.statement}&quot;
                </strong>
                , completing{' '}
                <span style={{ color: '#999' }}>0 (not yet tracked)</span> related tasks during this time.
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}
