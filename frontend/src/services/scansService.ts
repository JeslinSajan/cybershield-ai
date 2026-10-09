import { apiFetch } from './api';

export interface Scan {
  id: string;
  organization_id: string;
  agent_id: string | null;
  created_by_user_id: string;
  scan_type: 'discovery' | 'vulnerability' | 'health_check' | string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | string;
  target_scope: string;
  started_at: string | null;
  completed_at: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface CreateScanPayload {
  agent_id: string;
  scan_type: 'discovery' | 'vulnerability' | 'health_check';
  target_scope: string;
}

export const scansService = {
  async listScans(statusFilter?: string): Promise<Scan[]> {
    const params = new URLSearchParams();
    if (statusFilter && statusFilter !== 'ALL') {
      params.append('status', statusFilter);
    }
    const query = params.toString() ? `?${params.toString()}` : '';
    return apiFetch<Scan[]>(`/scans/${query}`);
  },

  async getScan(scanId: string): Promise<Scan> {
    return apiFetch<Scan>(`/scans/${scanId}`);
  },

  async createScan(payload: CreateScanPayload): Promise<{ id: string; status: string }> {
    return apiFetch<{ id: string; status: string }>('/scans/', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
};
