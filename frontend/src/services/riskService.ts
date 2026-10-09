import { apiFetch } from './api';

export interface VulnerabilityBreakdown {
  critical_count: number;
  critical_score: number;
  high_count: number;
  high_score: number;
  medium_count: number;
  medium_score: number;
  low_count: number;
  low_score: number;
  subtotal: number;
}

export interface AlertBreakdown {
  brute_force_count: number;
  brute_force_score: number;
  suspicious_login_count: number;
  suspicious_login_score: number;
  port_scan_count: number;
  port_scan_score: number;
  subtotal: number;
}

export interface ExposureBreakdown {
  open_ports_count: number;
  exposure_score: number;
}

export interface FactorBreakdown {
  vulnerabilities?: VulnerabilityBreakdown;
  alerts?: AlertBreakdown;
  exposure?: ExposureBreakdown;
  raw_total?: number;
  total_score?: number;
  risk_band?: string;
  formula_version?: string;
}

export interface DeviceRiskScore {
  id: string | null;
  device_id: string;
  device_ip: string | null;
  device_hostname: string | null;
  device_type: string | null;
  organization_id: string;
  score: number;
  risk_band: 'Low' | 'Medium' | 'High' | 'Critical';
  factor_breakdown: FactorBreakdown;
  formula_version: string;
  created_at: string | null;
  updated_at: string | null;
}

export const riskService = {
  async getRiskScores(params?: {
    risk_band?: string;
    limit?: number;
    offset?: number;
  }): Promise<DeviceRiskScore[]> {
    const query = new URLSearchParams();
    if (params?.risk_band && params.risk_band !== 'all') {
      query.append('risk_band', params.risk_band);
    }
    if (params?.limit) {
      query.append('limit', String(params.limit));
    }
    if (params?.offset) {
      query.append('offset', String(params.offset));
    }
    const qStr = query.toString() ? `?${query.toString()}` : '';
    return apiFetch<DeviceRiskScore[]>(`/risk-scores/${qStr}`);
  },

  async getDeviceRisk(deviceId: string): Promise<DeviceRiskScore> {
    return apiFetch<DeviceRiskScore>(`/devices/${deviceId}/risk`);
  },
};
