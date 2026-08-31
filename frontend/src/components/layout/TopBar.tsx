import { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

interface HealthResponse {
  status: string;
}

export function TopBar() {
  const [healthStatus, setHealthStatus] = useState<string>('Checking...');
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/v1/health`);
        const data: HealthResponse = await response.json();
        setHealthStatus(data.status === 'healthy' ? 'Connected' : 'Error');
      } catch (error) {
        setHealthStatus('Disconnected');
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="h-16 bg-soc-panel border-b border-soc-panelLight flex items-center justify-between px-6">
      <div className="flex items-center space-x-4">
        <div className="relative">
          <input
            type="text"
            placeholder="Search..."
            className="bg-soc-panelLight border border-soc-panelLight rounded-md px-4 py-2 text-sm text-gray-300 placeholder-gray-500 focus:outline-none focus:border-soc-accent w-64"
          />
        </div>
      </div>

      <div className="flex items-center space-x-4">
        {/* Backend Health Status */}
        <div className="flex items-center space-x-2">
          <div className={`w-2 h-2 rounded-full ${healthStatus === 'Connected' ? 'bg-soc-success' : 'bg-soc-danger'}`} />
          <span className="text-xs text-gray-400">
            Backend: {healthStatus}
          </span>
        </div>

        {/* Notifications */}
        <button className="relative p-2 text-gray-400 hover:text-white transition-colors">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
          <span className="absolute top-1 right-1 w-2 h-2 bg-soc-danger rounded-full"></span>
        </button>

        {/* User Profile */}
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-soc-accent rounded-full flex items-center justify-center">
            <span className="text-sm font-semibold text-white">{user?.username?.[0]?.toUpperCase() || 'A'}</span>
          </div>
          <span className="text-sm text-gray-300">{user?.username || 'Admin'}</span>
          <button 
            onClick={handleLogout}
            className="ml-2 text-gray-400 hover:text-white transition-colors"
            title="Logout"
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
