import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { healthService } from '../../services/healthService';
import { notificationsService, NotificationItem } from '../../services/notificationsService';

export function TopBar() {
  const [appHealth, setAppHealth] = useState<'checking' | 'healthy' | 'error'>('checking');
  const [dbHealth, setDbHealth] = useState<'connected' | 'disconnected' | 'checking'>('checking');
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  // Notifications State
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [isNotifOpen, setIsNotifOpen] = useState<boolean>(false);
  const notifDropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let isMounted = true;

    // Combined health check: single endpoint /health/db verifies both app and database
    const checkStatuses = async () => {
      try {
        const dbRes = await healthService.checkDatabaseHealth();
        if (isMounted) {
          setAppHealth(dbRes.status === 'healthy' ? 'healthy' : 'error');
          setDbHealth(dbRes.database === 'connected' ? 'connected' : 'disconnected');
        }
      } catch {
        if (isMounted) {
          setAppHealth('error');
          setDbHealth('disconnected');
        }
      }
    };

    // Fast unread count: returns a single integer without fetching full list payload
    const fetchUnreadCount = async () => {
      try {
        const count = await notificationsService.getUnreadCount();
        if (isMounted) {
          setUnreadCount(count);
        }
      } catch {
        // silent fallback
      }
    };

    checkStatuses();
    fetchUnreadCount();

    const interval = setInterval(() => {
      checkStatuses();
      fetchUnreadCount();
    }, 45000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  // Fetch full notification list lazily only when dropdown is opened
  useEffect(() => {
    if (!isNotifOpen) return;
    let isMounted = true;
    notificationsService
      .listNotifications({ limit: 10 })
      .then((list) => {
        if (isMounted) setNotifications(list);
      })
      .catch(() => {});
    return () => {
      isMounted = false;
    };
  }, [isNotifOpen]);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (notifDropdownRef.current && !notifDropdownRef.current.contains(e.target as Node)) {
        setIsNotifOpen(false);
      }
    };
    if (isNotifOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isNotifOpen]);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const handleMarkAllRead = async () => {
    try {
      await notificationsService.markAllRead();
      setUnreadCount(0);
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } catch {
      // ignore
    }
  };

  const handleNotificationClick = async (notif: NotificationItem) => {
    if (!notif.is_read) {
      try {
        await notificationsService.markRead(notif.id);
        setUnreadCount((c) => Math.max(0, c - 1));
        setNotifications((prev) =>
          prev.map((n) => (n.id === notif.id ? { ...n, is_read: true } : n))
        );
      } catch {
        // ignore
      }
    }
    setIsNotifOpen(false);
    if (notif.alert_id) {
      navigate('/alerts');
    }
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

      {/* Right side items: Telemetry, Notifications Bell, Profile, Logout */}
      <div className="flex items-center space-x-4">
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

        {/* Notifications Bell Dropdown */}
        <div className="relative" ref={notifDropdownRef}>
          <button
            type="button"
            onClick={() => setIsNotifOpen((prev) => !prev)}
            className="relative p-2 rounded-lg bg-slate-950/60 border border-slate-800 text-slate-300 hover:text-cyan-400 hover:border-slate-700 transition-colors"
            title="Incident Notifications"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
            {unreadCount > 0 && (
              <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-rose-500 text-white font-bold text-[9px] flex items-center justify-center animate-pulse">
                {unreadCount > 9 ? '9+' : unreadCount}
              </span>
            )}
          </button>

          {/* Floating Dropdown */}
          {isNotifOpen && (
            <div className="absolute right-0 mt-2 w-80 bg-slate-900 border border-slate-800 rounded-xl shadow-2xl z-50 overflow-hidden">
              <div className="p-3 border-b border-slate-800/80 flex items-center justify-between bg-slate-950/80">
                <span className="text-xs font-semibold text-slate-200">Incident Notifications</span>
                {unreadCount > 0 && (
                  <button
                    type="button"
                    onClick={handleMarkAllRead}
                    className="text-[10px] text-cyan-400 hover:text-cyan-300 font-mono"
                  >
                    Mark all read
                  </button>
                )}
              </div>

              <div className="max-h-80 overflow-y-auto divide-y divide-slate-800/60">
                {notifications.length === 0 ? (
                  <div className="p-6 text-center text-xs text-slate-500">
                    No active notifications
                  </div>
                ) : (
                  notifications.map((n) => (
                    <div
                      key={n.id}
                      onClick={() => handleNotificationClick(n)}
                      className={`p-3 cursor-pointer transition-colors hover:bg-slate-800/60 ${
                        !n.is_read ? 'bg-cyan-950/20' : 'bg-transparent'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <span className={`text-xs font-semibold ${!n.is_read ? 'text-cyan-300' : 'text-slate-300'}`}>
                          {n.title}
                        </span>
                        {!n.is_read && (
                          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 mt-1 flex-shrink-0" />
                        )}
                      </div>
                      <p className="text-[11px] text-slate-400 mt-0.5 line-clamp-2">
                        {n.body}
                      </p>
                      <span className="text-[9px] text-slate-500 font-mono mt-1 block">
                        {new Date(n.created_at).toLocaleString()}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
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
