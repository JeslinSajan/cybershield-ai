import { useState, useEffect, useCallback } from 'react';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Table } from '../components/ui/Table';
import { Modal } from '../components/ui/Modal';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { EmptyState } from '../components/ui/EmptyState';
import { vulnerabilitiesService, Vulnerability } from '../services/vulnerabilitiesService';
import { agentsService, Agent } from '../services/agentsService';
import { scansService } from '../services/scansService';
import { useAuth } from '../contexts/AuthContext';

export function Vulnerabilities() {
  const { canScan } = useAuth();
  const [vulns, setVulns] = useState<Vulnerability[]>([]);
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // CVE Detail Modal State
  const [selectedVuln, setSelectedVuln] = useState<Vulnerability | null>(null);
  const [isLoadingDetail, setIsLoadingDetail] = useState<boolean>(false);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState<boolean>(false);

  // Vulnerability Scan Modal State
  const [isScanModalOpen, setIsScanModalOpen] = useState<boolean>(false);
  const [onlineAgents, setOnlineAgents] = useState<Agent[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useState<string>('');
  const [targetScope, setTargetScope] = useState<string>('');
  const [authorizedConsent, setAuthorizedConsent] = useState<boolean>(false);
  const [isStartingScan, setIsStartingScan] = useState<boolean>(false);
  const [scanMessage, setScanMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const fetchVulns = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await vulnerabilitiesService.listVulnerabilities({
        severity: severityFilter,
        status: statusFilter,
        limit: 100,
      });
      setVulns(data);
    } catch (err: any) {
      setError(err?.message || 'Failed to load vulnerability records.');
    } finally {
      setIsLoading(false);
    }
  }, [severityFilter, statusFilter]);

  useEffect(() => {
    fetchVulns();
  }, [fetchVulns]);

  const handleOpenDetail = async (vuln: Vulnerability) => {
    setSelectedVuln(vuln);
    setIsDetailModalOpen(true);
    setIsLoadingDetail(true);
    try {
      const fullVuln = await vulnerabilitiesService.getVulnerability(vuln.id);
      setSelectedVuln(fullVuln);
    } catch {
      // Use existing
    } finally {
      setIsLoadingDetail(false);
    }
  };

  const handleOpenScanModal = async () => {
    setScanMessage(null);
    setAuthorizedConsent(false);
    setIsScanModalOpen(true);
    try {
      const agents = await agentsService.listAgents('ONLINE');
      setOnlineAgents(agents);
      if (agents.length > 0) {
        setSelectedAgentId(agents[0].id);
      }
    } catch {
      setOnlineAgents([]);
    }
  };

  const handleStartVulnScan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAgentId || !targetScope.trim() || !authorizedConsent) return;

    setIsStartingScan(true);
    setScanMessage(null);
    try {
      await scansService.createScan({
        agent_id: selectedAgentId,
        scan_type: 'vulnerability',
        target_scope: targetScope.trim(),
      });
      setScanMessage({
        type: 'success',
        text: 'Vulnerability scan task dispatched! The agent will run service detection (Nmap -sV) and match findings with CVE catalog.',
      });
      setTimeout(() => {
        setIsScanModalOpen(false);
        fetchVulns();
      }, 2000);
    } catch (err: any) {
      setScanMessage({
        type: 'error',
        text: err?.message || 'Failed to dispatch vulnerability scan.',
      });
    } finally {
      setIsStartingScan(false);
    }
  };

  const tableHeaders = ['Severity', 'CVE Identifier', 'CVSS Score', 'Vulnerability Description', 'Status', 'Discovered', 'Actions'];
  const tableRows = vulns.map((v) => [
    <Badge severity={v.severity}>{v.severity}</Badge>,
    <span className="font-mono text-cyan-300 font-bold text-xs">{v.cve_code || 'CVE-RECORD'}</span>,
    <span className="font-mono font-bold text-xs text-slate-200">
      {v.score !== null ? v.score.toFixed(1) : 'N/A'}
    </span>,
    <span className="text-slate-300 text-xs truncate max-w-xs block" title={v.description}>
      {v.description}
    </span>,
    <Badge variant={v.status}>{v.status.toUpperCase()}</Badge>,
    <span className="text-slate-400 text-xs font-mono">
      {v.created_at ? new Date(v.created_at).toLocaleDateString() : 'N/A'}
    </span>,
    <Button
      variant="secondary"
      size="sm"
      onClick={(e) => {
        e.stopPropagation();
        handleOpenDetail(v);
      }}
    >
      CVE Intel
    </Button>,
  ]);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h2 className="text-xl font-bold text-slate-100 tracking-tight">Vulnerability Management & CVE Findings</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Security weaknesses detected by endpoint banner scanning, matched against the local CVE advisory database.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="primary"
            size="sm"
            disabledReason={!canScan ? 'Security Analyst or Administrator role required to initiate scans' : undefined}
            onClick={handleOpenScanModal}
            icon={
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            }
          >
            Run Vulnerability Scan
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-rose-950/60 border border-rose-800 rounded-lg text-xs text-rose-300">
          {error}
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
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

          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 font-medium">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-slate-900 border border-slate-800 text-xs rounded-lg px-3 py-1.5 text-slate-200 focus:outline-none focus:border-cyan-500"
            >
              <option value="ALL">All Statuses</option>
              <option value="open">Open</option>
              <option value="resolved">Resolved</option>
            </select>
          </div>
        </div>

        <Button variant="secondary" size="sm" onClick={fetchVulns} isLoading={isLoading}>
          Refresh
        </Button>
      </div>

      {/* Table */}
      <Card>
        {isLoading && vulns.length === 0 ? (
          <LoadingSpinner size="md" message="Scanning vulnerability database..." />
        ) : vulns.length === 0 ? (
          <EmptyState
            title="No vulnerabilities identified"
            description={
              severityFilter !== 'ALL' || statusFilter !== 'ALL'
                ? 'No vulnerabilities matching the selected filters.'
                : 'No vulnerabilities logged yet. Execute a Vulnerability Scan on discovered network devices to scan services.'
            }
            action={
              canScan ? (
                <Button variant="primary" size="sm" onClick={handleOpenScanModal}>
                  Initiate First Vulnerability Scan
                </Button>
              ) : undefined
            }
          />
        ) : (
          <Table
            headers={tableHeaders}
            rows={tableRows}
            onRowClick={(idx) => handleOpenDetail(vulns[idx])}
          />
        )}
      </Card>

      {/* CVE DETAIL MODAL */}
      <Modal
        isOpen={isDetailModalOpen}
        onClose={() => setIsDetailModalOpen(false)}
        title={selectedVuln?.cve_code || 'Vulnerability Detail'}
        description="Detailed CVE metadata, affected service banners, and remediation guidelines."
        maxWidth="xl"
      >
        {isLoadingDetail ? (
          <LoadingSpinner size="sm" message="Loading CVE advisory intelligence..." />
        ) : selectedVuln ? (
          <div className="space-y-4">
            {/* Header Badge Strip */}
            <div className="flex items-center justify-between p-3 bg-slate-950/60 border border-slate-800 rounded-lg text-xs">
              <div className="flex items-center gap-2">
                <span className="text-slate-400">Severity:</span>
                <Badge severity={selectedVuln.severity}>{selectedVuln.severity}</Badge>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-slate-400">CVSS Score:</span>
                <span className="font-mono font-bold text-rose-400">
                  {selectedVuln.score !== null ? selectedVuln.score.toFixed(1) : 'N/A'}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-slate-400">Status:</span>
                <Badge variant={selectedVuln.status}>{selectedVuln.status.toUpperCase()}</Badge>
              </div>
            </div>

            {/* Description */}
            <div>
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                Vulnerability Summary
              </h4>
              <p className="text-xs text-slate-200 bg-slate-950/40 p-3 rounded-lg border border-slate-800">
                {selectedVuln.cve_details?.summary || selectedVuln.description}
              </p>
            </div>

            {/* Affected Service Details */}
            {selectedVuln.cve_details && (
              <div className="grid grid-cols-2 gap-3 text-xs font-mono">
                <div className="p-2.5 bg-slate-950 border border-slate-800 rounded-lg">
                  <span className="text-slate-500 font-sans text-[10px] uppercase font-semibold">Affected Service</span>
                  <p className="text-cyan-300 mt-1">{selectedVuln.cve_details.affected_service || 'N/A'}</p>
                </div>
                <div className="p-2.5 bg-slate-950 border border-slate-800 rounded-lg">
                  <span className="text-slate-500 font-sans text-[10px] uppercase font-semibold">Affected Version</span>
                  <p className="text-cyan-300 mt-1">{selectedVuln.cve_details.affected_version || 'N/A'}</p>
                </div>
              </div>
            )}

            {/* Recommendation */}
            <div>
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                Remediation & Recommendation
              </h4>
              <div className="p-3 bg-emerald-950/40 border border-emerald-800/60 rounded-lg text-xs text-emerald-300">
                {selectedVuln.cve_details?.recommendation || selectedVuln.recommendation || 'Apply the latest security patches provided by the software vendor.'}
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <Button variant="secondary" size="sm" onClick={() => setIsDetailModalOpen(false)}>
                Close
              </Button>
            </div>
          </div>
        ) : null}
      </Modal>

      {/* RUN VULNERABILITY SCAN MODAL */}
      <Modal
        isOpen={isScanModalOpen}
        onClose={() => setIsScanModalOpen(false)}
        title="Launch Vulnerability Scan (Nmap -sV)"
        description="Executes service version detection on a target IP address and correlates findings against CVE database."
      >
        <form onSubmit={handleStartVulnScan} className="space-y-4">
          {scanMessage && (
            <div
              className={`p-3 rounded-lg text-xs border ${
                scanMessage.type === 'success'
                  ? 'bg-emerald-950/70 border-emerald-800 text-emerald-300'
                  : 'bg-rose-950/70 border-rose-800 text-rose-300'
              }`}
            >
              {scanMessage.text}
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Scanning Agent Node</label>
            {onlineAgents.length === 0 ? (
              <p className="text-xs text-rose-400 p-2.5 rounded bg-rose-950/40 border border-rose-900">
                No active ONLINE agents found. A running agent is required to execute network service scans.
              </p>
            ) : (
              <select
                value={selectedAgentId}
                onChange={(e) => setSelectedAgentId(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
                required
              >
                {onlineAgents.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.name} ({a.hostname}) - ONLINE
                  </option>
                ))}
              </select>
            )}
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Target Host IP Address</label>
            <input
              type="text"
              value={targetScope}
              onChange={(e) => setTargetScope(e.target.value)}
              placeholder="e.g. 192.168.1.50 or 10.0.0.15"
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 font-mono focus:outline-none focus:border-cyan-500"
              required
            />
            <p className="text-[11px] text-slate-500 mt-1">Single IP address of the target host to assess for open ports and services.</p>
          </div>

          <div className="p-3 bg-amber-950/40 border border-amber-800/60 rounded-lg text-xs space-y-2">
            <p className="font-semibold text-amber-300">Authorized Target Confirmation</p>
            <p className="text-[11px] text-slate-300">
              Vulnerability scans interrogate network services using banner probing. Ensure the target system is authorized for security assessment.
            </p>
            <label className="flex items-center gap-2 pt-1 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={authorizedConsent}
                onChange={(e) => setAuthorizedConsent(e.target.checked)}
                className="rounded border-slate-700 text-cyan-600 focus:ring-cyan-500 bg-slate-900"
              />
              <span className="text-[11px] text-slate-200 font-medium">
                I verify that this target system is authorized for vulnerability scanning.
              </span>
            </label>
          </div>

          <div className="pt-3 flex justify-end gap-2">
            <Button type="button" variant="secondary" size="sm" onClick={() => setIsScanModalOpen(false)}>
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              isLoading={isStartingScan}
              disabled={onlineAgents.length === 0 || !authorizedConsent}
            >
              Start Vulnerability Scan
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
