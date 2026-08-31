import { createContext, useContext, useState, ReactNode } from 'react';

interface User {
  id: string;
  username: string;
  role: 'Administrator' | 'Security Analyst' | 'Viewer';
}

interface AuthContextType {
  user: User | null;
  login: (username: string, password: string) => void;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);

  const login = (username: string, _password: string) => {
    // TODO: Replace with real API call in Phase 7
    // For now, mock login
    setUser({
      id: '1',
      username,
      role: 'Administrator'
    });
  };

  const logout = () => {
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
