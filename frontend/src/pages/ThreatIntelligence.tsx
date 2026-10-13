import React, { useState, useEffect, useCallback } from 'react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { EmptyState } from '../components/ui/EmptyState';
import { useAuth } from '../contexts/AuthContext';
import { threatIntelService, ThreatIndicator } from '../services/threatIntelService';
import { ApiError } from '../services/api';

export function ThreatIntelligence() {
  const { isAdmin, isAnalyst } = useAuth();
  const canManage = isAdmin || isAnalyst;

  const [indicators, setIndicators] = useState<ThreatIndicator[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Filters
  const [typeFilter, setTypeFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Add Indicator Modal State
  const [isAddModalOpen, setIsAddModalOpen] = useState<boolean>(false);
  const [newType, setNewType] = useState<'ip' | 'domain' | 'hash'>('ip');
  const [newValue, setNewValue] = useState<string>('');
  const [newDescription, setNewDescription] = useState<string>('');
  const [newSource, setNewSource] = useState<string>('local_analyst');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Delete State
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState<boolean>(false);

  // Copy Feedback
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const fetchIndicators = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const data = await threatIntelService.list({
        indicator_type: typeFilter !== 'ALL' ? typeFilter : undefined,
        search: searchQuery.trim() || undefined,
      });
      setIndicators(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage('Failed to load threat intelligence indicators.');
      }
    } finally {
      setIsLoading(false);
    }
  }, [typeFilter, searchQuery]);

  useEffect(() => {
    fetchIndicators();
  }, [fetchIndicators]);

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleAddSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    if (!newValue.trim()) {
      setFormError('Indicator value is required.');
      return;
    }

    setIsSubmitting(true);
    try {
      await threatIntelService.create({
        indicator_type: newType,
        value: newValue.trim(),
        description: newDescription.trim() || undefined,
        source: newSource.trim() || 'local',
      });
      setIsAddModalOpen(false);
      setNewValue('');
      setNewDescription('');
      setNewSource('local_analyst');
      await fetchIndicators();
    } catch (err) {
      if (err instanceof ApiError) {
        setFormError(err.message);
      } else {
        setFormError('Failed to create threat indicator.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (indicator: ThreatIndicator) => {
    if (!isAdmin) return;
    setIsDeleting(true);
    try {
      await threatIntelService.delete(indicator.id);
      setDeletingId(null);
      await fetchIndicators();
    } catch (err) {
      if (err instanceof ApiError) {
        alert(err.message);
      } else {
        alert('Failed to delete indicator.');
      }
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-slate-100 tracking-tight">Threat Intelligence & IOC Management</h2>
            <span className="text-[10px] px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800 font-mono">
              Live Feed
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Maintain Indicators of Compromise (IPs, domains, hashes) automatically correlated against ingested agent telemetry.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => fetchIndicators()}
            isLoading={isLoading}
          >
            Refresh
          </Button>
          <Button
            variant="primary"
            size="sm"
            disabled={!canManage}
            disabledReason="Only Administrators and Security Analysts can add IOC indicators"
            onClick={() => {
              setFormError(null);
              setIsAddModalOpen(true);
            }}
          >
            + Add Indicator
          </Button>
        </div>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
          <span className="text-xs text-slate-400 font-medium">Total Indicators</span>
          <p className="text-2xl font-bold text-slate-100 mt-1">{indicators.length}</p>
        </div>
        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
          <span className="text-xs text-slate-400 font-medium">Malicious IPs</span>
          <p className="text-2xl font-bold text-cyan-400 mt-1">
            {indicators.filter((i) => i.indicator_type === 'ip').length}
          </p>
        </div>
        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
          <span className="text-xs text-slate-400 font-medium">Malicious Domains</span>
          <p className="text-2xl font-bold text-purple-400 mt-1">
            {indicators.filter((i) => i.indicator_type === 'domain').length}
          </p>
        </div>
        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
          <span className="text-xs text-slate-400 font-medium">File Hashes (SHA-256)</span>
          <p className="text-2xl font-bold text-amber-400 mt-1">
            {indicators.filter((i) => i.indicator_type === 'hash').length}
          </p>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 bg-slate-900/60 border border-slate-800 rounded-xl">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 font-medium">Type:</span>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="bg-slate-950 border border-slate-800 text-xs rounded-lg px-3 py-1.5 text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
            >
              <option value="ALL">All Types</option>
              <option value="ip">IP Addresses (ip)</option>
              <option value="domain">Domains (domain)</option>
              <option value="hash">File Hashes (hash)</option>
            </select>
          </div>
        </div>

        <div className="relative w-full sm:w-72">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <input
            type="text"
            placeholder="Search indicator value or notes..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 text-xs rounded-lg pl-9 pr-3 py-1.5 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
          />
        </div>
      </div>

      {/* Error Banner */}
      {errorMessage && (
        <div className="p-3 bg-rose-950/70 border border-rose-800/80 rounded-lg text-rose-300 text-xs flex items-center gap-2">
          <svg className="w-4 h-4 text-rose-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Indicators Table */}
      <Card>
        {isLoading ? (
          <div className="py-12 flex flex-col items-center justify-center text-slate-400 gap-3">
            <div className="w-6 h-6 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
            <span className="text-xs">Loading threat intelligence indicators...</span>
          </div>
        ) : indicators.length === 0 ? (
          <EmptyState
            title="No Threat Indicators Found"
            description={
              searchQuery || typeFilter !== 'ALL'
                ? 'No IOCs matched your search and filter criteria.'
                : 'No threat indicators are registered yet. Add indicators to automatically detect malicious activity.'
            }
            action={
              canManage ? (
                <Button variant="primary" size="sm" onClick={() => setIsAddModalOpen(true)}>
                  + Add First Indicator
                </Button>
              ) : undefined
            }
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300 border-collapse">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-950/40 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                  <th className="py-3 px-4">Type</th>
                  <th className="py-3 px-4">Indicator Value</th>
                  <th className="py-3 px-4">Description / Context</th>
                  <th className="py-3 px-4">Source</th>
                  <th className="py-3 px-4">Date Added</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-sans">
                {indicators.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 px-4 whitespace-nowrap">
                      {item.indicator_type === 'ip' && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono bg-cyan-950 text-cyan-300 border border-cyan-800">
                          IP
                        </span>
                      )}
                      {item.indicator_type === 'domain' && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono bg-purple-950 text-purple-300 border border-purple-800">
                          DOMAIN
                        </span>
                      )}
                      {item.indicator_type === 'hash' && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono bg-amber-950 text-amber-300 border border-amber-800">
                          HASH
                        </span>
                      )}
                    </td>

                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-cyan-400 font-medium select-all">
                          {item.value}
                        </span>
                        <button
                          type="button"
                          onClick={() => handleCopy(item.id, item.value)}
                          className="text-slate-500 hover:text-slate-300 transition-colors"
                          title="Copy value"
                        >
                          {copiedId === item.id ? (
                            <span className="text-[10px] text-emerald-400 font-mono">Copied!</span>
                          ) : (
                            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                            </svg>
                          )}
                        </button>
                      </div>
                    </td>

                    <td className="py-3 px-4 max-w-xs text-slate-300 truncate" title={item.description || ''}>
                      {item.description || <span className="text-slate-600 italic">No notes</span>}
                    </td>

                    <td className="py-3 px-4 whitespace-nowrap">
                      <span className="text-[11px] text-slate-400 font-mono">
                        {item.source}
                      </span>
                    </td>

                    <td className="py-3 px-4 whitespace-nowrap text-slate-500 font-mono text-[11px]">
                      {new Date(item.created_at).toLocaleDateString()}
                    </td>

                    <td className="py-3 px-4 whitespace-nowrap text-right">
                      {isAdmin ? (
                        <Button
                          variant="danger"
                          size="sm"
                          className="text-[11px] px-2 py-0.5"
                          onClick={() => setDeletingId(item.id)}
                        >
                          Delete
                        </Button>
                      ) : (
                        <span className="text-[11px] text-slate-600 italic">Admin only</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Add Indicator Modal */}
      {isAddModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-lg bg-slate-900 border border-slate-800 rounded-xl shadow-2xl overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-100">Add Threat Indicator (IOC)</h3>
              <button
                type="button"
                onClick={() => setIsAddModalOpen(false)}
                className="text-slate-500 hover:text-slate-300"
              >
                &times;
              </button>
            </div>

            <form onSubmit={handleAddSubmit} className="p-6 space-y-4">
              {formError && (
                <div className="p-3 bg-rose-950/70 border border-rose-800 rounded-lg text-rose-300 text-xs">
                  {formError}
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                  Indicator Type
                </label>
                <select
                  value={newType}
                  onChange={(e) => setNewType(e.target.value as any)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
                >
                  <option value="ip">IP Address (e.g. Malicious C2, scanner, brute-force IP)</option>
                  <option value="domain">Domain Name (e.g. Phishing host, malware delivery URL)</option>
                  <option value="hash">File Hash (e.g. SHA-256 malware signature)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                  Indicator Value
                </label>
                <input
                  type="text"
                  required
                  placeholder={
                    newType === 'ip'
                      ? '198.51.100.23'
                      : newType === 'domain'
                      ? 'c2-controller-vault.org'
                      : 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
                  }
                  value={newValue}
                  onChange={(e) => setNewValue(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 font-mono focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                  Description / Context
                </label>
                <textarea
                  rows={2}
                  placeholder="Cobalt strike beacon host observed in phishing campaign"
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                  Threat Feed / Source
                </label>
                <input
                  type="text"
                  placeholder="local_analyst, AlienVault_OTX, CISA_Advisory"
                  value={newSource}
                  onChange={(e) => setNewSource(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 font-mono focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="pt-4 flex items-center justify-end gap-3 border-t border-slate-800">
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={() => setIsAddModalOpen(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  size="sm"
                  isLoading={isSubmitting}
                >
                  Save Indicator
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deletingId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-sm bg-slate-900 border border-rose-900/60 rounded-xl shadow-2xl p-6 space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-rose-950/80 border border-rose-800/80 flex items-center justify-center text-rose-400">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </div>
              <div>
                <h4 className="text-sm font-bold text-slate-100">Delete Threat Indicator?</h4>
                <p className="text-xs text-slate-400">This action will be logged in the system audit trail.</p>
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setDeletingId(null)}
                disabled={isDeleting}
              >
                Cancel
              </Button>
              <Button
                variant="danger"
                size="sm"
                isLoading={isDeleting}
                onClick={() => {
                  const item = indicators.find((i) => i.id === deletingId);
                  if (item) handleDelete(item);
                }}
              >
                Confirm Delete
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
