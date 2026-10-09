import { useState, useEffect, useCallback } from 'react';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Table } from '../components/ui/Table';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { EmptyState } from '../components/ui/EmptyState';
import { agentsService, Agent, AgentNetworkStat } from '../services/agentsService';
import { devicesService, Device } from '../services/devicesService';
import { scansService, Scan } from '../services/scansService';

export function NetworkMonitoring() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [devices, setDevices] = useState<Device[]>([]);
  const [scans, setScans] = useState<Scan[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useState<string>('');
  const [agentStats, setAgentStats] = useState<AgentNetworkStat[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isLoadingStats, setIsLoadingStats] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchOverview = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [agentsData, devicesData, scansData] = await Promise.all([
        agentsService.listAgents().catch(() => []),
        devicesService.listDevices().catch(() => []),
        scansService.listScans().catch(() => []),
      ]);

      setAgents(agentsData);
      setDevices(devicesData);
      setScans(scansData);

      if (agentsData.length > 0 && !selectedAgentId) {
        setSelectedAgentId(agentsData[0].id);
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to load network monitoring telemetry.');
    } finally {
      setIsLoading(false);
    }
  }, [selectedAgentId]);

  useEffect(() => {
    fetchOverview();
  }, [fetchOverview]);

  useEffect(() => {
    if (!selectedAgentId) return;

    let isMounted = true;
    const fetchStats = async () => {
      setIsLoadingStats(true);
      try {
        const stats = await agentsService.getNetworkStats(selectedAgentId);
        if (isMounted) setAgentStats(stats);
      } catch {
        if (isMounted) setAgentStats([]);
      } finally {
        if (isMounted) setIsLoadingStats(false);
      }
    };

    fetchStats();
    return () => {
      isMounted = false;
    };
  }, [selectedAgentId]);

  const onlineDevicesCount = devices.filter((d) => d.status === 'online').length;
  const onlineAgentsCount = agents.filter((a) => a.status === 'ONLINE').length;

  const deviceHeaders = ['IP Address', 'MAC Address', 'Hostname', 'Vendor', 'Reachability', 'Last Seen'];
  const deviceRows = devices.map((d) => [
    <span className="font-mono text-cyan-300 font-semibold text-xs">{d.ip_address}</span>,
    <span className="font-mono text-slate-400 text-xs">{d.mac_address || 'Unresolved'}</span>,
    <span className="text-slate-200 text-xs">{d.hostname || 'Generic Device'}</span>,
    <span className="text-slate-300 text-xs">{d.vendor || 'Unknown'}</span>,
    <Badge severity={d.status === 'online' ? 'success' : 'offline'}>{d.status.toUpperCase()}</Badge>,
    <span className="text-slate-400 text-xs font-mono">
      {d.last_seen_at ? new Date(d.last_seen_at).toLocaleTimeString() : 'N/A'}
    </span>,
  ]);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h2 className="text-xl font-bold text-slate-100 tracking-tight">Network Monitoring & Telemetry</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Monitored subnet topology, interface reachability, and agent system utilization.
          </p>
        </div>
        <Button variant="secondary" size="sm" onClick={fetchOverview} isLoading={isLoading}>
          Refresh
        </Button>
      </div>

      {error && (
        <div className="p-3 bg-rose-950/60 border border-rose-800 rounded-lg text-xs text-rose-300">
          {error}
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Discovered IPs</p>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="text-3xl font-extrabold text-white">{devices.length}</span>
            <span className="text-xs text-emerald-400">{onlineDevicesCount} reachable</span>
          </div>
        </Card>

        <Card>
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Active Agent Probes</p>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="text-3xl font-extrabold text-white">{onlineAgentsCount}</span>
            <span className="text-xs text-slate-400">/ {agents.length} nodes</span>
          </div>
        </Card>

        <Card>
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Subnet Reachability</p>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="text-3xl font-extrabold text-cyan-400">
              {devices.length > 0 ? `${Math.round((onlineDevicesCount / devices.length) * 100)}%` : '0%'}
            </span>
            <span className="text-xs text-slate-400">live ping rate</span>
          </div>
        </Card>

        <Card>
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Network Scans Logged</p>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="text-3xl font-extrabold text-white">{scans.length}</span>
            <span className="text-xs text-slate-400">total executed</span>
          </div>
        </Card>
      </div>

      {/* Agent Telemetry Deep Dive */}
      <Card
        title="Agent Node Resource & Network Telemetry"
        description="Inspect CPU, memory, and storage telemetry transmitted by endpoint monitoring agents"
        action={
          agents.length > 0 ? (
            <select
              value={selectedAgentId}
              onChange={(e) => setSelectedAgentId(e.target.value)}
              className="bg-slate-950 border border-slate-700 text-xs rounded-lg px-3 py-1.5 text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
            >
              {agents.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name} ({a.hostname}) - {a.status}
                </option>
              ))}
            </select>
          ) : undefined
        }
      >
        {isLoadingStats ? (
          <LoadingSpinner size="sm" message="Loading agent node metrics..." />
        ) : agentStats.length === 0 ? (
          <div className="p-6 text-center text-xs text-slate-500">
            {agents.length === 0
              ? 'No agents available. Enroll an agent to view system telemetry.'
              : 'No telemetry frames recorded for this agent yet.'}
          </div>
        ) : (
          <div className="space-y-4">
            {/* Latest reading */}
            {agentStats[0] && (
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 p-3 bg-slate-950/60 border border-slate-800 rounded-lg text-xs">
                <div>
                  <span className="text-slate-500 text-[10px] uppercase font-semibold">Latest CPU Usage</span>
                  <p className="text-lg font-bold text-cyan-300 font-mono mt-0.5">
                    {agentStats[0].cpu_percent !== null ? `${agentStats[0].cpu_percent}%` : 'N/A'}
                  </p>
                </div>
                <div>
                  <span className="text-slate-500 text-[10px] uppercase font-semibold">Latest RAM Allocation</span>
                  <p className="text-lg font-bold text-cyan-300 font-mono mt-0.5">
                    {agentStats[0].memory_percent !== null ? `${agentStats[0].memory_percent}%` : 'N/A'}
                  </p>
                </div>
                <div>
                  <span className="text-slate-500 text-[10px] uppercase font-semibold">Telemetry Timestamp</span>
                  <p className="text-xs text-slate-300 font-mono mt-1">
                    {new Date(agentStats[0].timestamp).toLocaleString()}
                  </p>
                </div>
              </div>
            )}

            {/* History Table */}
            <div className="overflow-x-auto rounded-lg border border-slate-800">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950 border-b border-slate-800 text-slate-400 uppercase text-[10px]">
                  <tr>
                    <th className="py-2.5 px-3">Telemetry Time</th>
                    <th className="py-2.5 px-3">CPU Usage</th>
                    <th className="py-2.5 px-3">Memory Usage</th>
                    <th className="py-2.5 px-3">Disk Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 bg-slate-900/40 font-mono">
                  {agentStats.slice(0, 5).map((stat) => (
                    <tr key={stat.id}>
                      <td className="py-2 px-3 text-slate-300">
                        {new Date(stat.timestamp).toLocaleTimeString()}
                      </td>
                      <td className="py-2 px-3 text-cyan-300">
                        {stat.cpu_percent !== null ? `${stat.cpu_percent}%` : 'N/A'}
                      </td>
                      <td className="py-2 px-3 text-amber-300">
                        {stat.memory_percent !== null ? `${stat.memory_percent}%` : 'N/A'}
                      </td>
                      <td className="py-2 px-3 text-slate-400 text-[11px]">
                        {stat.details && typeof stat.details === 'object'
                          ? JSON.stringify(stat.details)
                          : 'Normal'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </Card>

      {/* Network Interface & IP Reachability Table */}
      <Card
        title="Discovered Network Interfaces & Subnet Endpoints"
        description="Comprehensive list of reachable network devices"
      >
        {devices.length === 0 ? (
          <EmptyState
            title="No network endpoints discovered"
            description="Run a discovery scan on the Devices page to discover devices on your local subnet."
          />
        ) : (
          <Table headers={deviceHeaders} rows={deviceRows} />
        )}
      </Card>
    </div>
  );
}
