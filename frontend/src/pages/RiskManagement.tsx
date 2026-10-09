import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';

export function RiskManagement() {
  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-slate-100 tracking-tight">Risk Scoring & Asset Exposure</h2>
            <span className="text-[10px] px-2 py-0.5 rounded bg-amber-950/70 text-amber-300 border border-amber-800 font-mono">
              Phase 17 Feature
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Holistic device and organization risk quantification based on vulnerabilities, open port exposures, and security alerts.
          </p>
        </div>
      </div>

      {/* Honest Status Notice */}
      <div className="p-4 bg-slate-900 border border-amber-800/40 rounded-xl space-y-2 text-xs">
        <div className="flex items-center gap-2 text-amber-300 font-semibold">
          <svg className="w-4 h-4 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Implementation Status: Scheduled for Phase 17
        </div>
        <p className="text-slate-300 leading-relaxed">
          The Risk Scoring Service (<code className="text-cyan-300 font-mono">risk_service.py</code>) and corresponding REST endpoints
          (<code className="text-cyan-300 font-mono">GET /api/v1/risk-scores/</code> and <code className="text-cyan-300 font-mono">GET /api/v1/devices/{'{id}'}/risk</code>)
          will be implemented in Phase 17 following Alert Management (Phase 16).
        </p>
      </div>

      {/* Formula Specification Card */}
      <Card
        title="Risk Scoring Formula & Banding Model"
        description="Deterministic scoring specification defined in Phase 17 roadmap"
      >
        <div className="space-y-4 text-xs">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="p-3 bg-slate-950/60 border border-slate-800 rounded-lg space-y-1">
              <span className="text-slate-400 font-semibold">1. Vulnerability Weight</span>
              <ul className="text-slate-300 text-[11px] space-y-1 pt-1 font-mono">
                <li>• Critical CVE: +30 (max 30)</li>
                <li>• High CVE: +15 (max 30)</li>
                <li>• Medium CVE: +5 (max 15)</li>
                <li>• Low CVE: +2 (max 5)</li>
              </ul>
            </div>

            <div className="p-3 bg-slate-950/60 border border-slate-800 rounded-lg space-y-1">
              <span className="text-slate-400 font-semibold">2. Active Incident Weight</span>
              <ul className="text-slate-300 text-[11px] space-y-1 pt-1 font-mono">
                <li>• Open Brute Force: +20</li>
                <li>• Suspicious Login: +15</li>
                <li>• Open Port Sweep: +10</li>
              </ul>
            </div>

            <div className="p-3 bg-slate-950/60 border border-slate-800 rounded-lg space-y-1">
              <span className="text-slate-400 font-semibold">3. Network Exposure Weight</span>
              <ul className="text-slate-300 text-[11px] space-y-1 pt-1 font-mono">
                <li>• &ge;10 open ports: +10</li>
                <li>• Score capped at 100</li>
              </ul>
            </div>
          </div>

          <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg space-y-2">
            <span className="font-semibold text-slate-300">Risk Severity Bands:</span>
            <div className="flex flex-wrap gap-3">
              <div className="flex items-center gap-1.5">
                <Badge severity="Low">0 - 24: Low Risk</Badge>
              </div>
              <div className="flex items-center gap-1.5">
                <Badge severity="Medium">25 - 49: Medium Risk</Badge>
              </div>
              <div className="flex items-center gap-1.5">
                <Badge severity="High">50 - 74: High Risk</Badge>
              </div>
              <div className="flex items-center gap-1.5">
                <Badge severity="Critical">75 - 100: Critical Risk</Badge>
              </div>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}
