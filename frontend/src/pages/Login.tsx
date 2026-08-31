import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

export function Login() {
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: Get form values and call login API
    // For now, mock login
    login('admin', 'password');
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-navy text-slate-300 font-sans flex items-center justify-center antialiased p-4 relative overflow-hidden">
      {/* Subtle background decoration */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden -z-10 pointer-events-none">
        <div className="absolute -top-[20%] -left-[10%] w-[50%] h-[50%] bg-cyan-900/10 blur-[120px] rounded-full"></div>
        <div className="absolute top-[80%] -right-[10%] w-[40%] h-[40%] bg-blue-900/10 blur-[120px] rounded-full"></div>
      </div>

      {/* Auth Card Container */}
      <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-xl shadow-2xl relative overflow-hidden">
        {/* Top accent line */}
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-cyan-600 to-blue-800"></div>
        
        <div className="p-8">
          {/* Branding */}
          <div className="flex flex-col items-center justify-center mb-8">
            <div className="w-12 h-12 bg-slate-950 border border-slate-800 rounded-lg flex items-center justify-center mb-4 shadow-inner">
              <svg className="w-7 h-7 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <h1 className="text-xl font-bold text-slate-100 tracking-wide">CYBERSHIELD AI</h1>
            <p className="text-sm text-slate-500 mt-1">
              {authMode === 'login' ? 'Authenticate to continue' : 'Request platform access'}
            </p>
          </div>

          {/* LOGIN FORM */}
          {authMode === 'login' && (
            <form onSubmit={handleLogin} className="space-y-5">
              <div>
                <label className="block text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">Username or Email</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <svg className="h-5 w-5 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                  </div>
                  <input 
                    type="text" 
                    placeholder="analyst@domain.com" 
                    className="block w-full bg-slate-950 border border-slate-700 text-slate-200 rounded-md pl-10 pr-3 py-2.5 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-colors text-sm" 
                    required 
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">Password</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <svg className="h-5 w-5 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                    </svg>
                  </div>
                  <input 
                    type="password" 
                    placeholder="••••••••••••" 
                    className="block w-full bg-slate-950 border border-slate-700 text-slate-200 rounded-md pl-10 pr-3 py-2.5 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-colors text-sm" 
                    required 
                  />
                </div>
              </div>

              <div className="pt-2">
                <button 
                  type="submit" 
                  className="w-full flex justify-center py-2.5 px-4 border border-transparent rounded-md shadow-sm text-sm font-bold text-white bg-cyan-600 hover:bg-cyan-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-cyan-500 focus:ring-offset-slate-900 transition-colors"
                >
                  SECURE LOGIN
                </button>
              </div>

              <div className="flex items-center justify-between pt-4 border-t border-slate-800 text-sm">
                <a href="#" className="font-medium text-slate-500 hover:text-cyan-400 transition-colors">Forgot Password?</a>
                <button 
                  type="button"
                  onClick={() => setAuthMode('register')}
                  className="font-medium text-cyan-500 hover:text-cyan-400 transition-colors flex items-center gap-1"
                >
                  Request Access 
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </button>
              </div>
            </form>
          )}

          {/* REGISTER / REQUEST ACCESS FORM */}
          {authMode === 'register' && (
            <form className="space-y-5">
              <div>
                <label className="block text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">Full Name</label>
                <input 
                  type="text" 
                  placeholder="e.g. John Doe" 
                  className="block w-full bg-slate-950 border border-slate-700 text-slate-200 rounded-md px-3 py-2.5 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-colors text-sm" 
                  required 
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">Work Email</label>
                <input 
                  type="email" 
                  placeholder="analyst@domain.com" 
                  className="block w-full bg-slate-950 border border-slate-700 text-slate-200 rounded-md px-3 py-2.5 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-colors text-sm" 
                  required 
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">Role Requested</label>
                <select className="block w-full bg-slate-950 border border-slate-700 text-slate-200 rounded-md px-3 py-2.5 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-colors text-sm appearance-none">
                  <option>Security Analyst</option>
                  <option>Read-Only Viewer</option>
                  <option>Administrator</option>
                </select>
              </div>

              <div className="pt-2">
                <button 
                  type="submit" 
                  className="w-full flex justify-center py-2.5 px-4 border border-transparent rounded-md shadow-sm text-sm font-bold text-slate-900 bg-slate-200 hover:bg-white focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-200 focus:ring-offset-slate-900 transition-colors"
                >
                  SUBMIT REQUEST
                </button>
                <p className="text-[11px] text-slate-500 text-center mt-3">Access requests must be approved by a system administrator before login is enabled.</p>
              </div>

              <div className="flex items-center justify-center pt-4 border-t border-slate-800 text-sm">
                <button 
                  type="button"
                  onClick={() => setAuthMode('login')}
                  className="font-medium text-slate-400 hover:text-cyan-400 transition-colors flex items-center gap-1"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                  Back to Login
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
