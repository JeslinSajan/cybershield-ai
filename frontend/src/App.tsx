import { Routes, Route, Navigate } from 'react-router-dom';
import { Sidebar } from './components/layout/Sidebar';
import { TopBar } from './components/layout/TopBar';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { Devices } from './pages/Devices';
import { Agents } from './pages/Agents';
import { NetworkMonitoring } from './pages/NetworkMonitoring';
import { Vulnerabilities } from './pages/Vulnerabilities';
import { Logs } from './pages/Logs';
import { ThreatDetection } from './pages/ThreatDetection';
import { Alerts } from './pages/Alerts';
import { RiskManagement } from './pages/RiskManagement';
import { ThreatIntelligence } from './pages/ThreatIntelligence';
import { Reports } from './pages/Reports';
import { Settings } from './pages/Settings';

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <div className="flex flex-col h-screen bg-slate-950 text-slate-100 antialiased overflow-hidden">
              <TopBar />
              <div className="flex flex-1 overflow-hidden">
                <Sidebar />
                <main className="flex-1 overflow-y-auto bg-slate-950">
                  <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/devices" element={<Devices />} />
                    <Route path="/agents" element={<Agents />} />
                    <Route path="/network" element={<NetworkMonitoring />} />
                    <Route path="/vulnerabilities" element={<Vulnerabilities />} />
                    <Route path="/logs" element={<Logs />} />
                    <Route path="/threat-detection" element={<ThreatDetection />} />
                    <Route path="/alerts" element={<Alerts />} />
                    <Route path="/risk-management" element={<RiskManagement />} />
                    <Route path="/threat-intelligence" element={<ThreatIntelligence />} />
                    <Route path="/reports" element={<Reports />} />
                    <Route path="/settings" element={<Settings />} />
                    <Route path="*" element={<Navigate to="/" replace />} />
                  </Routes>
                </main>
              </div>
            </div>
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

export default App;
