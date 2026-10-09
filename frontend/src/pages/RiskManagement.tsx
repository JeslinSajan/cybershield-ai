import { useState, useEffect } from 'react';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Table } from '../components/ui/Table';
import { Modal } from '../components/ui/Modal';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { EmptyState } from '../components/ui/EmptyState';
import { riskService, DeviceRiskScore } from '../services/riskService';

export function RiskManagement() {
  const [scores, setScores] = useState<DeviceRiskScore[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [searchTerm, setSearchTerm] = useState<string>('');
  const [bandFilter, setBandFilter] = useState<string>('all');
  const [selectedScore, setSelectedScore] = useState<DeviceRiskScore | null>(null);

  const loadRiskScores = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await riskService.getRiskScores({
        risk_band: bandFilter !== 'all' ? bandFilter : undefined,
      });
      setScores(data);
    } catch (err: any) {
      setError(err?.message || 'Failed to load risk scores.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRiskScores();
  }, [bandFilter]);

  const filteredScores = scores.filter((s) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      (s.device_hostname && s.device_hostname.toLowerCase().includes(term)) ||
      (s.device_ip && s.device_ip.toLowerCase().includes(term)) ||
      (s.device_type && s.device_type.toLowerCase().includes(term))
    );
  });

  // Calculate summary counts
  const criticalCount = scores.filter((s) => s.risk_band === 'Critical').length;
  const highCount = scores.filter((s) => s.risk_band === 'High').length;
  const mediumCount = scores.filter((s) => s.risk_band === 'Medium').length;
  const lowCount = scores.filter((s) => s.risk_band === 'Low').length;
  const avgScore =
    scores.length > 0
      ? (scores.reduce((acc, curr) => acc + curr.score, 0) / scores.length).toFixed(1)
      : '0.0';

  const tableHeaders = ['Device', 'IP Address', 'Type', 'Risk Band', 'Score', 'Actions'];

  const tableRows = filteredScores.map((scoreItem) => [
    <div key="device">
      <div className="font-semibold text-slate-200">
        {scoreItem.device_hostname || 'Unknown Hostname'}
      </div>
      <div className="text-[10px] text-slate-500 font-mono">
        ID: {scoreItem.device_id.slice(0, 8)}...
      </div>
    </div>,
    <span key="ip" className="font-mono text-cyan-300">
      {scoreItem.device_ip || '—'}
    </span>,
    <span key="type" className="text-slate-400 capitalize">
      {scoreItem.device_type || 'Host'}
    </span>,
    <Badge key="band" severity={scoreItem.risk_band}>
      {scoreItem.risk_band}
    </Badge>,
    <div key="score" className="flex items-center gap-2">
      <div className="w-16 h-2 bg-slate-800 rounded-full overflow-hidden">
        <div
          className={`h-full ${
            scoreItem.score >= 75
              ? 'bg-red-500'
              : scoreItem.score >= 50
              ? 'bg-amber-500'
              : scoreItem.score >= 25
              ? 'bg-yellow-500'
              : 'bg-emerald-500'
          }`}
          style={{ width: `${Math.min(100, Math.max(3, scoreItem.score))}%` }}
        />
      </div>
      <span className="font-mono font-bold text-slate-200">{scoreItem.score}</span>
    </div>,
    <Button
      key="action"
      variant="secondary"
      size="sm"
      className="text-xs py-1 px-2.5"
      onClick={() => setSelectedScore(scoreItem)}
    >
      Breakdown
    </Button>,
  ]);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-slate-100 tracking-tight">Risk Scoring & Asset Exposure</h2>
            <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950/70 text-emerald-300 border border-emerald-800 font-mono">
              Phase 17 Live
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Dynamic asset risk quantification evaluated from active CVEs, open security alerts, and service exposure.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="secondary" onClick={loadRiskScores} disabled={loading} className="text-xs">
            <svg
              className={`w-3.5 h-3.5 mr-1.5 ${loading ? 'animate-spin' : ''}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            Refresh Scores
          </Button>
        </div>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        <div className="p-3 bg-slate-900 border border-slate-800 rounded-xl">
          <div className="text-[11px] font-medium text-slate-400">Avg Risk Score</div>
          <div className="text-xl font-bold text-slate-100 mt-0.5 font-mono">{avgScore}</div>
          <div className="text-[10px] text-slate-400 mt-0.5">Fleet-wide average</div>
        </div>

        <div className="p-3 bg-slate-900 border border-red-900/40 rounded-xl">
          <div className="text-[11px] font-medium text-red-300">Critical (75-100)</div>
          <div className="text-xl font-bold text-red-400 mt-0.5 font-mono">{criticalCount}</div>
          <div className="text-[10px] text-slate-400 mt-0.5">Immediate intervention</div>
        </div>

        <div className="p-3 bg-slate-900 border border-amber-900/40 rounded-xl">
          <div className="text-[11px] font-medium text-amber-300">High (50-74)</div>
          <div className="text-xl font-bold text-amber-400 mt-0.5 font-mono">{highCount}</div>
          <div className="text-[10px] text-slate-400 mt-0.5">Urgent containment</div>
        </div>

        <div className="p-3 bg-slate-900 border border-yellow-900/40 rounded-xl">
          <div className="text-[11px] font-medium text-yellow-300">Medium (25-49)</div>
          <div className="text-xl font-bold text-yellow-400 mt-0.5 font-mono">{mediumCount}</div>
          <div className="text-[10px] text-slate-400 mt-0.5">Elevated monitoring</div>
        </div>

        <div className="p-3 bg-slate-900 border border-emerald-900/40 rounded-xl">
          <div className="text-[11px] font-medium text-emerald-300">Low (0-24)</div>
          <div className="text-xl font-bold text-emerald-400 mt-0.5 font-mono">{lowCount}</div>
          <div className="text-[10px] text-slate-400 mt-0.5">Healthy baseline</div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <input
            type="text"
            placeholder="Search by device IP, hostname, or type..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition-colors"
          />
          <svg
            className="w-4 h-4 text-slate-500 absolute left-2.5 top-2.5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-xs text-slate-400">Risk Band:</label>
          <select
            value={bandFilter}
            onChange={(e) => setBandFilter(e.target.value)}
            className="bg-slate-900 border border-slate-700 text-xs text-slate-200 rounded-lg px-2.5 py-2 focus:outline-none focus:border-cyan-500"
          >
            <option value="all">All Bands</option>
            <option value="Critical">Critical</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
          </select>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-3 bg-red-950/50 border border-red-800 rounded-xl text-xs text-red-300 flex items-center justify-between">
          <span>{error}</span>
          <Button variant="secondary" onClick={loadRiskScores} className="text-xs py-1">
            Retry
          </Button>
        </div>
      )}

      {/* Main Table */}
      <Card>
        {loading ? (
          <div className="py-12 flex justify-center">
            <LoadingSpinner size="lg" message="Quantifying device risks..." />
          </div>
        ) : filteredScores.length === 0 ? (
          <EmptyState
            title="No Device Risk Records"
            description={
              searchTerm || bandFilter !== 'all'
                ? 'No devices match your search or filter criteria.'
                : 'No devices have been scored yet. Run discovery scans to detect devices and evaluate risks.'
            }
          />
        ) : (
          <Table headers={tableHeaders} rows={tableRows} />
        )}
      </Card>

      {/* Factor Breakdown Modal */}
      {selectedScore && (
        <Modal
          isOpen={true}
          title={`Risk Breakdown: ${selectedScore.device_hostname || selectedScore.device_ip || 'Device'}`}
          onClose={() => setSelectedScore(null)}
        >
          <div className="space-y-4 text-xs">
            {/* Header score box */}
            <div className="flex items-center justify-between p-3 bg-slate-950 border border-slate-800 rounded-xl">
              <div>
                <span className="text-slate-400 text-[11px]">Total Quantified Risk</span>
                <div className="text-2xl font-bold font-mono text-slate-100">
                  {selectedScore.score} / 100
                </div>
              </div>
              <Badge severity={selectedScore.risk_band}>{selectedScore.risk_band} Risk</Badge>
            </div>

            {/* Breakdown sections */}
            <div className="space-y-3">
              {/* Vulnerabilities */}
              <div className="p-3 bg-slate-900 border border-slate-800 rounded-lg space-y-2">
                <div className="flex items-center justify-between font-semibold text-slate-300">
                  <span>1. Vulnerability Findings</span>
                  <span className="font-mono text-cyan-400">
                    +{selectedScore.factor_breakdown?.vulnerabilities?.subtotal ?? 0} pts
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-400 font-mono">
                  <div>
                    Critical ({selectedScore.factor_breakdown?.vulnerabilities?.critical_count ?? 0}):{' '}
                    <span className="text-slate-200">
                      +{selectedScore.factor_breakdown?.vulnerabilities?.critical_score ?? 0}
                    </span>
                  </div>
                  <div>
                    High ({selectedScore.factor_breakdown?.vulnerabilities?.high_count ?? 0}):{' '}
                    <span className="text-slate-200">
                      +{selectedScore.factor_breakdown?.vulnerabilities?.high_score ?? 0}
                    </span>
                  </div>
                  <div>
                    Medium ({selectedScore.factor_breakdown?.vulnerabilities?.medium_count ?? 0}):{' '}
                    <span className="text-slate-200">
                      +{selectedScore.factor_breakdown?.vulnerabilities?.medium_score ?? 0}
                    </span>
                  </div>
                  <div>
                    Low ({selectedScore.factor_breakdown?.vulnerabilities?.low_count ?? 0}):{' '}
                    <span className="text-slate-200">
                      +{selectedScore.factor_breakdown?.vulnerabilities?.low_score ?? 0}
                    </span>
                  </div>
                </div>
              </div>

              {/* Active Alerts */}
              <div className="p-3 bg-slate-900 border border-slate-800 rounded-lg space-y-2">
                <div className="flex items-center justify-between font-semibold text-slate-300">
                  <span>2. Active Security Incidents</span>
                  <span className="font-mono text-amber-400">
                    +{selectedScore.factor_breakdown?.alerts?.subtotal ?? 0} pts
                  </span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-[11px] text-slate-400 font-mono">
                  <div>
                    Brute Force ({selectedScore.factor_breakdown?.alerts?.brute_force_count ?? 0}):{' '}
                    <span className="text-slate-200">
                      +{selectedScore.factor_breakdown?.alerts?.brute_force_score ?? 0}
                    </span>
                  </div>
                  <div>
                    Suspicious Login ({selectedScore.factor_breakdown?.alerts?.suspicious_login_count ?? 0}):{' '}
                    <span className="text-slate-200">
                      +{selectedScore.factor_breakdown?.alerts?.suspicious_login_score ?? 0}
                    </span>
                  </div>
                  <div>
                    Port Scan ({selectedScore.factor_breakdown?.alerts?.port_scan_count ?? 0}):{' '}
                    <span className="text-slate-200">
                      +{selectedScore.factor_breakdown?.alerts?.port_scan_score ?? 0}
                    </span>
                  </div>
                </div>
              </div>

              {/* Network Exposure */}
              <div className="p-3 bg-slate-900 border border-slate-800 rounded-lg space-y-2">
                <div className="flex items-center justify-between font-semibold text-slate-300">
                  <span>3. Network Surface Exposure</span>
                  <span className="font-mono text-purple-400">
                    +{selectedScore.factor_breakdown?.exposure?.exposure_score ?? 0} pts
                  </span>
                </div>
                <div className="text-[11px] text-slate-400 font-mono">
                  Open Ports Detected:{' '}
                  <span className="text-slate-200">
                    {selectedScore.factor_breakdown?.exposure?.open_ports_count ?? 0} ports
                  </span>{' '}
                  (&ge;10 open ports awards +10 exposure penalty)
                </div>
              </div>
            </div>

            <div className="pt-2 text-[10px] text-slate-500 font-mono flex justify-between items-center border-t border-slate-800">
              <span>Formula: {selectedScore.formula_version || 'v1'}</span>
              <span>Updated: {selectedScore.updated_at ? new Date(selectedScore.updated_at).toLocaleString() : '—'}</span>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
