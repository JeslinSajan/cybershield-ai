import { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { healthService } from '../../services/healthService';

export function TopBar() {
  const [appHealth, setAppHealth] = useState<'checking' | 'healthy' | 'error'>('checking');
  const [dbHealth, setDbHealth] = useState<'connected' | 'disconnected' | 'checking'>('checking');
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    let isMounted = true;

    const checkStatuses = async () => {
      try {
        const appRes = await healthService.checkHealth();
        if (isMounted) {
          setAppHealth(appRes.status === 'healthy' ? 'healthy' : 'error');
        }
      } catch {
        if (isMounted) setAppHealth('error');
      }

      try {
        const dbRes = await healthService.checkDatabaseHealth();
        if (isMounted) {
          setDbHealth(dbRes.database === 'connected' ? 'connected' : 'disconnected');
        }
      } catch {
        if (isMounted) setDbHealth('disconnected');
      }
    };

    checkStatuses();
    const interval = setInterval(checkStatuses, 30000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <header className="h-16 bg-slate-900 border-b border-slate-800 flex items-center justify-between px-6 z-10 select-none">
      {/* Search Input / Quick Filter */}
      <div className="flex items-center space-x-4">
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <input
            type="text"
            placeholder="Global search (IP, hostname, CVE, log event)..."
            className="bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-4 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 w-80 transition-colors"
          />
        </div>
      </div>

      {/* Right side items: Live Status, Profile, Logout */}
      <div className="flex items-center space-x-5">
        {/* Backend & DB Health Telemetry */}
        <div className="flex items-center space-x-3 bg-slate-950/60 border border-slate-800 rounded-lg px-3 py-1.5 text-xs">
          <div className="flex items-center space-x-1.5">
            <span
              className={`w-2 h-2 rounded-full ${
                appHealth === 'healthy'
                  ? 'bg-emerald-400 shadow-sm shadow-emerald-400/50'
                  : appHealth === 'checking'
                  ? 'bg-amber-400 animate-pulse'
                  : 'bg-rose-500'
              }`}
            />
            <span className="text-slate-400 font-mono text-[11px]">API: {appHealth}</span>
          </div>

          <span className="text-slate-700">|</span>

          <div className="flex items-center space-x-1.5">
            <span
              className={`w-2 h-2 rounded-full ${
                dbHealth === 'connected'
                  ? 'bg-emerald-400 shadow-sm shadow-emerald-400/50'
                  : dbHealth === 'checking'
                  ? 'bg-amber-400 animate-pulse'
                  : 'bg-rose-500'
              }`}
            />
            <span className="text-slate-400 font-mono text-[11px]">DB: {dbHealth}</span>
          </div>
        </div>

        {/* User Profile Badge & Logout */}
        <div className="flex items-center space-x-3 border-l border-slate-800 pl-4">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-600 to-blue-600 flex items-center justify-center font-bold text-white text-xs shadow-md shadow-cyan-950/40">
              {user?.username?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase() || 'U'}
            </div>
            <div className="text-left hidden sm:block">
              <p className="text-xs font-semibold text-slate-200 leading-tight">
                {user?.username || user?.email?.split('@')[0] || 'User'}
              </p>
              <p className="text-[10px] text-cyan-400/90 font-mono leading-tight">
                {user?.role || 'Viewer'}
              </p>
            </div>
          </div>

          <button
            onClick={handleLogout}
            title="Secure Sign Out"
            className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded-lg transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
          </button>
        </div>
      </div>
    </header>
  );
}
