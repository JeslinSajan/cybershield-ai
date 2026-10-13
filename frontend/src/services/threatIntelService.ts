import { apiFetch } from './api';

export interface ThreatIndicator {
  id: string;
  organization_id: string;
  indicator_type: 'ip' | 'domain' | 'hash';
  value: string;
  description: string | null;
  source: string;
  created_at: string;
  updated_at: string;
}

export interface CreateThreatIndicatorInput {
  indicator_type: 'ip' | 'domain' | 'hash';
  value: string;
  description?: string;
  source?: string;
}

export const threatIntelService = {
  list: async (params?: { indicator_type?: string; search?: string; limit?: number; offset?: number }): Promise<ThreatIndicator[]> => {
    const query = new URLSearchParams();
    if (params?.indicator_type && params.indicator_type !== 'ALL') {
      query.append('indicator_type', params.indicator_type);
    }
    if (params?.search) {
      query.append('search', params.search);
    }
    if (params?.limit) {
      query.append('limit', String(params.limit));
    }
    if (params?.offset) {
      query.append('offset', String(params.offset));
    }
    const qStr = query.toString();
    return apiFetch<ThreatIndicator[]>(`/threat-intelligence/${qStr ? `?${qStr}` : ''}`);
  },

  getById: async (id: string): Promise<ThreatIndicator> => {
    return apiFetch<ThreatIndicator>(`/threat-intelligence/${id}`);
  },

  create: async (payload: CreateThreatIndicatorInput): Promise<ThreatIndicator> => {
    return apiFetch<ThreatIndicator>('/threat-intelligence/', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  delete: async (id: string): Promise<{ message: string; id: string }> => {
    return apiFetch<{ message: string; id: string }>(`/threat-intelligence/${id}`, {
      method: 'DELETE',
    });
  },
};
