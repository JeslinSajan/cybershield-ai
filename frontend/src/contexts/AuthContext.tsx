import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authService, UserInToken } from '../services/authService';
import { getStoredToken, getStoredUser, removeStoredToken, setStoredUser } from '../services/api';

export type UserRole = 'Administrator' | 'Security Analyst' | 'Viewer';

export interface AuthUser extends UserInToken {
  role: UserRole;
}

interface AuthContextType {
  user: AuthUser | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  isAuthenticated: boolean;
  isAdmin: boolean;
  isAnalyst: boolean;
  isViewer: boolean;
  canScan: boolean;
  canManageUsers: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

function parseJwt(token: string): { sub?: string; role?: string; org?: string; exp?: number } | null {
  try {
    const base64Url = token.split('.')[1];
    if (!base64Url) return null;
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(getStoredToken());
  const [user, setUser] = useState<AuthUser | null>(() => {
    const storedUser = getStoredUser() as UserInToken | null;
    const storedToken = getStoredToken();
    if (!storedToken) return null;

    const payload = parseJwt(storedToken);
    if (!payload) return null;

    // Check expiration
    if (payload.exp && payload.exp * 1000 < Date.now()) {
      removeStoredToken();
      return null;
    }

    const role = (payload.role as UserRole) || 'Viewer';
    return {
      id: payload.sub || storedUser?.id || '',
      organization_id: payload.org || storedUser?.organization_id || '',
      role_id: storedUser?.role_id || '',
      email: storedUser?.email || '',
      username: storedUser?.username || storedUser?.email?.split('@')[0] || 'User',
      role,
      is_active: storedUser?.is_active ?? true,
      last_login_at: storedUser?.last_login_at || null,
    };
  });

  useEffect(() => {
    // If token exists, verify expiration
    if (token) {
      const payload = parseJwt(token);
      if (payload?.exp && payload.exp * 1000 < Date.now()) {
        logout();
      }
    }
  }, [token]);

  const login = async (email: string, password: string): Promise<void> => {
    const response = await authService.login(email, password);
    setToken(response.token);

    const payload = parseJwt(response.token);
    const role = (payload?.role as UserRole) || 'Administrator';

    const fullUser: AuthUser = {
      ...response.user,
      role,
      username: response.user.username || response.user.email.split('@')[0],
    };

    setUser(fullUser);
    setStoredUser(fullUser);
  };

  const logout = async (): Promise<void> => {
    await authService.logout();
    setToken(null);
    setUser(null);
  };

  const role = user?.role;
  const isAdmin = role === 'Administrator';
  const isAnalyst = role === 'Security Analyst';
  const isViewer = role === 'Viewer';
  const canScan = isAdmin || isAnalyst;
  const canManageUsers = isAdmin;

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        login,
        logout,
        isAuthenticated: !!token && !!user,
        isAdmin,
        isAnalyst,
        isViewer,
        canScan,
        canManageUsers,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
