import { useState, useEffect, useCallback } from 'react';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Table } from '../components/ui/Table';
import { Modal } from '../components/ui/Modal';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { EmptyState } from '../components/ui/EmptyState';
import { logsService, LogEntry } from '../services/logsService';

export function Logs() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [eventTypeFilter, setEventTypeFilter] = useState<string>('ALL');
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');
  const [sourceIpFilter, setSourceIpFilter] = useState<string>('');
  const [usernameFilter, setUsernameFilter] = useState<string>('');
  const [limit, setLimit] = useState<number>(50);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Detail Modal State
  const [selectedLog, setSelectedLog] = useState<LogEntry | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState<boolean>(false);
  const [copiedRaw, setCopiedRaw] = useState<boolean>(false);

  const fetchLogs = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await logsService.listLogs({
        event_type: eventTypeFilter,
        severity: severityFilter,
        source_ip: sourceIpFilter.trim() || undefined,
        username: usernameFilter.trim() || undefined,
        limit,
      });
      setLogs(data);
    } catch (err: any) {
      setError(err?.message || 'Failed to query security logs.');
    } finally {
      setIsLoading(false);
    }
  }, [eventTypeFilter, severityFilter, sourceIpFilter, usernameFilter, limit]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  const handleOpenDetail = (log: LogEntry) => {
    setSelectedLog(log);
    setIsDetailModalOpen(true);
  };

  const copyLogJson = () => {
    if (!selectedLog) return;
    navigator.clipboard.writeText(JSON.stringify(selectedLog, null, 2));
    setCopiedRaw(true);
    setTimeout(() => setCopiedRaw(false), 2000);
  };

  const tableHeaders = ['Timestamp', 'Severity', 'Event Type', 'Source IP', 'User', 'Message', 'Actions'];
  const tableRows = logs.map((log) => [
    <span className="font-mono text-slate-400 text-xs whitespace-nowrap">
      {log.timestamp ? new Date(log.timestamp).toLocaleString() : 'N/A'}
    </span>,
    <Badge severity={log.severity}>{log.severity.toUpperCase()}</Badge>,
    <span className="font-mono text-cyan-300 font-semibold text-xs">{log.event_type}</span>,
    <span className="font-mono text-slate-300 text-xs">{log.source_ip || 'Internal'}</span>,
    <span className="text-slate-300 text-xs">{log.username || <span className="text-slate-500 italic">None</span>}</span>,
    <span className="text-slate-300 text-xs truncate max-w-xs block" title={log.message}>
      {log.message}
    </span>,
    <Button
      variant="secondary"
      size="sm"
      onClick={(e) => {
        e.stopPropagation();
        handleOpenDetail(log);
      }}
    >
      Inspect
    </Button>,
  ]);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h2 className="text-xl font-bold text-slate-100 tracking-tight">Security Log Management & Audit Trail</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Centralized authentication events, host telemetry, and suspicious activity logs ingested via Phase 14 collectors.
          </p>
        </div>
        <Button variant="secondary" size="sm" onClick={fetchLogs} isLoading={isLoading}>
          Query Logs
        </Button>
      </div>

      {error && (
        <div className="p-3 bg-rose-950/60 border border-rose-800 rounded-lg text-xs text-rose-300">
          {error}
        </div>
      )}

      {/* Filters Bar */}
      <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-3">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          <div>
            <label className="block text-[11px] font-semibold text-slate-400 uppercase mb-1">Event Type</label>
            <select
              value={eventTypeFilter}
              onChange={(e) => setEventTypeFilter(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 text-xs rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
            >
              <option value="ALL">All Event Types</option>
              <option value="login_failure">login_failure (Failed Auth)</option>
              <option value="login_success">login_success (Success Auth)</option>
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-400 uppercase mb-1">Severity</label>
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 text-xs rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-cyan-500"
            >
              <option value="ALL">All Severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
              <option value="info">Info</option>
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-400 uppercase mb-1">Source IP Address</label>
            <input
              type="text"
              value={sourceIpFilter}
              onChange={(e) => setSourceIpFilter(e.target.value)}
              placeholder="e.g. 192.168.1.10"
              className="w-full bg-slate-950 border border-slate-800 text-xs rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
            />
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-400 uppercase mb-1">Target Username</label>
            <input
              type="text"
              value={usernameFilter}
              onChange={(e) => setUsernameFilter(e.target.value)}
              placeholder="e.g. root, admin"
              className="w-full bg-slate-950 border border-slate-800 text-xs rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-400 uppercase mb-1">Max Entries</label>
            <select
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
              className="w-full bg-slate-950 border border-slate-800 text-xs rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
            >
              <option value={25}>25 Rows</option>
              <option value={50}>50 Rows</option>
              <option value={100}>100 Rows</option>
              <option value={200}>200 Rows</option>
            </select>
          </div>
        </div>
      </div>

      {/* Table */}
      <Card>
        {isLoading && logs.length === 0 ? (
          <LoadingSpinner size="md" message="Streaming security logs from database..." />
        ) : logs.length === 0 ? (
          <EmptyState
            title="No log records matched"
            description="No log events match the query parameters. Monitored agent nodes stream authentication logs periodically."
          />
        ) : (
          <Table
            headers={tableHeaders}
            rows={tableRows}
            onRowClick={(idx) => handleOpenDetail(logs[idx])}
          />
        )}
      </Card>

      {/* LOG INSPECTION MODAL */}
      <Modal
        isOpen={isDetailModalOpen}
        onClose={() => setIsDetailModalOpen(false)}
        title="Security Log Inspector"
        description="Comprehensive audit record details and structured payload."
        maxWidth="lg"
      >
        {selectedLog && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 p-3 bg-slate-950/60 border border-slate-800 rounded-lg text-xs font-mono">
              <div>
                <span className="text-slate-500 font-sans text-[10px] uppercase font-semibold">Severity</span>
                <div className="mt-1">
                  <Badge severity={selectedLog.severity}>{selectedLog.severity.toUpperCase()}</Badge>
                </div>
              </div>
              <div>
                <span className="text-slate-500 font-sans text-[10px] uppercase font-semibold">Event Type</span>
                <p className="text-cyan-300 font-bold mt-1">{selectedLog.event_type}</p>
              </div>
              <div>
                <span className="text-slate-500 font-sans text-[10px] uppercase font-semibold">Source Subsystem</span>
                <p className="text-slate-300 mt-1">{selectedLog.source}</p>
              </div>
              <div>
                <span className="text-slate-500 font-sans text-[10px] uppercase font-semibold">Source IP</span>
                <p className="text-slate-300 mt-1">{selectedLog.source_ip || 'Internal / Local'}</p>
              </div>
              <div>
                <span className="text-slate-500 font-sans text-[10px] uppercase font-semibold">User Account</span>
                <p className="text-slate-300 mt-1">{selectedLog.username || 'Unspecified'}</p>
              </div>
              <div>
                <span className="text-slate-500 font-sans text-[10px] uppercase font-semibold">Recorded Time</span>
                <p className="text-slate-300 mt-1">
                  {selectedLog.timestamp ? new Date(selectedLog.timestamp).toLocaleTimeString() : 'N/A'}
                </p>
              </div>
            </div>

            <div>
              <span className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                Full Message
              </span>
              <p className="p-3 bg-slate-950 border border-slate-800 rounded-lg text-xs font-mono text-slate-200">
                {selectedLog.message}
              </p>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Raw JSON Record
                </span>
                <button
                  type="button"
                  onClick={copyLogJson}
                  className="text-xs font-semibold text-cyan-400 hover:text-cyan-300 font-mono"
                >
                  {copiedRaw ? 'Copied!' : 'Copy JSON'}
                </button>
              </div>
              <pre className="p-3 bg-slate-950 border border-slate-800 rounded-lg text-[11px] font-mono text-slate-300 overflow-x-auto max-h-48">
                {JSON.stringify(selectedLog, null, 2)}
              </pre>
            </div>

            <div className="pt-2 flex justify-end">
              <Button variant="secondary" size="sm" onClick={() => setIsDetailModalOpen(false)}>
                Close
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
