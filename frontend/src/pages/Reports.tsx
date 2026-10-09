import { useState, useEffect } from 'react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { EmptyState } from '../components/ui/EmptyState';
import { apiFetch } from '../services/api';

export function Reports() {
  const [apiResponse, setApiResponse] = useState<any>(null);
  const [reportType, setReportType] = useState<string>('security_overview');
  const [format, setFormat] = useState<'pdf' | 'csv'>('pdf');
  const [dateRange, setDateRange] = useState<string>('30d');

  useEffect(() => {
    const fetchReports = async () => {
      try {
        const res = await apiFetch<any>('/reports/');
        setApiResponse(res);
      } catch (err: any) {
        setApiResponse({ error: err?.message || 'Endpoint returned error' });
      }
    };
    fetchReports();
  }, []);

  const isStubEndpoint =
    apiResponse &&
    (apiResponse.message?.includes('Not implemented yet') ||
      apiResponse.message?.includes('Phase') ||
      !Array.isArray(apiResponse));

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-slate-100 tracking-tight">Compliance & Executive Reporting</h2>
            <span className="text-[10px] px-2 py-0.5 rounded bg-amber-950/70 text-amber-300 border border-amber-800 font-mono">
              Phase 20 Implementation Target
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Automated PDF and CSV security summary export for stakeholders, compliance audits, and incident documentation.
          </p>
        </div>
      </div>

      {/* Honest Backend Integration Banner */}
      <div className="p-4 bg-slate-900 border border-amber-800/40 rounded-xl space-y-2 text-xs">
        <div className="flex items-center gap-2 text-amber-300 font-semibold">
          <svg className="w-4 h-4 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Backend Integration Notice: Scheduled for Phase 20
        </div>
        <p className="text-slate-300 leading-relaxed">
          The PDF document generator (<code className="text-cyan-300 font-mono">fpdf2</code> library integration) and CSV streaming endpoints
          (<code className="text-cyan-300 font-mono">POST /api/v1/reports/</code> and <code className="text-cyan-300 font-mono">GET /api/v1/reports/{'{id}'}/download</code>)
          will be implemented in <strong>Phase 20</strong>.
        </p>
        <p className="text-slate-400 font-mono text-[11px]">
          Current Backend Endpoint Status: {JSON.stringify(apiResponse)}
        </p>
      </div>

      {/* Generation Control Panel (Visual Interface Prepared for Phase 20) */}
      <Card
        title="Report Generation Parameters"
        description="Select report scope, timeframe, and export document format"
      >
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">Report Type</label>
            <select
              value={reportType}
              onChange={(e) => setReportType(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
            >
              <option value="security_overview">Executive Security Overview</option>
              <option value="vulnerability">Vulnerability & CVE Assessment</option>
              <option value="alert">Incident & Alert Audit Trail</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">Period Timeframe</label>
            <select
              value={dateRange}
              onChange={(e) => setDateRange(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
            >
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days (Monthly)</option>
              <option value="90d">Last 90 Days (Quarterly)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">Export Format</label>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setFormat('pdf')}
                className={`flex-1 py-2 rounded-lg text-xs font-semibold border transition-colors ${
                  format === 'pdf'
                    ? 'bg-cyan-600/20 text-cyan-300 border-cyan-600'
                    : 'bg-slate-950 text-slate-400 border-slate-800'
                }`}
              >
                PDF Document
              </button>
              <button
                type="button"
                onClick={() => setFormat('csv')}
                className={`flex-1 py-2 rounded-lg text-xs font-semibold border transition-colors ${
                  format === 'csv'
                    ? 'bg-cyan-600/20 text-cyan-300 border-cyan-600'
                    : 'bg-slate-950 text-slate-400 border-slate-800'
                }`}
              >
                CSV Raw Data
              </button>
            </div>
          </div>
        </div>

        <div className="mt-5 pt-4 border-t border-slate-800 flex justify-end">
          <Button
            variant="primary"
            size="sm"
            disabled
            disabledReason="Automated report generation will be activated in Phase 20"
          >
            Generate Report (Phase 20)
          </Button>
        </div>
      </Card>

      {/* Generated Reports Archive */}
      <Card
        title="Archived Reports"
        description="Historical generated reports stored on server"
      >
        {isStubEndpoint ? (
          <EmptyState
            title="No reports generated yet"
            description="Generated compliance reports will be indexed here for quick retrieval and download once the generation engine in Phase 20 is enabled."
            icon={
              <div className="w-12 h-12 rounded-xl bg-amber-950/60 border border-amber-800/60 flex items-center justify-center text-amber-400">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
                </svg>
              </div>
            }
          />
        ) : (
          <div className="p-4 text-xs text-slate-300">{JSON.stringify(apiResponse)}</div>
        )}
      </Card>
    </div>
  );
}
