import { useState, useEffect } from 'react'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

interface HealthResponse {
  status: string
}

interface HealthDbResponse {
  status: string
  database?: string
  message?: string
  test_row?: {
    id: number
    timestamp: string
  }
}

function App() {
  const [healthStatus, setHealthStatus] = useState<string>('Loading...')
  const [dbStatus, setDbStatus] = useState<string>('Loading...')
  const [dbDetails, setDbDetails] = useState<string>('')

  useEffect(() => {
    // Call backend health endpoints
    const checkHealth = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/v1/health`)
        const data: HealthResponse = await response.json()
        setHealthStatus(data.status)
      } catch (error) {
        setHealthStatus(`Error: ${error}`)
      }
    }

    const checkDbHealth = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/v1/health/db`)
        const data: HealthDbResponse = await response.json()
        setDbStatus(data.status)
        setDbDetails(JSON.stringify(data, null, 2))
      } catch (error) {
        setDbStatus(`Error: ${error}`)
      }
    }

    checkHealth()
    checkDbHealth()
  }, [])

  return (
    <div style={{ padding: '20px', fontFamily: 'monospace' }}>
      <h1>CyberShield AI - Deployment Smoke Test</h1>
      
      <div style={{ marginBottom: '20px' }}>
        <h2>Backend Health Check</h2>
        <p>Status: {healthStatus}</p>
      </div>

      <div>
        <h2>Database Health Check</h2>
        <p>Status: {dbStatus}</p>
        <pre style={{ background: '#f0f0f0', padding: '10px' }}>
          {dbDetails}
        </pre>
      </div>
    </div>
  )
}

export default App
