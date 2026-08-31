import { Routes, Route } from 'react-router-dom'
import { Sidebar } from './components/layout/Sidebar'
import { TopBar } from './components/layout/TopBar'
import { ProtectedRoute } from './components/auth/ProtectedRoute'
import { Login } from './pages/Login'
import { Dashboard } from './pages/Dashboard'
import { Agents } from './pages/Agents'
import { Devices } from './pages/Devices'
import { Vulnerabilities } from './pages/Vulnerabilities'
import { Alerts } from './pages/Alerts'
import { Logs } from './pages/Logs'
import { ThreatIntelligence } from './pages/ThreatIntelligence'
import { Reports } from './pages/Reports'
import { AIAssistant } from './pages/AIAssistant'
import { Settings } from './pages/Settings'

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <div className="flex flex-col h-screen bg-soc-bg">
              <TopBar />
              <div className="flex flex-1 overflow-hidden">
                <Sidebar />
                <main className="flex-1 overflow-y-auto">
                  <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/agents" element={<Agents />} />
                    <Route path="/devices" element={<Devices />} />
                    <Route path="/vulnerabilities" element={<Vulnerabilities />} />
                    <Route path="/alerts" element={<Alerts />} />
                    <Route path="/logs" element={<Logs />} />
                    <Route path="/threat-intelligence" element={<ThreatIntelligence />} />
                    <Route path="/reports" element={<Reports />} />
                    <Route path="/ai-assistant" element={<AIAssistant />} />
                    <Route path="/settings" element={<Settings />} />
                  </Routes>
                </main>
              </div>
            </div>
          </ProtectedRoute>
        }
      />
    </Routes>
  )
}

export default App
