import ValuesPage from './pages/ValuesPage'

function App() {
  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f5f5f5' }}>
      <nav style={{ 
        padding: '1rem 2rem', 
        backgroundColor: 'white', 
        borderBottom: '1px solid #ddd',
        marginBottom: '0'
      }}>
        <h1 style={{ margin: 0, fontSize: '1.5rem' }}>The Next Step</h1>
      </nav>
      <ValuesPage />
    </div>
  )
}

export default App
