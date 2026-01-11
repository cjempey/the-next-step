import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import TaskList from './pages/TaskList'
import TaskEntry from './pages/TaskEntry'
import ValuesPage from './pages/ValuesPage'
import MorningPlanning from './pages/MorningPlanning'
import EveningReview from './pages/EveningReview'
import WhatNext from './pages/WhatNext'

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Navigate to="/tasks" replace />} />
          <Route path="/tasks" element={<TaskList />} />
          <Route path="/tasks/new" element={<TaskEntry />} />
          <Route path="/values" element={<ValuesPage />} />
          <Route path="/morning-planning" element={<MorningPlanning />} />
          <Route path="/evening-review" element={<EveningReview />} />
          <Route path="/what-next" element={<WhatNext />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}

export default App
