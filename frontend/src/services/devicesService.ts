import { apiFetch } from './api';

export interface Device {
  id: string;
  organization_id: string;
  agent_id: string | null;
  ip_address: string;
  mac_address: string | null;
  hostname: string | null;
  vendor: string | null;
  device_type: string | null;
  status: 'online' | 'offline' | 'unknown' | string;
  last_seen_at: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface DeviceVulnerability {
  id: string;
  organization_id: string;
  device_id: string;
  scan_id: string | null;
  cve_id: string | null;
  cve_code: string | null;
  severity: 'Critical' | 'High' | 'Medium' | 'Low' | string;
  score: number | null;
  description: string;
  summary?: string;
  recommendation: string | null;
  status: 'open' | 'resolved' | string;
  created_at: string | null;
  updated_at: string | null;
}

export const devicesService = {
  async listDevices(statusFilter?: string): Promise<Device[]> {
    const params = new URLSearchParams();
    if (statusFilter && statusFilter !== 'ALL') {
      params.append('status', statusFilter);
    }
    const query = params.toString() ? `?${params.toString()}` : '';
    return apiFetch<Device[]>(`/devices/${query}`);
  },

  async getDevice(deviceId: string): Promise<Device> {
    return apiFetch<Device>(`/devices/${deviceId}`);
  },

  async getDeviceVulnerabilities(deviceId: string): Promise<DeviceVulnerability[]> {
    return apiFetch<DeviceVulnerability[]>(`/devices/${deviceId}/vulnerabilities`);
  },
};
