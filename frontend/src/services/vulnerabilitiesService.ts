import { apiFetch } from './api';

export interface CVEDetails {
  cve_id: string;
  severity: string;
  cvss_score: number | null;
  affected_service: string | null;
  affected_version: string | null;
  summary: string | null;
  recommendation: string | null;
  source: string | null;
}

export interface Vulnerability {
  id: string;
  organization_id: string;
  device_id: string;
  scan_id: string | null;
  cve_id: string | null;
  cve_code: string | null;
  severity: 'Critical' | 'High' | 'Medium' | 'Low' | string;
  score: number | null;
  description: string;
  recommendation: string | null;
  status: 'open' | 'resolved' | string;
  created_at: string | null;
  updated_at: string | null;
  cve_details?: CVEDetails | null;
}

export interface VulnerabilityFilters {
  severity?: string;
  status?: string;
  device_id?: string;
  limit?: number;
  offset?: number;
}

export const vulnerabilitiesService = {
  async listVulnerabilities(filters: VulnerabilityFilters = {}): Promise<Vulnerability[]> {
    const params = new URLSearchParams();
    if (filters.severity && filters.severity !== 'ALL') {
      params.append('severity', filters.severity);
    }
    if (filters.status && filters.status !== 'ALL') {
      params.append('status', filters.status);
    }
    if (filters.device_id) {
      params.append('device_id', filters.device_id);
    }
    if (filters.limit) {
      params.append('limit', String(filters.limit));
    }
    if (filters.offset) {
      params.append('offset', String(filters.offset));
    }

    const query = params.toString() ? `?${params.toString()}` : '';
    return apiFetch<Vulnerability[]>(`/vulnerabilities/${query}`);
  },

  async getVulnerability(vulnId: string): Promise<Vulnerability> {
    return apiFetch<Vulnerability>(`/vulnerabilities/${vulnId}`);
  },
};
