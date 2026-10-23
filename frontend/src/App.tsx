import { lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Sidebar } from './components/layout/Sidebar';
import { TopBar } from './components/layout/TopBar';
import { ProtectedRoute } from './components/auth/ProtectedRoute';

// Dynamic code-splitting: load route components on-demand to eliminate main-thread blocking on initial load
const Login = lazy(() => import('./pages/Login').then((m) => ({ default: m.Login })));
const Dashboard = lazy(() => import('./pages/Dashboard').then((m) => ({ default: m.Dashboard })));
const Devices = lazy(() => import('./pages/Devices').then((m) => ({ default: m.Devices })));
const Agents = lazy(() => import('./pages/Agents').then((m) => ({ default: m.Agents })));
const NetworkMonitoring = lazy(() => import('./pages/NetworkMonitoring').then((m) => ({ default: m.NetworkMonitoring })));
const Vulnerabilities = lazy(() => import('./pages/Vulnerabilities').then((m) => ({ default: m.Vulnerabilities })));
const Logs = lazy(() => import('./pages/Logs').then((m) => ({ default: m.Logs })));
const ThreatDetection = lazy(() => import('./pages/ThreatDetection').then((m) => ({ default: m.ThreatDetection })));
const Alerts = lazy(() => import('./pages/Alerts').then((m) => ({ default: m.Alerts })));
const RiskManagement = lazy(() => import('./pages/RiskManagement').then((m) => ({ default: m.RiskManagement })));
const ThreatIntelligence = lazy(() => import('./pages/ThreatIntelligence').then((m) => ({ default: m.ThreatIntelligence })));
const Reports = lazy(() => import('./pages/Reports').then((m) => ({ default: m.Reports })));
const Settings = lazy(() => import('./pages/Settings').then((m) => ({ default: m.Settings })));
const AIAssistant = lazy(() => import('./pages/AIAssistant').then((m) => ({ default: m.AIAssistant })));

const PageLoader = () => (
  <div className="flex items-center justify-center min-h-[300px]">
    <div className="w-7 h-7 border-2 border-cyan-500/20 border-t-cyan-500 rounded-full animate-spin" />
  </div>
);

function App() {
  return (
    <Suspense fallback={<PageLoader />}>
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
                    <Suspense fallback={<PageLoader />}>
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
                        <Route path="/ai-assistant" element={<AIAssistant />} />
                        <Route path="/reports" element={<Reports />} />
                        <Route path="/settings" element={<Settings />} />
                        <Route path="*" element={<Navigate to="/" replace />} />
                      </Routes>
                    </Suspense>
                  </main>
                </div>
              </div>
            </ProtectedRoute>
          }
        />
      </Routes>
    </Suspense>
  );
}

export default App;
