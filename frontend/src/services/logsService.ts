import { apiFetch } from './api';

export interface LogEntry {
  id: string;
  organization_id: string;
  agent_id: string;
  device_id: string | null;
  source: string;
  event_type: string;
  severity: string;
  message: string;
  source_ip: string | null;
  username: string | null;
  timestamp: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface LogFilters {
  event_type?: string;
  source?: string;
  severity?: string;
  username?: string;
  source_ip?: string;
  device_id?: string;
  agent_id?: string;
  from_date?: string;
  to_date?: string;
  limit?: number;
  offset?: number;
}

export const logsService = {
  async listLogs(filters: LogFilters = {}): Promise<LogEntry[]> {
    const params = new URLSearchParams();
    if (filters.event_type && filters.event_type !== 'ALL') {
      params.append('event_type', filters.event_type);
    }
    if (filters.source && filters.source !== 'ALL') {
      params.append('source', filters.source);
    }
    if (filters.severity && filters.severity !== 'ALL') {
      params.append('severity', filters.severity);
    }
    if (filters.username) {
      params.append('username', filters.username);
    }
    if (filters.source_ip) {
      params.append('source_ip', filters.source_ip);
    }
    if (filters.device_id) {
      params.append('device_id', filters.device_id);
    }
    if (filters.agent_id) {
      params.append('agent_id', filters.agent_id);
    }
    if (filters.from_date) {
      params.append('from_date', filters.from_date);
    }
    if (filters.to_date) {
      params.append('to_date', filters.to_date);
    }
    if (filters.limit) {
      params.append('limit', String(filters.limit));
    }
    if (filters.offset) {
      params.append('offset', String(filters.offset));
    }

    const query = params.toString() ? `?${params.toString()}` : '';
    return apiFetch<LogEntry[]>(`/logs/${query}`);
  },

  async getLog(logId: string): Promise<LogEntry> {
    return apiFetch<LogEntry>(`/logs/${logId}`);
  },
};
