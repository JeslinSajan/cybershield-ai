import { useState, useEffect, useCallback } from 'react';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Table } from '../components/ui/Table';
import { Modal } from '../components/ui/Modal';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { EmptyState } from '../components/ui/EmptyState';
import { alertsService, Alert, AlertsSummary } from '../services/alertsService';
import { useAuth } from '../contexts/AuthContext';

export function Alerts() {
  const { canScan } = useAuth(); // canScan = Admin or Analyst
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [summary, setSummary] = useState<AlertsSummary | null>(null);
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Detail & Triage Modal State
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [isLoadingDetail, setIsLoadingDetail] = useState<boolean>(false);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState<boolean>(false);
  const [triageReason, setTriageReason] = useState<string>('');
  const [isUpdatingStatus, setIsUpdatingStatus] = useState<boolean>(false);
  const [triageError, setTriageError] = useState<string | null>(null);

  const fetchAlertsAndSummary = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [alertsData, summaryData] = await Promise.all([
        alertsService.listAlerts({
          status: statusFilter,
          severity: severityFilter,
          limit: 100,
        }),
        alertsService.getSummary().catch(() => null),
      ]);
      setAlerts(alertsData);
      setSummary(summaryData);
    } catch (err: any) {
      setError(err?.message || 'Failed to retrieve security incident alerts.');
    } finally {
      setIsLoading(false);
    }
  }, [statusFilter, severityFilter]);

  useEffect(() => {
    fetchAlertsAndSummary();
  }, [fetchAlertsAndSummary]);

  const handleOpenDetail = async (alert: Alert) => {
    setSelectedAlert(alert);
    setTriageReason('');
    setTriageError(null);
    setIsDetailModalOpen(true);
    setIsLoadingDetail(true);
    try {
      const fullAlert = await alertsService.getAlert(alert.id);
      setSelectedAlert(fullAlert);
    } catch {
      // Use existing
    } finally {
      setIsLoadingDetail(false);
    }
  };

  const handleTransitionStatus = async (targetStatus: string) => {
    if (!selectedAlert) return;
    setIsUpdatingStatus(true);
    setTriageError(null);
    try {
      await alertsService.updateAlertStatus(selectedAlert.id, targetStatus, triageReason.trim() || undefined);
      // Refresh current alert details and list
      const updated = await alertsService.getAlert(selectedAlert.id);
      setSelectedAlert(updated);
      setTriageReason('');
      fetchAlertsAndSummary();
    } catch (err: any) {
      setTriageError(err?.message || `Failed to transition status to ${targetStatus}.`);
    } finally {
      setIsUpdatingStatus(false);
    }
  };

  const normStatus = (selectedAlert?.status || '').toLowerCase().replace(' ', '_');

  const tableHeaders = ['Severity', 'Status', 'Alert Type', 'Description', 'Risk Score', 'Triggered', 'Actions'];
  const tableRows = alerts.map((a) => [
    <Badge severity={a.severity}>{a.severity}</Badge>,
    <Badge variant={a.status}>{a.status}</Badge>,
    <span className="font-mono text-cyan-300 font-semibold text-xs capitalize">
      {a.alert_type.replace('_', ' ')}
    </span>,
    <span className="text-slate-300 text-xs truncate max-w-xs block" title={a.description}>
      {a.description}
    </span>,
    <span className="font-mono font-bold text-xs text-slate-200">
      {typeof a.risk_score === 'number' ? a.risk_score.toFixed(1) : a.risk_score}
    </span>,
    <span className="text-slate-400 text-xs font-mono">
      {a.triggered_at ? new Date(a.triggered_at).toLocaleString() : 'N/A'}
    </span>,
    <Button
      variant="secondary"
      size="sm"
      onClick={(e) => {
        e.stopPropagation();
        handleOpenDetail(a);
      }}
    >
      Triage
    </Button>,
  ]);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-slate-100 tracking-tight">Security Incident Alerts Triage</h2>
            <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950/70 text-emerald-300 border border-emerald-800 font-mono">
              Phase 16 Active
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Operational triage center: monitor detection alerts, transition investigation statuses, and review lifecycle audit history.
          </p>
        </div>
        <Button variant="secondary" size="sm" onClick={fetchAlertsAndSummary} isLoading={isLoading}>
          Refresh
        </Button>
      </div>

      {error && (
        <div className="p-3 bg-rose-950/60 border border-rose-800 rounded-lg text-xs text-rose-300">
          {error}
        </div>
      )}

      {/* Summary KPI Cards from Live /alerts/summary */}
      {summary && (
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          <div className="p-3 bg-slate-900 border border-rose-800/60 rounded-xl">
            <span className="text-[10px] uppercase font-bold text-rose-400">Open Incidents</span>
            <p className="text-2xl font-extrabold text-white mt-1">{summary.open}</p>
          </div>
          <div className="p-3 bg-slate-900 border border-amber-800/60 rounded-xl">
            <span className="text-[10px] uppercase font-bold text-amber-400">Acknowledged</span>
            <p className="text-2xl font-extrabold text-white mt-1">{summary.acknowledged}</p>
          </div>
          <div className="p-3 bg-slate-900 border border-cyan-800/60 rounded-xl">
            <span className="text-[10px] uppercase font-bold text-cyan-400">Investigating</span>
            <p className="text-2xl font-extrabold text-white mt-1">{summary.investigating}</p>
          </div>
          <div className="p-3 bg-slate-900 border border-emerald-800/60 rounded-xl">
            <span className="text-[10px] uppercase font-bold text-emerald-400">Resolved</span>
            <p className="text-2xl font-extrabold text-white mt-1">{summary.resolved}</p>
          </div>
          <div className="p-3 bg-slate-900 border border-slate-800 rounded-xl">
            <span className="text-[10px] uppercase font-bold text-slate-400">False Positives</span>
            <p className="text-2xl font-extrabold text-white mt-1">{summary.false_positive}</p>
          </div>
        </div>
      )}

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 font-medium">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-slate-900 border border-slate-800 text-xs rounded-lg px-3 py-1.5 text-slate-200 focus:outline-none focus:border-cyan-500"
            >
              <option value="ALL">All Statuses</option>
              <option value="Open">Open</option>
              <option value="Acknowledged">Acknowledged</option>
              <option value="Investigating">Investigating</option>
              <option value="Resolved">Resolved</option>
              <option value="False Positive">False Positive</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 font-medium">Severity:</span>
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="bg-slate-900 border border-slate-800 text-xs rounded-lg px-3 py-1.5 text-slate-200 focus:outline-none focus:border-cyan-500"
            >
              <option value="ALL">All Severities</option>
              <option value="Critical">Critical</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main Table */}
      <Card>
        {isLoading && alerts.length === 0 ? (
          <LoadingSpinner size="md" message="Connecting to incident alerts engine..." />
        ) : alerts.length === 0 ? (
          <EmptyState
            title="No alerts found"
            description={
              statusFilter !== 'ALL' || severityFilter !== 'ALL'
                ? 'No alerts match the selected filters.'
                : 'No alerts currently recorded in the database. When detection rules fire, incidents appear here.'
            }
          />
        ) : (
          <Table
            headers={tableHeaders}
            rows={tableRows}
            onRowClick={(idx) => handleOpenDetail(alerts[idx])}
          />
        )}
      </Card>

      {/* ALERT DETAIL & TRIAGE MODAL */}
      <Modal
        isOpen={isDetailModalOpen}
        onClose={() => setIsDetailModalOpen(false)}
        title={selectedAlert ? `Alert: ${selectedAlert.alert_type.replace('_', ' ')}` : 'Alert Investigation'}
        description="Review incident payload, examine audit event history, and transition lifecycle state."
        maxWidth="xl"
      >
        {isLoadingDetail && !selectedAlert?.history ? (
          <LoadingSpinner size="sm" message="Loading alert history..." />
        ) : selectedAlert ? (
          <div className="space-y-5">
            {triageError && (
              <div className="p-3 bg-rose-950/70 border border-rose-800 rounded-lg text-xs text-rose-300">
                {triageError}
              </div>
            )}

            {/* Incident Summary Banner */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-3 bg-slate-950/60 border border-slate-800 rounded-lg text-xs font-mono">
              <div>
                <span className="text-slate-500 font-sans text-[10px] uppercase font-semibold">Severity</span>
                <div className="mt-1">
                  <Badge severity={selectedAlert.severity}>{selectedAlert.severity}</Badge>
                </div>
              </div>
              <div>
                <span className="text-slate-500 font-sans text-[10px] uppercase font-semibold">Status</span>
                <div className="mt-1">
                  <Badge variant={selectedAlert.status}>{selectedAlert.status}</Badge>
                </div>
              </div>
              <div>
                <span className="text-slate-500 font-sans text-[10px] uppercase font-semibold">Risk Score</span>
                <p className="text-cyan-300 font-bold mt-1">
                  {typeof selectedAlert.risk_score === 'number'
                    ? selectedAlert.risk_score.toFixed(1)
                    : selectedAlert.risk_score}
                </p>
              </div>
              <div>
                <span className="text-slate-500 font-sans text-[10px] uppercase font-semibold">Triggered At</span>
                <p className="text-slate-300 text-[11px] mt-1">
                  {selectedAlert.triggered_at ? new Date(selectedAlert.triggered_at).toLocaleTimeString() : 'N/A'}
                </p>
              </div>
            </div>

            {/* Description */}
            <div>
              <span className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                Incident Description
              </span>
              <p className="p-3 bg-slate-950/70 border border-slate-800 rounded-lg text-xs text-slate-200">
                {selectedAlert.description}
              </p>
            </div>

            {/* Lifecycle Status Transition Controls */}
            <div className="p-3.5 bg-slate-950 border border-slate-800 rounded-xl space-y-3">
              <span className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Lifecycle State Transition (FR-12.2)
              </span>

              {!canScan ? (
                <p className="text-xs text-slate-500 italic">
                  Read-only: Security Analyst or Administrator permission required to update alert statuses.
                </p>
              ) : normStatus === 'resolved' || normStatus === 'false_positive' ? (
                <p className="text-xs text-slate-400">
                  This alert is closed ({selectedAlert.status}). Terminal lifecycle states cannot be re-opened.
                </p>
              ) : (
                <div className="space-y-3">
                  <input
                    type="text"
                    value={triageReason}
                    onChange={(e) => setTriageReason(e.target.value)}
                    placeholder="Optional reason for state change (e.g. Host verified, IP blocked)..."
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
                  />

                  <div className="flex flex-wrap gap-2">
                    {normStatus === 'open' && (
                      <>
                        <Button
                          variant="secondary"
                          size="sm"
                          isLoading={isUpdatingStatus}
                          onClick={() => handleTransitionStatus('Acknowledged')}
                        >
                          &rarr; Acknowledge
                        </Button>
                        <Button
                          variant="primary"
                          size="sm"
                          isLoading={isUpdatingStatus}
                          onClick={() => handleTransitionStatus('Investigating')}
                        >
                          &rarr; Investigate
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          isLoading={isUpdatingStatus}
                          onClick={() => handleTransitionStatus('False Positive')}
                        >
                          Mark False Positive
                        </Button>
                      </>
                    )}

                    {normStatus === 'acknowledged' && (
                      <>
                        <Button
                          variant="primary"
                          size="sm"
                          isLoading={isUpdatingStatus}
                          onClick={() => handleTransitionStatus('Investigating')}
                        >
                          &rarr; Investigate
                        </Button>
                        <Button
                          variant="secondary"
                          size="sm"
                          isLoading={isUpdatingStatus}
                          onClick={() => handleTransitionStatus('Resolved')}
                        >
                          Resolve Alert
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          isLoading={isUpdatingStatus}
                          onClick={() => handleTransitionStatus('False Positive')}
                        >
                          Mark False Positive
                        </Button>
                      </>
                    )}

                    {normStatus === 'investigating' && (
                      <>
                        <Button
                          variant="primary"
                          size="sm"
                          isLoading={isUpdatingStatus}
                          onClick={() => handleTransitionStatus('Resolved')}
                        >
                          Resolve Incident
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          isLoading={isUpdatingStatus}
                          onClick={() => handleTransitionStatus('False Positive')}
                        >
                          Mark False Positive
                        </Button>
                      </>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Audit History Timeline */}
            <div>
              <span className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                Status Change Audit History (FR-12.3)
              </span>
              {selectedAlert.history && selectedAlert.history.length > 0 ? (
                <div className="border border-slate-800 rounded-lg overflow-hidden">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-950 text-slate-400 uppercase text-[10px]">
                      <tr>
                        <th className="py-2 px-3">Timestamp</th>
                        <th className="py-2 px-3">From</th>
                        <th className="py-2 px-3">To</th>
                        <th className="py-2 px-3">Reason</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 bg-slate-900/60 font-mono">
                      {selectedAlert.history.map((ev) => (
                        <tr key={ev.id}>
                          <td className="py-2 px-3 text-slate-400 text-[11px]">
                            {ev.changed_at ? new Date(ev.changed_at).toLocaleString() : 'N/A'}
                          </td>
                          <td className="py-2 px-3 text-slate-400">{ev.from_status || 'Initial'}</td>
                          <td className="py-2 px-3 text-cyan-300 font-bold">{ev.to_status}</td>
                          <td className="py-2 px-3 text-slate-300 font-sans">
                            {ev.reason || <span className="text-slate-500 italic">None</span>}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-xs text-slate-500 italic p-3 bg-slate-950/40 rounded-lg border border-slate-800">
                  No state transitions recorded yet for this alert.
                </p>
              )}
            </div>

            <div className="pt-2 flex justify-end">
              <Button variant="secondary" size="sm" onClick={() => setIsDetailModalOpen(false)}>
                Close
              </Button>
            </div>
          </div>
        ) : null}
      </Modal>
    </div>
  );
}
