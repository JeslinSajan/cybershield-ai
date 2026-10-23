import { apiFetch } from './api';
import { Agent } from './agentsService';
import { Device } from './devicesService';
import { Vulnerability } from './vulnerabilitiesService';
import { Scan } from './scansService';
import { LogEntry } from './logsService';

export interface DashboardSummary {
  agents_online: number;
  agents_total: number;
  devices_online: number;
  devices_total: number;
  critical_vulns: number;
  high_vulns: number;
  medium_vulns: number;
  low_vulns: number;
  scans_in_progress: number;
  scans_total: number;
}

export interface DashboardResponse {
  summary: DashboardSummary;
  agents: Agent[];
  devices: Device[];
  vulnerabilities: Vulnerability[];
  scans: Scan[];
  recent_logs: LogEntry[];
}

export const dashboardService = {
  async getDashboard(): Promise<DashboardResponse> {
    return apiFetch<DashboardResponse>('/dashboard/');
  },
};
