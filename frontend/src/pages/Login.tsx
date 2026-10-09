import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { ApiError } from '../services/api';
import { Button } from '../components/ui/Button';

export function Login() {
  const [authMode, setAuthMode] = useState<'login' | 'info'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setIsLoading(true);

    try {
      await login(email.trim(), password);
      navigate('/');
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 423) {
          setErrorMessage('Account locked: 5 consecutive failed attempts. Please wait 10 minutes.');
        } else if (err.status === 401) {
          setErrorMessage('Invalid email or password.');
        } else {
          setErrorMessage(err.message || 'Authentication failed. Please verify credentials.');
        }
      } else {
        setErrorMessage('Unable to connect to the authentication service. Check server status.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-300 font-sans flex items-center justify-center antialiased p-4 relative overflow-hidden select-none">
      {/* Background ambient lighting */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden -z-10 pointer-events-none">
        <div className="absolute -top-[20%] -left-[10%] w-[50%] h-[50%] bg-cyan-950/30 blur-[130px] rounded-full" />
        <div className="absolute top-[80%] -right-[10%] w-[40%] h-[40%] bg-blue-950/30 blur-[130px] rounded-full" />
      </div>

      {/* Auth Card Container */}
      <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-xl shadow-2xl relative overflow-hidden">
        {/* Top accent line */}
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-cyan-500 via-blue-500 to-cyan-600" />

        <div className="p-8">
          {/* Branding */}
          <div className="flex flex-col items-center justify-center mb-6">
            <div className="w-12 h-12 bg-slate-950 border border-cyan-800/40 rounded-xl flex items-center justify-center mb-3 shadow-inner">
              <svg className="w-7 h-7 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <h1 className="text-xl font-bold text-slate-100 tracking-wider">CYBERSHIELD AI</h1>
            <p className="text-xs text-slate-400 mt-1">
              {authMode === 'login' ? 'Unified SOC Security Portal' : 'User Provisioning Policy'}
            </p>
          </div>

          {/* Error Banner */}
          {errorMessage && (
            <div className="mb-5 p-3 rounded-lg bg-rose-950/70 border border-rose-800/80 text-rose-300 text-xs flex items-start gap-2.5">
              <svg className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <span>{errorMessage}</span>
            </div>
          )}

          {/* LOGIN FORM */}
          {authMode === 'login' && (
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                  Email Address
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.206" />
                    </svg>
                  </div>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="analyst@domain.com"
                    className="block w-full bg-slate-950 border border-slate-700 text-slate-200 rounded-lg pl-9 pr-3 py-2.5 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-colors text-sm"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                  Password
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                    </svg>
                  </div>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="block w-full bg-slate-950 border border-slate-700 text-slate-200 rounded-lg pl-9 pr-10 py-2.5 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-colors text-sm"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-500 hover:text-slate-300"
                  >
                    {showPassword ? (
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l18 18" />
                      </svg>
                    ) : (
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                    )}
                  </button>
                </div>
              </div>

              <div className="pt-2">
                <Button
                  type="submit"
                  variant="primary"
                  size="md"
                  className="w-full font-bold"
                  isLoading={isLoading}
                >
                  AUTHENTICATE
                </Button>
              </div>

              <div className="flex items-center justify-between pt-4 border-t border-slate-800 text-xs">
                <span className="text-slate-500">Need credentials?</span>
                <button
                  type="button"
                  onClick={() => setAuthMode('info')}
                  className="font-semibold text-cyan-400 hover:text-cyan-300 transition-colors"
                >
                  Account Provisioning Info &rarr;
                </button>
              </div>
            </form>
          )}

          {/* ACCOUNT PROVISIONING INFO */}
          {authMode === 'info' && (
            <div className="space-y-4">
              <div className="p-3 bg-slate-950/60 border border-slate-800 rounded-lg text-xs space-y-2 text-slate-300">
                <p className="font-semibold text-cyan-400">Enterprise Access Control</p>
                <p>
                  Per Security Requirement FR-2.1, CyberShield AI does not support public self-registration.
                </p>
                <p>
                  All user accounts (Security Analysts, Viewers, Administrators) must be provisioned directly by a designated platform Administrator via the Users API.
                </p>
                <div className="pt-2 border-t border-slate-800 text-[11px] text-slate-400">
                  <span className="font-mono text-cyan-300">Default Admin:</span> Use the admin email and password configured during platform setup.
                </div>
              </div>

              <Button
                type="button"
                variant="secondary"
                size="md"
                className="w-full"
                onClick={() => setAuthMode('login')}
              >
                &larr; Back to Login
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
