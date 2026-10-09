import { apiFetch } from './api';

export interface AlertEvent {
  id: string;
  organization_id: string;
  alert_id: string;
  actor_user_id: string | null;
  from_status: string | null;
  to_status: string;
  reason: string | null;
  changed_at: string | null;
}

export interface Alert {
  id: string;
  organization_id: string;
  agent_id: string | null;
  device_id: string | null;
  alert_type: string;
  severity: 'Critical' | 'High' | 'Medium' | 'Low' | string;
  status: 'Open' | 'Acknowledged' | 'Investigating' | 'Resolved' | 'False Positive' | string;
  description: string;
  risk_score: number;
  triggered_at: string | null;
  created_at: string | null;
  updated_at: string | null;
  history?: AlertEvent[];
}

export interface AlertsSummary {
  open: number;
  acknowledged: number;
  investigating: number;
  resolved: number;
  false_positive: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
}

export interface AlertFilters {
  status?: string;
  severity?: string;
  alert_type?: string;
  limit?: number;
  offset?: number;
}

export const alertsService = {
  async getSummary(): Promise<AlertsSummary> {
    return apiFetch<AlertsSummary>('/alerts/summary');
  },

  async listAlerts(filters: AlertFilters = {}): Promise<Alert[]> {
    const params = new URLSearchParams();
    if (filters.status && filters.status !== 'ALL') {
      params.append('status', filters.status);
    }
    if (filters.severity && filters.severity !== 'ALL') {
      params.append('severity', filters.severity);
    }
    if (filters.alert_type && filters.alert_type !== 'ALL') {
      params.append('alert_type', filters.alert_type);
    }
    if (filters.limit) {
      params.append('limit', String(filters.limit));
    }
    if (filters.offset) {
      params.append('offset', String(filters.offset));
    }

    const query = params.toString() ? `?${params.toString()}` : '';
    return apiFetch<Alert[]>(`/alerts/${query}`);
  },

  async getAlert(alertId: string): Promise<Alert> {
    return apiFetch<Alert>(`/alerts/${alertId}`);
  },

  async getAlertHistory(alertId: string): Promise<AlertEvent[]> {
    return apiFetch<AlertEvent[]>(`/alerts/${alertId}/history`);
  },

  async updateAlertStatus(
    alertId: string,
    status: string,
    reason?: string
  ): Promise<{ id: string; status: string; from_status: string; reason?: string }> {
    return apiFetch(`/alerts/${alertId}`, {
      method: 'PATCH',
      body: JSON.stringify({ status, reason }),
    });
  },
};
