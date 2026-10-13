import { useState, useEffect, useCallback, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { useAuth } from '../contexts/AuthContext';
import { aiService, ChatMessage } from '../services/aiService';
import { alertsService, Alert } from '../services/alertsService';
import { vulnerabilitiesService, Vulnerability } from '../services/vulnerabilitiesService';
import { devicesService, Device } from '../services/devicesService';
import { ApiError } from '../services/api';

export function AIAssistant() {
  const { isViewer } = useAuth();
  const [searchParams] = useSearchParams();
  const queryTab = searchParams.get('tab') as 'alert' | 'vulnerability' | 'risk' | null;
  const queryId = searchParams.get('id');

  // Mode: 'alert' | 'vulnerability' | 'risk'
  const [activeTab, setActiveTab] = useState<'alert' | 'vulnerability' | 'risk'>(
    queryTab && ['alert', 'vulnerability', 'risk'].includes(queryTab) ? queryTab : 'alert'
  );

  // Context entity lists
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [vulns, setVulns] = useState<Vulnerability[]>([]);
  const [devices, setDevices] = useState<Device[]>([]);

  // Selected entities
  const [selectedAlertId, setSelectedAlertId] = useState<string>(
    queryTab === 'alert' && queryId ? queryId : ''
  );
  const [selectedVulnId, setSelectedVulnId] = useState<string>(
    queryTab === 'vulnerability' && queryId ? queryId : ''
  );
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>(
    queryTab === 'risk' && queryId ? queryId : ''
  );

  // Auto explanation triggered ref
  const autoExplainedRef = useRef<boolean>(false);

  // Investigation & Chat state
  const [explanation, setExplanation] = useState<string | null>(null);
  const [isLoadingExplanation, setIsLoadingExplanation] = useState<boolean>(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [userPrompt, setUserPrompt] = useState<string>('');
  const [isSendingPrompt, setIsSendingPrompt] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Initial data load
  useEffect(() => {
    if (isViewer) return;

    const loadEntities = async () => {
      try {
        const [alertData, vulnData, deviceData] = await Promise.all([
          alertsService.listAlerts({ limit: 20 }),
          vulnerabilitiesService.listVulnerabilities({ limit: 20 }),
          devicesService.listDevices(),
        ]);
        setAlerts(alertData);
        if (!queryId || queryTab !== 'alert') {
          if (alertData.length > 0) setSelectedAlertId(alertData[0].id);
        }

        setVulns(vulnData);
        if (!queryId || queryTab !== 'vulnerability') {
          if (vulnData.length > 0) setSelectedVulnId(vulnData[0].id);
        }

        setDevices(deviceData);
        if (!queryId || queryTab !== 'risk') {
          if (deviceData.length > 0) setSelectedDeviceId(deviceData[0].id);
        }
      } catch (err) {
        console.warn('Failed loading entities for AI assistant:', err);
      }
    };

    loadEntities();
  }, [isViewer, queryId, queryTab]);

  // Generate explanation
  const handleGenerateExplanation = useCallback(async () => {
    setErrorMessage(null);
    setIsLoadingExplanation(true);
    setExplanation(null);
    setMessages([]);

    try {
      if (activeTab === 'alert' && selectedAlertId) {
        const res = await aiService.explainAlert(selectedAlertId);
        setExplanation(res.explanation);
      } else if (activeTab === 'vulnerability' && selectedVulnId) {
        const res = await aiService.explainVulnerability(selectedVulnId);
        setExplanation(res.explanation);
      } else if (activeTab === 'risk' && selectedDeviceId) {
        const res = await aiService.explainRisk(selectedDeviceId);
        setExplanation(res.explanation);
      } else {
        setErrorMessage('Please select a target entity to analyze.');
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage('Failed to generate AI explanation.');
      }
    } finally {
      setIsLoadingExplanation(false);
    }
  }, [activeTab, selectedAlertId, selectedVulnId, selectedDeviceId]);

  // Deep-link auto-explanation trigger
  useEffect(() => {
    if (queryId && !autoExplainedRef.current) {
      if (
        (queryTab === 'alert' && selectedAlertId === queryId) ||
        (queryTab === 'vulnerability' && selectedVulnId === queryId) ||
        (queryTab === 'risk' && selectedDeviceId === queryId)
      ) {
        autoExplainedRef.current = true;
        handleGenerateExplanation();
      }
    }
  }, [queryId, queryTab, selectedAlertId, selectedVulnId, selectedDeviceId, handleGenerateExplanation]);

  // Handle follow-up chat
  const handleSendPrompt = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!userPrompt.trim()) return;

    const targetId =
      activeTab === 'alert'
        ? selectedAlertId
        : activeTab === 'vulnerability'
        ? selectedVulnId
        : selectedDeviceId;

    if (!targetId) {
      setErrorMessage('Please select an entity first.');
      return;
    }

    const currentText = userPrompt.trim();
    setUserPrompt('');
    setIsSendingPrompt(true);

    const tempUserMsg: ChatMessage = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: currentText,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    try {
      const res = await aiService.chat(currentText, activeTab, targetId);
      const assistantMsg: ChatMessage = {
        id: `resp-${Date.now()}`,
        role: 'assistant',
        content: res.response,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage('Failed to send inquiry to AI explanation engine.');
      }
    } finally {
      setIsSendingPrompt(false);
    }
  };

  // Viewer Access Denied Banner
  if (isViewer) {
    return (
      <div className="p-6 space-y-6">
        <div className="pb-2 border-b border-slate-800">
          <h2 className="text-xl font-bold text-slate-100">Local Security Explanation Engine</h2>
          <p className="text-xs text-slate-400 mt-0.5">Automated SOC triage, CVE analysis, and device risk explanation.</p>
        </div>
        <Card>
          <div className="py-16 px-4 text-center space-y-3">
            <div className="w-12 h-12 mx-auto rounded-xl bg-amber-950/60 border border-amber-800/80 flex items-center justify-center text-amber-400">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <h3 className="text-base font-semibold text-slate-200">Access Restricted — Read-Only Viewer Role</h3>
            <p className="text-xs text-slate-400 max-w-md mx-auto">
              Per Security Specification FR-2.1 and RBAC policies, the AI Security Assistant is reserved for
              <strong> Administrators</strong> and <strong> Security Analysts</strong>.
            </p>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-slate-100 tracking-tight">AI Security Assistant</h2>
            <span className="text-[10px] px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800 font-mono">
              Local Rule Engine
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Deterministic security explanation engine running 100% locally and offline without external AI APIs or cloud leakage.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs text-slate-400 font-mono">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span>Local Engine Active (v1.0)</span>
        </div>
      </div>

      {/* Mode Selector Tabs */}
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-800/80 pb-2">
        <button
          type="button"
          onClick={() => {
            setActiveTab('alert');
            setExplanation(null);
            setMessages([]);
          }}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-2 ${
            activeTab === 'alert'
              ? 'bg-cyan-950 text-cyan-300 border border-cyan-800 shadow-sm'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900 border border-transparent'
          }`}
        >
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
          Alert Triage Analysis
        </button>

        <button
          type="button"
          onClick={() => {
            setActiveTab('vulnerability');
            setExplanation(null);
            setMessages([]);
          }}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-2 ${
            activeTab === 'vulnerability'
              ? 'bg-cyan-950 text-cyan-300 border border-cyan-800 shadow-sm'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900 border border-transparent'
          }`}
        >
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          CVE Vulnerability Breakdown
        </button>

        <button
          type="button"
          onClick={() => {
            setActiveTab('risk');
            setExplanation(null);
            setMessages([]);
          }}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-2 ${
            activeTab === 'risk'
              ? 'bg-cyan-950 text-cyan-300 border border-cyan-800 shadow-sm'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900 border border-transparent'
          }`}
        >
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          Device Risk Scoring Evaluation
        </button>
      </div>

      {/* Target Selector Card */}
      <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex-1">
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              Select Investigation Target
            </label>

            {activeTab === 'alert' && (
              <select
                value={selectedAlertId}
                onChange={(e) => setSelectedAlertId(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
              >
                {alerts.length === 0 ? (
                  <option value="">No alerts available</option>
                ) : (
                  alerts.map((a) => (
                    <option key={a.id} value={a.id}>
                      [{a.severity}] {a.alert_type.toUpperCase()} — {a.description.substring(0, 75)}... (Status: {a.status})
                    </option>
                  ))
                )}
              </select>
            )}

            {activeTab === 'vulnerability' && (
              <select
                value={selectedVulnId}
                onChange={(e) => setSelectedVulnId(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
              >
                {vulns.length === 0 ? (
                  <option value="">No vulnerabilities available</option>
                ) : (
                  vulns.map((v) => (
                    <option key={v.id} value={v.id}>
                      [{v.severity}] {v.cve_details?.cve_id || v.cve_code || 'CVE'} — {v.description.substring(0, 75)}...
                    </option>
                  ))
                )}
              </select>
            )}

            {activeTab === 'risk' && (
              <select
                value={selectedDeviceId}
                onChange={(e) => setSelectedDeviceId(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
              >
                {devices.length === 0 ? (
                  <option value="">No devices available</option>
                ) : (
                  devices.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.ip_address} ({d.hostname || 'No hostname'}) — Status: {d.status}
                    </option>
                  ))
                )}
              </select>
            )}
          </div>

          <div className="sm:self-end">
            <Button
              variant="primary"
              size="md"
              isLoading={isLoadingExplanation}
              onClick={handleGenerateExplanation}
              className="w-full sm:w-auto font-bold text-xs"
            >
              Analyze with AI
            </Button>
          </div>
        </div>
      </div>

      {/* Error Alert */}
      {errorMessage && (
        <div className="p-3 bg-rose-950/70 border border-rose-800/80 rounded-lg text-rose-300 text-xs flex items-center gap-2">
          <svg className="w-4 h-4 text-rose-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Main Analysis Output & Conversation Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Structured Analysis Brief */}
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <div className="p-5 space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-cyan-400" />
                  Investigation Report
                </h3>
                <span className="text-[10px] text-slate-500 font-mono">
                  Engine: LocalRuleAI
                </span>
              </div>

              {isLoadingExplanation ? (
                <div className="py-16 flex flex-col items-center justify-center text-slate-400 gap-3">
                  <div className="w-7 h-7 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
                  <span className="text-xs">Evaluating telemetry and synthesizing response...</span>
                </div>
              ) : explanation ? (
                <div className="prose prose-invert max-w-none text-xs text-slate-300 whitespace-pre-wrap leading-relaxed font-sans">
                  {explanation}
                </div>
              ) : (
                <div className="py-16 text-center text-slate-500 space-y-2">
                  <div className="w-10 h-10 mx-auto rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-center text-slate-600">
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                  </div>
                  <p className="text-xs font-medium text-slate-400">Ready for Analysis</p>
                  <p className="text-[11px] text-slate-500 max-w-sm mx-auto">
                    Select an alert, CVE vulnerability, or device risk factor above and click "Analyze with AI" to generate a complete SOC explanation.
                  </p>
                </div>
              )}
            </div>
          </Card>
        </div>

        {/* Right 1 Col: Follow-up Inquiry Chat Thread */}
        <div className="space-y-4">
          <Card>
            <div className="p-4 flex flex-col h-[520px]">
              <div className="pb-3 border-b border-slate-800 flex items-center justify-between">
                <h4 className="text-xs font-bold text-slate-200">Interactive Inquiry</h4>
                <span className="text-[10px] text-cyan-400 font-mono">SOC Assistant</span>
              </div>

              {/* Chat Messages Log */}
              <div className="flex-1 overflow-y-auto py-3 space-y-3 pr-1 text-xs">
                {messages.length === 0 ? (
                  <div className="h-full flex items-center justify-center text-center text-slate-500 p-4">
                    <p className="text-[11px]">
                      Ask questions regarding triage steps, mitigation priorities, or related security standards.
                    </p>
                  </div>
                ) : (
                  messages.map((m) => (
                    <div
                      key={m.id}
                      className={`p-3 rounded-lg text-xs ${
                        m.role === 'user'
                          ? 'bg-cyan-950/60 border border-cyan-800/60 text-cyan-200 ml-4'
                          : 'bg-slate-950 border border-slate-800 text-slate-300 mr-2 whitespace-pre-wrap leading-relaxed'
                      }`}
                    >
                      <div className="flex items-center justify-between text-[10px] text-slate-500 mb-1 font-mono">
                        <span>{m.role === 'user' ? 'Analyst' : 'CyberShield Engine'}</span>
                      </div>
                      <p>{m.content}</p>
                    </div>
                  ))
                )}
                {isSendingPrompt && (
                  <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-400 flex items-center gap-2">
                    <span className="w-3 h-3 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
                    <span>Evaluating rules...</span>
                  </div>
                )}
              </div>

              {/* Prompt Input Form */}
              <form onSubmit={handleSendPrompt} className="pt-3 border-t border-slate-800 flex items-center gap-2">
                <input
                  type="text"
                  placeholder="Ask follow-up question..."
                  value={userPrompt}
                  onChange={(e) => setUserPrompt(e.target.value)}
                  disabled={isSendingPrompt}
                  className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
                />
                <Button
                  type="submit"
                  variant="primary"
                  size="sm"
                  isLoading={isSendingPrompt}
                  disabled={!userPrompt.trim()}
                >
                  Send
                </Button>
              </form>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
