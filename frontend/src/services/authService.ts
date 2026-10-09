import { apiFetch, setStoredToken, setStoredUser, removeStoredToken } from './api';

export interface UserInToken {
  id: string;
  organization_id: string;
  role_id: string;
  email: string;
  username: string | null;
  role?: string;
  organization_name?: string;
  is_active: boolean;
  last_login_at?: string | null;
}

export interface LoginResponse {
  user: UserInToken;
  token: string;
  token_type: string;
}

export interface MeResponse {
  id: string;
  organization_id: string;
  role_id: string;
  email: string;
  username: string | null;
  is_active: boolean;
  failed_login_count: number;
  last_login_at: string | null;
  created_at: string;
  updated_at: string;
}

export const authService = {
  async login(email: string, password: string): Promise<LoginResponse> {
    const data = await apiFetch<LoginResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });

    setStoredToken(data.token);
    setStoredUser(data.user);
    return data;
  },

  async logout(): Promise<void> {
    try {
      await apiFetch<void>('/auth/logout', {
        method: 'POST',
      });
    } catch {
      // Ignore network errors on logout
    } finally {
      removeStoredToken();
    }
  },

  async getMe(): Promise<MeResponse> {
    return apiFetch<MeResponse>('/auth/me', {
      method: 'GET',
    });
  },
};
