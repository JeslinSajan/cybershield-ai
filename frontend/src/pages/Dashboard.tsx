import { useState, useEffect, useCallback } from 'react';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { EmptyState } from '../components/ui/EmptyState';
import { agentsService, Agent } from '../services/agentsService';
import { devicesService, Device } from '../services/devicesService';
import { vulnerabilitiesService, Vulnerability } from '../services/vulnerabilitiesService';
import { scansService, Scan } from '../services/scansService';
import { logsService, LogEntry } from '../services/logsService';
import { Link } from 'react-router-dom';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell, PieChart, Pie } from 'recharts';

export function Dashboard() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [devices, setDevices] = useState<Device[]>([]);
  const [vulns, setVulns] = useState<Vulnerability[]>([]);
  const [scans, setScans] = useState<Scan[]>([]);
  const [recentLogs, setRecentLogs] = useState<LogEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefreshed, setLastRefreshed] = useState<Date>(new Date());

  const fetchDashboardData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [agentsData, devicesData, vulnsData, scansData, logsData] = await Promise.all([
        agentsService.listAgents().catch(() => []),
        devicesService.listDevices().catch(() => []),
        vulnerabilitiesService.listVulnerabilities({ limit: 100 }).catch(() => []),
        scansService.listScans().catch(() => []),
        logsService.listLogs({ limit: 10 }).catch(() => []),
      ]);

      setAgents(agentsData);
      setDevices(devicesData);
      setVulns(vulnsData);
      setScans(scansData);
      setRecentLogs(logsData);
      setLastRefreshed(new Date());
    } catch (err: any) {
      setError(err?.message || 'Failed to load security monitoring statistics.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
    // Auto-refresh every 60 seconds
    const interval = setInterval(fetchDashboardData, 60000);
    return () => clearInterval(interval);
  }, [fetchDashboardData]);

  // Derived metrics from real backend data
  const onlineAgents = agents.filter((a) => a.status === 'ONLINE').length;
  const totalAgents = agents.length;
  const onlineDevices = devices.filter((d) => d.status === 'online').length;
  const totalDevices = devices.length;

  const criticalVulns = vulns.filter((v) => v.severity.toLowerCase() === 'critical').length;
  const highVulns = vulns.filter((v) => v.severity.toLowerCase() === 'high').length;
  const mediumVulns = vulns.filter((v) => v.severity.toLowerCase() === 'medium').length;
  const lowVulns = vulns.filter((v) => v.severity.toLowerCase() === 'low').length;

  const vulnChartData = [
    { name: 'Critical', count: criticalVulns, color: '#dc2626' },
    { name: 'High', count: highVulns, color: '#ea580c' },
    { name: 'Medium', count: mediumVulns, color: '#f59e0b' },
    { name: 'Low', count: lowVulns, color: '#10b981' },
  ];

  const agentChartData = [
    { name: 'Online', value: onlineAgents, color: '#10b981' },
    { name: 'Offline', value: agents.filter((a) => a.status === 'OFFLINE').length, color: '#64748b' },
    { name: 'Pending', value: agents.filter((a) => a.status === 'PENDING').length, color: '#f59e0b' },
  ].filter((item) => item.value > 0);

  return (
    <div className="p-6 space-y-6">
      {/* Top Header & Refresh */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h2 className="text-xl font-bold text-slate-100 tracking-tight">Security Overview</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time platform telemetry across monitored endpoints, networks, and vulnerability scans.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-[11px] text-slate-500 font-mono">
            Updated: {lastRefreshed.toLocaleTimeString()}
          </span>
          <Button
            variant="secondary"
            size="sm"
            onClick={fetchDashboardData}
            isLoading={isLoading}
            icon={
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            }
          >
            Refresh
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-rose-950/60 border border-rose-800 rounded-lg text-xs text-rose-300">
          {error}
        </div>
      )}

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Monitored Agents */}
        <Card className="relative overflow-hidden">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Monitored Agents
              </p>
              <div className="flex items-baseline gap-2 mt-2">
                <span className="text-3xl font-extrabold text-white">{onlineAgents}</span>
                <span className="text-xs text-slate-400">/ {totalAgents} active</span>
              </div>
              <p className="text-[11px] text-emerald-400 mt-2 font-medium">
                {totalAgents === 0 ? 'No agents enrolled' : `${Math.round((onlineAgents / (totalAgents || 1)) * 100)}% heartbeat reachability`}
              </p>
            </div>
            <div className="p-2.5 bg-emerald-950/60 border border-emerald-800/40 rounded-lg text-emerald-400">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
              </svg>
            </div>
          </div>
        </Card>

        {/* Discovered Devices */}
        <Card className="relative overflow-hidden">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Discovered Devices
              </p>
              <div className="flex items-baseline gap-2 mt-2">
                <span className="text-3xl font-extrabold text-white">{onlineDevices}</span>
                <span className="text-xs text-slate-400">/ {totalDevices} total</span>
              </div>
              <p className="text-[11px] text-cyan-400 mt-2 font-medium">
                {totalDevices === 0 ? 'No network devices found' : 'Discovered via Nmap scans'}
              </p>
            </div>
            <div className="p-2.5 bg-cyan-950/60 border border-cyan-800/40 rounded-lg text-cyan-400">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
          </div>
        </Card>

        {/* Critical Vulnerabilities */}
        <Card className="relative overflow-hidden">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Critical Vulnerabilities
              </p>
              <div className="flex items-baseline gap-2 mt-2">
                <span className="text-3xl font-extrabold text-rose-400">{criticalVulns}</span>
                <span className="text-xs text-slate-400">({highVulns} High)</span>
              </div>
              <p className="text-[11px] text-slate-400 mt-2 font-medium">
                {vulns.length} total across {devices.length} devices
              </p>
            </div>
            <div className="p-2.5 bg-rose-950/60 border border-rose-800/40 rounded-lg text-rose-400">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
          </div>
        </Card>

        {/* Active Scans */}
        <Card className="relative overflow-hidden">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Scan Pipeline
              </p>
              <div className="flex items-baseline gap-2 mt-2">
                <span className="text-3xl font-extrabold text-white">
                  {scans.filter((s) => s.status === 'RUNNING' || s.status === 'PENDING').length}
                </span>
                <span className="text-xs text-slate-400">in progress</span>
              </div>
              <p className="text-[11px] text-amber-400 mt-2 font-medium">
                {scans.filter((s) => s.status === 'COMPLETED').length} scans completed
              </p>
            </div>
            <div className="p-2.5 bg-amber-950/60 border border-amber-800/40 rounded-lg text-amber-400">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
              </svg>
            </div>
          </div>
        </Card>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Vulnerability Severity Distribution */}
        <Card
          title="Vulnerability Distribution by Severity"
          description="Live tally from Nmap service banners matched against the CVE database"
        >
          {vulns.length === 0 ? (
            <div className="h-56 flex items-center justify-center text-slate-500 text-xs">
              No vulnerabilities identified. Run a vulnerability scan on discovered devices.
            </div>
          ) : (
            <div className="h-56 w-full pt-2">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={vulnChartData} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <XAxis type="number" stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                  <YAxis type="category" dataKey="name" stroke="#64748b" tick={{ fill: '#cbd5e1', fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                  />
                  <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                    {vulnChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </Card>

        {/* Agent Connection Telemetry */}
        <Card
          title="Agent Fleet Health Breakdown"
          description="Current status of deployed Python monitoring agents"
        >
          {agents.length === 0 ? (
            <div className="h-56 flex items-center justify-center text-slate-500 text-xs">
              No agents registered. Generate an enrollment token in the Agents page to connect a machine.
            </div>
          ) : (
            <div className="h-56 w-full flex items-center justify-center">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={agentChartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={75}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {agentChartData.map((entry, index) => (
                      <Cell key={`agent-cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </Card>
      </div>

      {/* Recent Security Activity & Logs */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Live Logs Stream */}
        <div className="lg:col-span-2">
          <Card
            title="Recent Security Event Logs"
            description="Latest authentication and telemetry events ingested from monitoring agents"
            action={
              <Link to="/logs" className="text-xs font-semibold text-cyan-400 hover:text-cyan-300">
                View All Logs &rarr;
              </Link>
            }
          >
            {isLoading && recentLogs.length === 0 ? (
              <LoadingSpinner size="sm" message="Loading security events..." />
            ) : recentLogs.length === 0 ? (
              <EmptyState
                title="No log events ingested yet"
                description="Agents automatically upload host authentication logs periodically via /api/v1/agents/logs."
              />
            ) : (
              <div className="divide-y divide-slate-800/60 overflow-hidden">
                {recentLogs.map((log) => (
                  <div key={log.id} className="py-2.5 flex items-center justify-between text-xs gap-3">
                    <div className="flex items-center gap-2.5 min-w-0">
                      <Badge severity={log.severity}>{log.severity.toUpperCase()}</Badge>
                      <span className="font-mono text-slate-300 truncate">
                        {log.event_type}
                      </span>
                      {log.username && (
                        <span className="text-slate-400 truncate">user: {log.username}</span>
                      )}
                      {log.source_ip && (
                        <span className="text-slate-500 font-mono text-[11px] truncate">
                          ({log.source_ip})
                        </span>
                      )}
                    </div>
                    <span className="text-[11px] text-slate-500 font-mono whitespace-nowrap">
                      {log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : ''}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>

        {/* Recent Scans Pipeline */}
        <div>
          <Card
            title="Recent Scans"
            description="Network & vulnerability scan jobs"
            action={
              <Link to="/devices" className="text-xs font-semibold text-cyan-400 hover:text-cyan-300">
                Manage Devices &rarr;
              </Link>
            }
          >
            {scans.length === 0 ? (
              <div className="py-8 text-center text-slate-500 text-xs">
                No scans dispatched. Launch a discovery scan on the Devices page.
              </div>
            ) : (
              <div className="space-y-3">
                {scans.slice(0, 5).map((scan) => (
                  <div
                    key={scan.id}
                    className="p-3 bg-slate-950/60 border border-slate-800 rounded-lg text-xs space-y-1.5"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-slate-200 capitalize">
                        {scan.scan_type.replace('_', ' ')} Scan
                      </span>
                      <Badge variant={scan.status}>{scan.status}</Badge>
                    </div>
                    <p className="text-slate-400 font-mono text-[11px] truncate">
                      Target: {scan.target_scope}
                    </p>
                    <p className="text-[10px] text-slate-500">
                      Created: {scan.created_at ? new Date(scan.created_at).toLocaleString() : 'N/A'}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
