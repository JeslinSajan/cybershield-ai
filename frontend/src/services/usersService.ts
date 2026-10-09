import { apiFetch } from './api';

export interface UserItem {
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

export interface CreateUserData {
  organization_id: string;
  role_id: string;
  email: string;
  username?: string;
  password: string;
}

export interface UpdateUserData {
  email?: string;
  username?: string;
  role_id?: string;
  is_active?: boolean;
}

export const usersService = {
  async listUsers(): Promise<UserItem[]> {
    return apiFetch<UserItem[]>('/users/');
  },

  async getUser(userId: string): Promise<UserItem> {
    return apiFetch<UserItem>(`/users/${userId}`);
  },

  async createUser(data: CreateUserData): Promise<UserItem> {
    return apiFetch<UserItem>('/users/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async updateUser(userId: string, data: UpdateUserData): Promise<UserItem> {
    return apiFetch<UserItem>(`/users/${userId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },

  async deactivateUser(userId: string): Promise<{ id: string; is_active: boolean }> {
    return apiFetch<{ id: string; is_active: boolean }>(`/users/${userId}/deactivate`, {
      method: 'POST',
    });
  },
};
