import { useState, useEffect, useCallback } from 'react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Table } from '../components/ui/Table';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { EmptyState } from '../components/ui/EmptyState';
import { reportsService, ReportItem } from '../services/reportsService';
import { useAuth } from '../contexts/AuthContext';
import { ApiError } from '../services/api';

export function Reports() {
  const { canScan, isViewer } = useAuth(); // canScan = Admin or Analyst
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Generation form state
  const [reportType, setReportType] = useState<'security_overview' | 'vulnerability' | 'alert'>('security_overview');
  const [timeframePreset, setTimeframePreset] = useState<string>('30d');
  const [customStartDate, setCustomStartDate] = useState<string>('');
  const [customEndDate, setCustomEndDate] = useState<string>('');
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [generationSuccess, setGenerationSuccess] = useState<string | null>(null);
  const [generationError, setGenerationError] = useState<string | null>(null);

  // Download state
  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const [filterType, setFilterType] = useState<string>('all');

  const fetchReports = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await reportsService.listReports({
        type: filterType !== 'all' ? filterType : undefined,
      });
      setReports(data);
    } catch (err: any) {
      setError(err?.message || 'Failed to retrieve reports list.');
    } finally {
      setIsLoading(false);
    }
  }, [filterType]);

  useEffect(() => {
    fetchReports();
  }, [fetchReports]);

  const calculateDates = (): { from_date: string; to_date: string } => {
    const end = new Date();
    if (timeframePreset === 'custom' && customStartDate && customEndDate) {
      return {
        from_date: new Date(customStartDate).toISOString(),
        to_date: new Date(customEndDate).toISOString(),
      };
    }

    const start = new Date();
    if (timeframePreset === '7d') {
      start.setDate(end.getDate() - 7);
    } else if (timeframePreset === '90d') {
      start.setDate(end.getDate() - 90);
    } else {
      // Default 30d
      start.setDate(end.getDate() - 30);
    }

    return {
      from_date: start.toISOString(),
      to_date: end.toISOString(),
    };
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canScan) return;

    setIsGenerating(true);
    setGenerationError(null);
    setGenerationSuccess(null);

    try {
      const { from_date, to_date } = calculateDates();
      const newReport = await reportsService.generateReport({
        type: reportType,
        from_date,
        to_date,
      });
      setGenerationSuccess(`Report generated successfully! (ID: ${newReport.id.slice(0, 8)}...)`);
      fetchReports();
    } catch (err: any) {
      if (err instanceof ApiError) {
        setGenerationError(err.message);
      } else {
        setGenerationError(err?.message || 'Failed generating report.');
      }
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDownload = async (reportId: string, format: 'pdf' | 'csv', type: string) => {
    if (isViewer) return;

    setDownloadingId(`${reportId}-${format}`);
    try {
      const filename = `cybershield_${type}_${reportId.slice(0, 8)}.${format}`;
      await reportsService.downloadReport(reportId, format, filename);
    } catch (err: any) {
      alert(err?.message || `Failed to download ${format.toUpperCase()} report.`);
    } finally {
      setDownloadingId(null);
    }
  };

  const formatReportTypeName = (type: string) => {
    switch (type) {
      case 'security_overview':
        return 'Executive Security Overview';
      case 'vulnerability':
        return 'Vulnerability & CVE Assessment';
      case 'alert':
        return 'Incident & Alert Audit Trail';
      default:
        return type.replace('_', ' ');
    }
  };

  const tableHeaders = ['Report Type', 'Assessment Window', 'Format / Status', 'Generated At', 'Export Actions'];
  const tableRows = reports.map((r) => [
    <div key="type">
      <span className="font-semibold text-slate-200 block text-xs">
        {formatReportTypeName(r.report_type)}
      </span>
      <span className="text-[10px] text-cyan-400 font-mono">
        ID: {r.id.slice(0, 8)}...
      </span>
    </div>,
    <div key="window" className="text-xs text-slate-300 font-mono">
      <span>{new Date(r.period_start).toLocaleDateString()}</span>
      <span className="text-slate-500 mx-1.5">&rarr;</span>
      <span>{new Date(r.period_end).toLocaleDateString()}</span>
    </div>,
    <div key="status" className="flex items-center gap-1.5">
      <Badge variant="active">{r.status}</Badge>
      <span className="text-[10px] text-slate-400 font-mono uppercase">
        {r.mime_type ? r.mime_type.split('/')[1] : 'PDF'}
      </span>
    </div>,
    <span key="date" className="text-xs text-slate-400 font-mono">
      {new Date(r.created_at).toLocaleString()}
    </span>,
    <div key="actions" className="flex items-center gap-2">
      <Button
        variant="outline"
        size="sm"
        className="text-xs text-cyan-400 border-cyan-800/80 hover:bg-cyan-950/40 py-1 px-2.5"
        disabled={isViewer || downloadingId === `${r.id}-pdf`}
        isLoading={downloadingId === `${r.id}-pdf`}
        onClick={() => handleDownload(r.id, 'pdf', r.report_type)}
      >
        <span className="flex items-center gap-1">
          <svg className="w-3.5 h-3.5 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          PDF
        </span>
      </Button>
      <Button
        variant="secondary"
        size="sm"
        className="text-xs py-1 px-2.5"
        disabled={isViewer || downloadingId === `${r.id}-csv`}
        isLoading={downloadingId === `${r.id}-csv`}
        onClick={() => handleDownload(r.id, 'csv', r.report_type)}
      >
        <span className="flex items-center gap-1">
          <svg className="w-3.5 h-3.5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          CSV
        </span>
      </Button>
    </div>,
  ]);

  return (
    <div className="p-6 space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-slate-100 tracking-tight">Compliance & Executive Reporting</h2>
            <span className="text-[10px] px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800 font-mono">
              Phase 20 Complete
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Generate and export automated PDF and CSV security summary reports for stakeholders, compliance audits, and incident reviews.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span>Report Engine Active (fpdf2)</span>
        </div>
      </div>

      {/* Report Generation Parameter Card */}
      <Card
        title="Generate Security Report"
        description="Select report scope, timeframe window, and generate export documents"
      >
        <form onSubmit={handleGenerate} className="space-y-4">
          {generationSuccess && (
            <div className="p-3 bg-emerald-950/60 border border-emerald-800 text-emerald-300 rounded-lg text-xs flex items-center justify-between">
              <span>{generationSuccess}</span>
              <button
                type="button"
                onClick={() => setGenerationSuccess(null)}
                className="text-emerald-400 hover:text-emerald-200"
              >
                &times;
              </button>
            </div>
          )}

          {generationError && (
            <div className="p-3 bg-rose-950/60 border border-rose-800 text-rose-300 rounded-lg text-xs flex items-center justify-between">
              <span>{generationError}</span>
              <button
                type="button"
                onClick={() => setGenerationError(null)}
                className="text-rose-400 hover:text-rose-200"
              >
                &times;
              </button>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">Report Scope & Subject</label>
              <select
                value={reportType}
                onChange={(e) => setReportType(e.target.value as any)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
              >
                <option value="security_overview">Executive Security Overview (Fleet & Posture)</option>
                <option value="vulnerability">Vulnerability & CVE Technical Assessment</option>
                <option value="alert">Security Incident & Alert Audit Trail</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">Assessment Window Preset</label>
              <select
                value={timeframePreset}
                onChange={(e) => setTimeframePreset(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
              >
                <option value="7d">Last 7 Days (Weekly Audit)</option>
                <option value="30d">Last 30 Days (Monthly Compliance)</option>
                <option value="90d">Last 90 Days (Quarterly Assessment)</option>
                <option value="custom">Custom Date Range</option>
              </select>
            </div>
          </div>

          {timeframePreset === 'custom' && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 p-3 bg-slate-950/60 border border-slate-800 rounded-lg">
              <div>
                <label className="block text-[11px] font-semibold text-slate-400 mb-1">Start Date</label>
                <input
                  type="date"
                  value={customStartDate}
                  onChange={(e) => setCustomStartDate(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
                  required={timeframePreset === 'custom'}
                />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-slate-400 mb-1">End Date</label>
                <input
                  type="date"
                  value={customEndDate}
                  onChange={(e) => setCustomEndDate(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
                  required={timeframePreset === 'custom'}
                />
              </div>
            </div>
          )}

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2 border-t border-slate-800/80">
            <span className="text-[11px] text-slate-500">
              {isViewer ? (
                <span className="text-amber-400">Notice: Read-only Viewer role cannot generate or download reports.</span>
              ) : (
                'Generated reports are saved and immediately available in PDF and CSV format.'
              )}
            </span>

            <Button
              type="submit"
              variant="primary"
              size="sm"
              disabled={!canScan || isGenerating}
              isLoading={isGenerating}
            >
              Generate Report
            </Button>
          </div>
        </form>
      </Card>

      {/* Generated Reports Table */}
      <div className="space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-slate-200">Historical Report Archive</h3>
            <span className="text-xs text-slate-500">({reports.length} reports)</span>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400">Filter:</span>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1 text-xs text-slate-300 focus:outline-none focus:border-cyan-500"
            >
              <option value="all">All Types</option>
              <option value="security_overview">Security Overview</option>
              <option value="vulnerability">Vulnerability</option>
              <option value="alert">Alerts</option>
            </select>
          </div>
        </div>

        {error && (
          <div className="p-3 bg-rose-950/60 border border-rose-800 text-rose-300 rounded-lg text-xs">
            {error}
          </div>
        )}

        {isLoading ? (
          <div className="py-12 flex justify-center">
            <LoadingSpinner size="lg" message="Retrieving generated report archives..." />
          </div>
        ) : reports.length === 0 ? (
          <EmptyState
            title="No reports generated yet"
            description="Use the parameters form above to generate your first compliance or executive summary report."
          />
        ) : (
          <Card>
            <Table headers={tableHeaders} rows={tableRows} />
          </Card>
        )}
      </div>
    </div>
  );
}
