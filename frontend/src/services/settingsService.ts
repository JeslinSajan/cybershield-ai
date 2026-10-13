/**
 * Settings and Audit Logs service for CyberShield AI.
 * Endpoints restricted to Administrator role.
 */

import { apiFetch } from './api';

export interface SystemSettingItem {
  id: string;
  organization_id: string;
  key: string;
  value: any;
  created_at: string;
  updated_at: string;
}

export interface AuditLogItem {
  id: string;
  organization_id: string;
  actor_type: string;
  actor_id?: string | null;
  action: string;
  target_type?: string | null;
  target_id?: string | null;
  details?: Record<string, any> | null;
  created_at: string;
}

export const settingsService = {
  /**
   * List system setting key-value pairs (Admin only).
   */
  async getSettings(): Promise<SystemSettingItem[]> {
    return apiFetch<SystemSettingItem[]>('/settings/');
  },

  /**
   * Update or create a system setting key (Admin only).
   */
  async setSetting(key: string, value: any): Promise<SystemSettingItem> {
    return apiFetch<SystemSettingItem>(`/settings/${encodeURIComponent(key)}`, {
      method: 'PUT',
      body: JSON.stringify({ value }),
    });
  },

  /**
   * List organizational audit log entries (Admin only).
   */
  async getAuditLogs(params?: { action?: string; actor_type?: string; limit?: number; offset?: number }): Promise<AuditLogItem[]> {
    const q = new URLSearchParams();
    if (params?.action) q.set('action', params.action);
    if (params?.actor_type) q.set('actor_type', params.actor_type);
    if (params?.limit) q.set('limit', params.limit.toString());
    if (params?.offset) q.set('offset', params.offset.toString());
    const queryStr = q.toString() ? `?${q.toString()}` : '';
    return apiFetch<AuditLogItem[]>(`/settings/audit-logs${queryStr}`);
  },
};
