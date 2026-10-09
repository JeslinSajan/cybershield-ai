import { useState, useEffect, useCallback } from 'react';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Table } from '../components/ui/Table';
import { Modal } from '../components/ui/Modal';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { EmptyState } from '../components/ui/EmptyState';
import { devicesService, Device, DeviceVulnerability } from '../services/devicesService';
import { agentsService, Agent } from '../services/agentsService';
import { scansService } from '../services/scansService';
import { useAuth } from '../contexts/AuthContext';

export function Devices() {
  const { canScan } = useAuth();
  const [devices, setDevices] = useState<Device[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Detail Modal State
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);
  const [deviceVulns, setDeviceVulns] = useState<DeviceVulnerability[]>([]);
  const [isLoadingVulns, setIsLoadingVulns] = useState<boolean>(false);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState<boolean>(false);

  // Discovery Scan Modal State
  const [isScanModalOpen, setIsScanModalOpen] = useState<boolean>(false);
  const [onlineAgents, setOnlineAgents] = useState<Agent[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useState<string>('');
  const [targetScope, setTargetScope] = useState<string>('192.168.1.0/24');
  const [authorizedConsent, setAuthorizedConsent] = useState<boolean>(false);
  const [isStartingScan, setIsStartingScan] = useState<boolean>(false);
  const [scanMessage, setScanMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const fetchDevices = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await devicesService.listDevices(statusFilter);
      setDevices(data);
    } catch (err: any) {
      setError(err?.message || 'Failed to fetch discovered network devices.');
    } finally {
      setIsLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    fetchDevices();
  }, [fetchDevices]);

  const handleOpenDetails = async (device: Device) => {
    setSelectedDevice(device);
    setIsDetailModalOpen(true);
    setIsLoadingVulns(true);
    try {
      const vulns = await devicesService.getDeviceVulnerabilities(device.id);
      setDeviceVulns(vulns);
    } catch {
      setDeviceVulns([]);
    } finally {
      setIsLoadingVulns(false);
    }
  };

  const handleOpenScanModal = async () => {
    setScanMessage(null);
    setAuthorizedConsent(false);
    setIsScanModalOpen(true);
    try {
      const allAgents = await agentsService.listAgents('ONLINE');
      setOnlineAgents(allAgents);
      if (allAgents.length > 0) {
        setSelectedAgentId(allAgents[0].id);
      }
    } catch {
      setOnlineAgents([]);
    }
  };

  const handleStartDiscoveryScan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAgentId || !targetScope.trim() || !authorizedConsent) return;

    setIsStartingScan(true);
    setScanMessage(null);
    try {
      await scansService.createScan({
        agent_id: selectedAgentId,
        scan_type: 'discovery',
        target_scope: targetScope.trim(),
      });
      setScanMessage({
        type: 'success',
        text: 'Discovery scan task dispatched successfully! The agent will execute Nmap discovery.',
      });
      setTimeout(() => {
        setIsScanModalOpen(false);
        fetchDevices();
      }, 2000);
    } catch (err: any) {
      setScanMessage({
        type: 'error',
        text: err?.message || 'Failed to dispatch discovery scan task.',
      });
    } finally {
      setIsStartingScan(false);
    }
  };

  // Local search filter
  const filteredDevices = devices.filter((device) => {
    const q = searchQuery.toLowerCase();
    const matchIp = device.ip_address.toLowerCase().includes(q);
    const matchHost = (device.hostname || '').toLowerCase().includes(q);
    const matchMac = (device.mac_address || '').toLowerCase().includes(q);
    const matchVendor = (device.vendor || '').toLowerCase().includes(q);
    return matchIp || matchHost || matchMac || matchVendor;
  });

  const tableHeaders = ['Hostname', 'IP Address', 'MAC Address', 'Vendor', 'Type', 'Status', 'Last Seen', 'Actions'];
  const tableRows = filteredDevices.map((device) => [
    <span className="font-semibold text-white">
      {device.hostname || <span className="text-slate-500 italic">Unknown</span>}
    </span>,
    <span className="font-mono text-cyan-300 text-xs font-semibold">{device.ip_address}</span>,
    <span className="font-mono text-slate-400 text-xs">{device.mac_address || 'N/A'}</span>,
    <span className="text-slate-300 text-xs">{device.vendor || 'Generic'}</span>,
    <span className="text-slate-400 text-xs capitalize">{device.device_type || 'Unknown'}</span>,
    <Badge severity={device.status === 'online' ? 'success' : 'offline'}>
      {device.status.toUpperCase()}
    </Badge>,
    <span className="text-slate-400 text-xs font-mono">
      {device.last_seen_at ? new Date(device.last_seen_at).toLocaleString() : 'N/A'}
    </span>,
    <Button
      variant="secondary"
      size="sm"
      onClick={(e) => {
        e.stopPropagation();
        handleOpenDetails(device);
      }}
    >
      Details
    </Button>,
  ]);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h2 className="text-xl font-bold text-slate-100 tracking-tight">Discovered Devices Inventory</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Network endpoints identified via ARP/ICMP/Nmap ping scans by enrolled monitoring agents.
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
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            }
          >
            Run Discovery Scan
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-rose-950/60 border border-rose-800 rounded-lg text-xs text-rose-300">
          {error}
        </div>
      )}

      {/* Filters Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Filter by IP, hostname, or MAC..."
            className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 w-full sm:w-64 focus:outline-none focus:border-cyan-500"
          />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-900 border border-slate-800 text-xs rounded-lg px-3 py-1.5 text-slate-200 focus:outline-none focus:border-cyan-500"
          >
            <option value="ALL">All Reachability</option>
            <option value="online">Online</option>
            <option value="offline">Offline</option>
          </select>
        </div>
        <Button variant="secondary" size="sm" onClick={fetchDevices} isLoading={isLoading}>
          Refresh
        </Button>
      </div>

      {/* Table */}
      <Card>
        {isLoading && devices.length === 0 ? (
          <LoadingSpinner size="md" message="Scanning network device database..." />
        ) : filteredDevices.length === 0 ? (
          <EmptyState
            title="No devices found"
            description={
              searchQuery
                ? `No devices matching query "${searchQuery}".`
                : 'No network endpoints discovered yet. Run a discovery scan using an active agent.'
            }
            action={
              canScan && !searchQuery ? (
                <Button variant="primary" size="sm" onClick={handleOpenScanModal}>
                  Initiate First Discovery Scan
                </Button>
              ) : undefined
            }
          />
        ) : (
          <Table
            headers={tableHeaders}
            rows={tableRows}
            onRowClick={(idx) => handleOpenDetails(filteredDevices[idx])}
          />
        )}
      </Card>

      {/* DEVICE DETAILS MODAL */}
      <Modal
        isOpen={isDetailModalOpen}
        onClose={() => setIsDetailModalOpen(false)}
        title={selectedDevice ? `Device: ${selectedDevice.ip_address}` : 'Device Details'}
        description="Comprehensive endpoint hardware, network attributes, and vulnerability findings."
        maxWidth="xl"
      >
        {selectedDevice && (
          <div className="space-y-5">
            {/* Attributes Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 p-3.5 bg-slate-950/60 border border-slate-800 rounded-lg text-xs font-mono">
              <div>
                <p className="text-slate-500 text-[10px] uppercase font-sans font-semibold">IP Address</p>
                <p className="text-cyan-300 font-bold mt-1">{selectedDevice.ip_address}</p>
              </div>
              <div>
                <p className="text-slate-500 text-[10px] uppercase font-sans font-semibold">MAC Address</p>
                <p className="text-slate-200 mt-1">{selectedDevice.mac_address || 'Unresolved'}</p>
              </div>
              <div>
                <p className="text-slate-500 text-[10px] uppercase font-sans font-semibold">Hostname</p>
                <p className="text-slate-200 mt-1">{selectedDevice.hostname || 'None'}</p>
              </div>
              <div>
                <p className="text-slate-500 text-[10px] uppercase font-sans font-semibold">Vendor / Hardware</p>
                <p className="text-slate-200 mt-1">{selectedDevice.vendor || 'Unknown'}</p>
              </div>
              <div>
                <p className="text-slate-500 text-[10px] uppercase font-sans font-semibold">Device Type</p>
                <p className="text-slate-200 mt-1 capitalize">{selectedDevice.device_type || 'Generic'}</p>
              </div>
              <div>
                <p className="text-slate-500 text-[10px] uppercase font-sans font-semibold">Last Seen Reachable</p>
                <p className="text-slate-200 mt-1">
                  {selectedDevice.last_seen_at ? new Date(selectedDevice.last_seen_at).toLocaleString() : 'N/A'}
                </p>
              </div>
            </div>

            {/* Vulnerabilities Associated with Device */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                  Associated Vulnerabilities ({deviceVulns.length})
                </h4>
              </div>

              {isLoadingVulns ? (
                <LoadingSpinner size="sm" message="Querying CVE correlations..." />
              ) : deviceVulns.length === 0 ? (
                <div className="p-4 rounded-lg border border-dashed border-slate-800 text-center text-xs text-slate-500">
                  No vulnerabilities logged for this device. Run a Vulnerability Scan to assess service exposures.
                </div>
              ) : (
                <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                  {deviceVulns.map((vuln) => (
                    <div
                      key={vuln.id}
                      className="p-3 bg-slate-950/70 border border-slate-800 rounded-lg text-xs space-y-1.5"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Badge severity={vuln.severity}>{vuln.severity}</Badge>
                          <span className="font-mono text-cyan-300 font-semibold">
                            {vuln.cve_code || 'CVE-PENDING'}
                          </span>
                        </div>
                        <Badge variant={vuln.status}>{vuln.status}</Badge>
                      </div>
                      <p className="text-slate-300 text-[11px]">{vuln.description}</p>
                      {vuln.recommendation && (
                        <p className="text-[11px] text-emerald-400 font-sans">
                          Remediation: {vuln.recommendation}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="pt-2 flex justify-end">
              <Button variant="secondary" size="sm" onClick={() => setIsDetailModalOpen(false)}>
                Close
              </Button>
            </div>
          </div>
        )}
      </Modal>

      {/* RUN DISCOVERY SCAN MODAL */}
      <Modal
        isOpen={isScanModalOpen}
        onClose={() => setIsScanModalOpen(false)}
        title="Launch Network Discovery Scan"
        description="Dispatches a background Nmap network discovery job to a deployed agent."
      >
        <form onSubmit={handleStartDiscoveryScan} className="space-y-4">
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
            <label className="block text-xs font-semibold text-slate-300 mb-1">Executing Agent</label>
            {onlineAgents.length === 0 ? (
              <p className="text-xs text-rose-400 p-2.5 rounded bg-rose-950/40 border border-rose-900">
                No active ONLINE agents available. Ensure at least one agent is running and transmitting heartbeats before launching a scan.
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
            <label className="block text-xs font-semibold text-slate-300 mb-1">Target Network Scope / CIDR</label>
            <input
              type="text"
              value={targetScope}
              onChange={(e) => setTargetScope(e.target.value)}
              placeholder="e.g. 192.168.1.0/24 or 10.0.0.1-50"
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 font-mono focus:outline-none focus:border-cyan-500"
              required
            />
            <p className="text-[11px] text-slate-500 mt-1">Specify an authorized subnet CIDR or IP range reachable by the chosen agent.</p>
          </div>

          <div className="p-3 bg-amber-950/40 border border-amber-800/60 rounded-lg text-xs space-y-2">
            <p className="font-semibold text-amber-300">Authorization & Compliance Guard</p>
            <p className="text-[11px] text-slate-300">
              Network scans generate active packet probes. Only scan networks and IP ranges you own or are explicitly authorized to assess under contract.
            </p>
            <label className="flex items-center gap-2 pt-1 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={authorizedConsent}
                onChange={(e) => setAuthorizedConsent(e.target.checked)}
                className="rounded border-slate-700 text-cyan-600 focus:ring-cyan-500 bg-slate-900"
              />
              <span className="text-[11px] text-slate-200 font-medium">
                I confirm explicit authorization to scan this target scope.
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
              Start Discovery Scan
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
