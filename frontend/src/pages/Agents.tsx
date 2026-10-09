import { useState, useEffect, useCallback } from 'react';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Table } from '../components/ui/Table';
import { Modal } from '../components/ui/Modal';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { EmptyState } from '../components/ui/EmptyState';
import { agentsService, Agent } from '../services/agentsService';
import { useAuth } from '../contexts/AuthContext';

export function Agents() {
  const { isAdmin } = useAuth();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Detail Modal State
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [isLoadingDetails, setIsLoadingDetails] = useState<boolean>(false);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState<boolean>(false);

  // Generate Token Modal State
  const [isTokenModalOpen, setIsTokenModalOpen] = useState<boolean>(false);
  const [tokenAgentName, setTokenAgentName] = useState<string>('');
  const [tokenExpiry, setTokenExpiry] = useState<number>(60);
  const [generatedToken, setGeneratedToken] = useState<{ token: string; expires_at: string } | null>(null);
  const [isGeneratingToken, setIsGeneratingToken] = useState<boolean>(false);
  const [tokenError, setTokenError] = useState<string | null>(null);
  const [copiedToken, setCopiedToken] = useState<boolean>(false);

  // Revoke Modal State
  const [isRevokeModalOpen, setIsRevokeModalOpen] = useState<boolean>(false);
  const [agentToRevoke, setAgentToRevoke] = useState<Agent | null>(null);
  const [isRevoking, setIsRevoking] = useState<boolean>(false);
  const [revokeError, setRevokeError] = useState<string | null>(null);

  const fetchAgents = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await agentsService.listAgents(statusFilter);
      setAgents(data);
    } catch (err: any) {
      setError(err?.message || 'Failed to load monitoring agents.');
    } finally {
      setIsLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    fetchAgents();
    const interval = setInterval(fetchAgents, 30000); // 30s auto-refresh
    return () => clearInterval(interval);
  }, [fetchAgents]);

  const handleOpenDetails = async (agent: Agent) => {
    setIsDetailModalOpen(true);
    setIsLoadingDetails(true);
    setSelectedAgent(agent);
    try {
      const fullAgent = await agentsService.getAgent(agent.id);
      setSelectedAgent(fullAgent);
    } catch (err) {
      // Fall back to current agent object
    } finally {
      setIsLoadingDetails(false);
    }
  };

  const handleGenerateToken = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!tokenAgentName.trim()) return;

    setIsGeneratingToken(true);
    setTokenError(null);
    try {
      const result = await agentsService.generateEnrollmentToken(tokenAgentName.trim(), tokenExpiry);
      setGeneratedToken(result);
      fetchAgents();
    } catch (err: any) {
      setTokenError(err?.message || 'Failed to generate enrollment token.');
    } finally {
      setIsGeneratingToken(false);
    }
  };

  const handleRevokeAgent = async () => {
    if (!agentToRevoke) return;
    setIsRevoking(true);
    setRevokeError(null);
    try {
      await agentsService.revokeAgent(agentToRevoke.id);
      setIsRevokeModalOpen(false);
      setAgentToRevoke(null);
      fetchAgents();
      if (selectedAgent && selectedAgent.id === agentToRevoke.id) {
        setIsDetailModalOpen(false);
      }
    } catch (err: any) {
      setRevokeError(err?.message || 'Failed to revoke agent.');
    } finally {
      setIsRevoking(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedToken(true);
    setTimeout(() => setCopiedToken(false), 2000);
  };

  const tableHeaders = ['Agent Name', 'Hostname', 'Status', 'Version', 'Last Heartbeat', 'Actions'];
  const tableRows = agents.map((agent) => [
    <div className="font-semibold text-white flex items-center gap-2">
      <div
        className={`w-2 h-2 rounded-full ${
          agent.status === 'ONLINE' ? 'bg-emerald-400' : agent.status === 'PENDING' ? 'bg-amber-400' : 'bg-slate-500'
        }`}
      />
      <span>{agent.name}</span>
    </div>,
    <span className="font-mono text-slate-300 text-xs">{agent.hostname}</span>,
    <Badge severity={agent.status}>{agent.status}</Badge>,
    <span className="font-mono text-xs text-slate-400">{agent.version}</span>,
    <span className="text-slate-400 text-xs font-mono">
      {agent.last_heartbeat_at ? new Date(agent.last_heartbeat_at).toLocaleString() : 'Never'}
    </span>,
    <div className="flex items-center gap-2">
      <Button
        variant="secondary"
        size="sm"
        onClick={(e) => {
          e.stopPropagation();
          handleOpenDetails(agent);
        }}
      >
        Details
      </Button>
      {agent.is_active && (
        <Button
          variant="danger"
          size="sm"
          disabledReason={!isAdmin ? 'Administrator role required to revoke agents' : undefined}
          onClick={(e) => {
            e.stopPropagation();
            setAgentToRevoke(agent);
            setRevokeError(null);
            setIsRevokeModalOpen(true);
          }}
        >
          Revoke
        </Button>
      )}
    </div>,
  ]);

  return (
    <div className="p-6 space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h2 className="text-xl font-bold text-slate-100 tracking-tight">Agent Fleet Management</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Manage deployed endpoint sensors, inspect system telemetry, and generate enrollment credentials.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="primary"
            size="sm"
            disabledReason={!isAdmin ? 'Administrator role required to generate enrollment tokens' : undefined}
            onClick={() => {
              setTokenAgentName('');
              setGeneratedToken(null);
              setTokenError(null);
              setIsTokenModalOpen(true);
            }}
            icon={
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
            }
          >
            Generate Enrollment Token
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-rose-950/60 border border-rose-800 rounded-lg text-xs text-rose-300">
          {error}
        </div>
      )}

      {/* Filter and Actions Bar */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 font-medium">Status Filter:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-900 border border-slate-800 text-xs rounded-lg px-3 py-1.5 text-slate-200 focus:outline-none focus:border-cyan-500"
          >
            <option value="ALL">All Statuses</option>
            <option value="ONLINE">ONLINE (Active Heartbeat)</option>
            <option value="OFFLINE">OFFLINE</option>
            <option value="PENDING">PENDING</option>
          </select>
        </div>
        <Button
          variant="secondary"
          size="sm"
          onClick={fetchAgents}
          isLoading={isLoading}
        >
          Refresh (30s auto)
        </Button>
      </div>

      {/* Agents Table or Empty State */}
      <Card>
        {isLoading && agents.length === 0 ? (
          <LoadingSpinner size="md" message="Connecting to agent registry..." />
        ) : agents.length === 0 ? (
          <EmptyState
            title="No agents found"
            description={
              statusFilter === 'ALL'
                ? 'No monitoring agents have been enrolled yet. Generate a token to enroll your first host.'
                : `No agents found with status "${statusFilter}".`
            }
            action={
              isAdmin && statusFilter === 'ALL' ? (
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => {
                    setTokenAgentName('');
                    setGeneratedToken(null);
                    setTokenError(null);
                    setIsTokenModalOpen(true);
                  }}
                >
                  Generate First Token
                </Button>
              ) : undefined
            }
          />
        ) : (
          <Table
            headers={tableHeaders}
            rows={tableRows}
            onRowClick={(index) => handleOpenDetails(agents[index])}
          />
        )}
      </Card>

      {/* GENERATE TOKEN MODAL */}
      <Modal
        isOpen={isTokenModalOpen}
        onClose={() => setIsTokenModalOpen(false)}
        title="Generate Agent Enrollment Token"
        description="One-time enrollment token used by the CyberShield Python agent on initial boot."
      >
        {generatedToken ? (
          <div className="space-y-4">
            <div className="p-3 bg-emerald-950/60 border border-emerald-800/80 rounded-lg text-xs space-y-2">
              <p className="font-semibold text-emerald-300">Enrollment Token Ready</p>
              <p className="text-slate-300">
                Configure this token in your agent's <code className="text-emerald-300">.env</code> file under{' '}
                <code className="text-emerald-300">ENROLLMENT_TOKEN</code>.
              </p>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1">One-Time Token Value</label>
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  readOnly
                  value={generatedToken.token}
                  className="bg-slate-950 border border-slate-700 font-mono text-xs text-cyan-300 rounded-lg px-3 py-2 w-full select-all focus:outline-none"
                />
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => copyToClipboard(generatedToken.token)}
                >
                  {copiedToken ? 'Copied!' : 'Copy'}
                </Button>
              </div>
              <p className="text-[11px] text-slate-500 mt-1 font-mono">
                Expires at: {new Date(generatedToken.expires_at).toLocaleString()}
              </p>
            </div>

            <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg text-[11px] text-slate-400 font-mono space-y-1">
              <p className="text-slate-300 font-semibold">Agent Command:</p>
              <p className="text-cyan-400">$ cd agent</p>
              <p className="text-cyan-400">$ python -m agent.main</p>
            </div>

            <div className="pt-2 flex justify-end">
              <Button
                variant="primary"
                size="sm"
                onClick={() => setIsTokenModalOpen(false)}
              >
                Done
              </Button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleGenerateToken} className="space-y-4">
            {tokenError && (
              <div className="p-2.5 rounded bg-rose-950/60 border border-rose-800 text-xs text-rose-300">
                {tokenError}
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Agent / Host Identifier</label>
              <input
                type="text"
                value={tokenAgentName}
                onChange={(e) => setTokenAgentName(e.target.value)}
                placeholder="e.g. corp-workstation-01"
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
                required
              />
              <p className="text-[11px] text-slate-500 mt-1">Name to identify this machine in the SOC dashboard.</p>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Token Validity Duration</label>
              <select
                value={tokenExpiry}
                onChange={(e) => setTokenExpiry(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
              >
                <option value={15}>15 Minutes</option>
                <option value={60}>1 Hour (Standard)</option>
                <option value={360}>6 Hours</option>
                <option value={1440}>24 Hours</option>
              </select>
            </div>

            <div className="pt-3 flex justify-end gap-2">
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={() => setIsTokenModalOpen(false)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                size="sm"
                isLoading={isGeneratingToken}
              >
                Create Token
              </Button>
            </div>
          </form>
        )}
      </Modal>

      {/* AGENT DETAIL DRAWER / MODAL */}
      <Modal
        isOpen={isDetailModalOpen}
        onClose={() => setIsDetailModalOpen(false)}
        title={selectedAgent ? `Agent: ${selectedAgent.name}` : 'Agent Telemetry'}
        maxWidth="xl"
      >
        {isLoadingDetails && !selectedAgent?.recent_heartbeats ? (
          <LoadingSpinner size="sm" message="Loading heartbeat metrics..." />
        ) : selectedAgent ? (
          <div className="space-y-5">
            {/* Metadata Summary */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-3 bg-slate-950/60 border border-slate-800 rounded-lg text-xs">
              <div>
                <p className="text-slate-500 text-[10px] uppercase font-semibold">Status</p>
                <div className="mt-1">
                  <Badge severity={selectedAgent.status}>{selectedAgent.status}</Badge>
                </div>
              </div>
              <div>
                <p className="text-slate-500 text-[10px] uppercase font-semibold">Hostname</p>
                <p className="text-slate-200 font-mono mt-1 truncate">{selectedAgent.hostname}</p>
              </div>
              <div>
                <p className="text-slate-500 text-[10px] uppercase font-semibold">Version</p>
                <p className="text-slate-200 font-mono mt-1">{selectedAgent.version}</p>
              </div>
              <div>
                <p className="text-slate-500 text-[10px] uppercase font-semibold">Enrolled</p>
                <p className="text-slate-200 font-mono mt-1">
                  {new Date(selectedAgent.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>

            {/* Heartbeat Telemetry Table */}
            <div>
              <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider mb-2">
                Recent Heartbeats (Last 10)
              </h4>
              {selectedAgent.recent_heartbeats && selectedAgent.recent_heartbeats.length > 0 ? (
                <div className="border border-slate-800 rounded-lg overflow-hidden">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-950 border-b border-slate-800 text-slate-400">
                      <tr>
                        <th className="py-2 px-3">Timestamp</th>
                        <th className="py-2 px-3">Status</th>
                        <th className="py-2 px-3">CPU %</th>
                        <th className="py-2 px-3">Memory %</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 bg-slate-900/60 font-mono">
                      {selectedAgent.recent_heartbeats.map((hb) => (
                        <tr key={hb.id}>
                          <td className="py-2 px-3 text-slate-300">
                            {new Date(hb.timestamp).toLocaleTimeString()}
                          </td>
                          <td className="py-2 px-3">
                            <Badge severity={hb.status}>{hb.status}</Badge>
                          </td>
                          <td className="py-2 px-3 text-slate-300">
                            {hb.cpu_percent !== null ? `${hb.cpu_percent}%` : 'N/A'}
                          </td>
                          <td className="py-2 px-3 text-slate-300">
                            {hb.memory_percent !== null ? `${hb.memory_percent}%` : 'N/A'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-xs text-slate-500 italic">No heartbeats recorded yet for this agent.</p>
              )}
            </div>

            <div className="pt-2 flex justify-end">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setIsDetailModalOpen(false)}
              >
                Close
              </Button>
            </div>
          </div>
        ) : null}
      </Modal>

      {/* CONFIRM REVOKE MODAL */}
      <Modal
        isOpen={isRevokeModalOpen}
        onClose={() => setIsRevokeModalOpen(false)}
        title="Revoke Agent Credentials"
        description="Permanent security revocation action (Administrator only)."
      >
        <div className="space-y-4">
          {revokeError && (
            <div className="p-2.5 rounded bg-rose-950/60 border border-rose-800 text-xs text-rose-300">
              {revokeError}
            </div>
          )}

          <p className="text-xs text-slate-300">
            Are you sure you want to revoke agent{' '}
            <strong className="text-white">{agentToRevoke?.name}</strong>?
          </p>
          <p className="text-xs text-rose-400 bg-rose-950/40 p-2.5 rounded border border-rose-900/50">
            This will immediately deactivate all API authentication tokens for this agent. It will be unable to send heartbeats, execute tasks, or ingest security logs.
          </p>

          <div className="pt-3 flex justify-end gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setIsRevokeModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              variant="danger"
              size="sm"
              isLoading={isRevoking}
              onClick={handleRevokeAgent}
            >
              Confirm Revocation
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
