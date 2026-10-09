import { useState, useEffect, useCallback } from 'react';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { EmptyState } from '../components/ui/EmptyState';
import { logsService, LogEntry } from '../services/logsService';

interface SuspiciousIpCluster {
  ip: string;
  failureCount: number;
  lastSeen: string;
  targetedUsers: string[];
}

export function ThreatDetection() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDetectionData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const logData = await logsService.listLogs({ limit: 150 });
      setLogs(logData);
    } catch (err: any) {
      setError(err?.message || 'Failed to query threat detection feed.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDetectionData();
  }, [fetchDetectionData]);

  // Correlate suspicious IP clusters from live log records
  const ipFailuresMap = new Map<string, { count: number; lastSeen: string; users: Set<string> }>();
  logs.forEach((log) => {
    if (log.event_type === 'login_failure' && log.source_ip) {
      const current = ipFailuresMap.get(log.source_ip) || {
        count: 0,
        lastSeen: log.timestamp || '',
        users: new Set<string>(),
      };
      current.count += 1;
      if (log.timestamp && (!current.lastSeen || new Date(log.timestamp) > new Date(current.lastSeen))) {
        current.lastSeen = log.timestamp;
      }
      if (log.username) {
        current.users.add(log.username);
      }
      ipFailuresMap.set(log.source_ip, current);
    }
  });

  const suspiciousClusters: SuspiciousIpCluster[] = Array.from(ipFailuresMap.entries())
    .map(([ip, data]) => ({
      ip,
      failureCount: data.count,
      lastSeen: data.lastSeen,
      targetedUsers: Array.from(data.users),
    }))
    .sort((a, b) => b.failureCount - a.failureCount);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h2 className="text-xl font-bold text-slate-100 tracking-tight">Threat Detection Engine</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Phase 15 behavioral correlation engine monitoring authentication anomalies and port exposure patterns.
          </p>
        </div>
        <Button variant="secondary" size="sm" onClick={fetchDetectionData} isLoading={isLoading}>
          Re-evaluate
        </Button>
      </div>

      {error && (
        <div className="p-3 bg-rose-950/60 border border-rose-800 rounded-lg text-xs text-rose-300">
          {error}
        </div>
      )}

      {/* Active Rules Grid */}
      <div>
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
          Deployed Detection Rules (Synchronous Evaluation)
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Rule 1 */}
          <Card className="border-l-4 border-l-rose-500">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono text-cyan-400 uppercase font-semibold">Rule 1: Brute Force</span>
              <Badge severity="Critical">ACTIVE</Badge>
            </div>
            <h4 className="text-sm font-bold text-slate-100 mt-2">Authentication Flood</h4>
            <p className="text-xs text-slate-400 mt-1">
              Triggers when <strong className="text-slate-200">&ge; 5 login_failure</strong> logs occur from the same source IP within a 10-minute sliding window.
            </p>
            <div className="mt-3 pt-3 border-t border-slate-800 flex items-center justify-between text-[11px] text-slate-500 font-mono">
              <span>Risk Score: +40</span>
              <span>1h Deduplication</span>
            </div>
          </Card>

          {/* Rule 2 */}
          <Card className="border-l-4 border-l-orange-500">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono text-cyan-400 uppercase font-semibold">Rule 2: Port Sweep</span>
              <Badge severity="High">ACTIVE</Badge>
            </div>
            <h4 className="text-sm font-bold text-slate-100 mt-2">Excessive Open Ports</h4>
            <p className="text-xs text-slate-400 mt-1">
              Triggers when an agent scan result exposes <strong className="text-slate-200">&ge; 10 open service ports</strong> on an internal endpoint.
            </p>
            <div className="mt-3 pt-3 border-t border-slate-800 flex items-center justify-between text-[11px] text-slate-500 font-mono">
              <span>Risk Score: +30</span>
              <span>Device Scope</span>
            </div>
          </Card>

          {/* Rule 3 */}
          <Card className="border-l-4 border-l-amber-500">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono text-cyan-400 uppercase font-semibold">Rule 3: Login Anomaly</span>
              <Badge severity="Medium">ACTIVE</Badge>
            </div>
            <h4 className="text-sm font-bold text-slate-100 mt-2">Suspicious Successful Login</h4>
            <p className="text-xs text-slate-400 mt-1">
              Triggers when a <strong className="text-slate-200">login_success</strong> originates from an IP address with 3+ prior failures in the last 60 minutes.
            </p>
            <div className="mt-3 pt-3 border-t border-slate-800 flex items-center justify-between text-[11px] text-slate-500 font-mono">
              <span>Risk Score: +35</span>
              <span>Compromise Guard</span>
            </div>
          </Card>
        </div>
      </div>

      {/* Correlation Results from Live Log Stream */}
      <Card
        title="Live Suspicious Activity Correlated from Host Logs"
        description="Source IP addresses exhibiting repeated failed authentications"
      >
        {isLoading && suspiciousClusters.length === 0 ? (
          <LoadingSpinner size="md" message="Running correlation queries..." />
        ) : suspiciousClusters.length === 0 ? (
          <EmptyState
            title="No anomalous clusters detected"
            description="All ingested log events are within baseline failure thresholds. The detection engine is actively listening for anomalous spikes."
          />
        ) : (
          <div className="divide-y divide-slate-800/60 overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950 text-slate-400 text-[10px] uppercase font-semibold">
                <tr>
                  <th className="py-2.5 px-3">Suspicious Source IP</th>
                  <th className="py-2.5 px-3">Failed Attempts</th>
                  <th className="py-2.5 px-3">Targeted Usernames</th>
                  <th className="py-2.5 px-3">Rule 1 Threshold</th>
                  <th className="py-2.5 px-3">Last Activity</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {suspiciousClusters.map((cluster) => {
                  const isThresholdExceeded = cluster.failureCount >= 5;
                  return (
                    <tr key={cluster.ip} className="hover:bg-slate-800/40">
                      <td className="py-3 px-3 text-cyan-300 font-bold">{cluster.ip}</td>
                      <td className="py-3 px-3">
                        <span
                          className={`px-2 py-0.5 rounded text-xs font-bold ${
                            isThresholdExceeded
                              ? 'bg-rose-950 text-rose-300 border border-rose-800'
                              : 'bg-slate-800 text-slate-300'
                          }`}
                        >
                          {cluster.failureCount} Failures
                        </span>
                      </td>
                      <td className="py-3 px-3 text-slate-300 font-sans">
                        {cluster.targetedUsers.length > 0
                          ? cluster.targetedUsers.join(', ')
                          : 'Multiple'}
                      </td>
                      <td className="py-3 px-3">
                        {isThresholdExceeded ? (
                          <Badge severity="Critical">ALERT TRIGGERED (&ge;5)</Badge>
                        ) : (
                          <span className="text-slate-500 text-[11px]">Below Threshold (5)</span>
                        )}
                      </td>
                      <td className="py-3 px-3 text-slate-400 text-[11px]">
                        {cluster.lastSeen ? new Date(cluster.lastSeen).toLocaleString() : 'N/A'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
