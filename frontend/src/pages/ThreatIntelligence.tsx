import { useState, useEffect } from 'react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { EmptyState } from '../components/ui/EmptyState';
import { apiFetch } from '../services/api';

export function ThreatIntelligence() {
  const [apiResponse, setApiResponse] = useState<any>(null);
  const [indicatorTypeFilter, setIndicatorTypeFilter] = useState<string>('ALL');

  useEffect(() => {
    const fetchIndicators = async () => {
      try {
        const res = await apiFetch<any>('/threat-intelligence/');
        setApiResponse(res);
      } catch (err: any) {
        setApiResponse({ error: err?.message || 'Endpoint returned error' });
      }
    };
    fetchIndicators();
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
            <h2 className="text-xl font-bold text-slate-100 tracking-tight">Threat Intelligence & Indicators of Compromise</h2>
            <span className="text-[10px] px-2 py-0.5 rounded bg-amber-950/70 text-amber-300 border border-amber-800 font-mono">
              Phase 18 Implementation Target
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Local threat feed repository, malicious IP / domain / file hash indicators, and automated IOC log correlation.
          </p>
        </div>
        <Button
          variant="primary"
          size="sm"
          disabled
          disabledReason="IOC indicator creation will be activated with Phase 18 backend deployment"
        >
          + Add Threat Indicator (Phase 18)
        </Button>
      </div>

      {/* Honest Status Notice */}
      <div className="p-4 bg-slate-900 border border-amber-800/40 rounded-xl space-y-2 text-xs">
        <div className="flex items-center gap-2 text-amber-300 font-semibold">
          <svg className="w-4 h-4 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Backend Integration Status: Scheduled for Phase 18
        </div>
        <p className="text-slate-300 leading-relaxed">
          The threat intelligence ingestion engine (<code className="text-cyan-300 font-mono">ThreatIndicator</code> schema,
          threat seed dataset, and automatic matching of source IPs against known malicious IOCs) is scheduled for implementation in <strong>Phase 18</strong>.
        </p>
        <p className="text-slate-400 font-mono text-[11px]">
          Current API Response: {JSON.stringify(apiResponse)}
        </p>
      </div>

      {/* Filter Bar (Visual Layout Prepared for Phase 18) */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 font-medium">Indicator Type:</span>
          <select
            value={indicatorTypeFilter}
            onChange={(e) => setIndicatorTypeFilter(e.target.value)}
            className="bg-slate-900 border border-slate-800 text-xs rounded-lg px-3 py-1.5 text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
          >
            <option value="ALL">All Types</option>
            <option value="ip">IP Addresses (Malicious C2 / Proxies)</option>
            <option value="domain">Domains (Phishing / Malicious)</option>
            <option value="hash">File Hashes (SHA-256)</option>
          </select>
        </div>
      </div>

      {/* Main View */}
      <Card>
        {isStubEndpoint ? (
          <EmptyState
            title="Threat Intelligence Pipeline Under Construction (Phase 18)"
            description="When Phase 18 is deployed, you will be able to manage threat indicators (IPs, domains, hashes) and automatically alert whenever ingested agent logs contain matching malicious entities."
            icon={
              <div className="w-12 h-12 rounded-xl bg-amber-950/60 border border-amber-800/60 flex items-center justify-center text-amber-400">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                </svg>
              </div>
            }
          />
        ) : (
          <div className="p-4 text-xs text-slate-300">
            {JSON.stringify(apiResponse)}
          </div>
        )}
      </Card>
    </div>
  );
}
