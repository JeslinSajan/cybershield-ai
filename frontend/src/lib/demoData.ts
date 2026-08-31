// Data types matching API contract schemas
// These will be populated by real API calls in Phase 7+

export interface Agent {
  id: string;
  organization_id: string;
  name: string;
  hostname: string;
  status: 'PENDING' | 'ONLINE' | 'OFFLINE';
  version: string;
  last_heartbeat_at: string;
  is_active: boolean;
  created_at: string;
}

export interface Device {
  id: string;
  organization_id: string;
  agent_id: string;
  ip_address: string;
  mac_address: string;
  hostname: string;
  vendor: string;
  device_type: string;
  status: 'online' | 'offline' | 'unknown';
  last_seen_at: string;
  created_at: string;
}

export interface Vulnerability {
  id: string;
  organization_id: string;
  device_id: string;
  severity: 'Low' | 'Medium' | 'High' | 'Critical';
  score: number;
  description: string;
  recommendation: string;
  status: string;
  created_at: string;
}

export interface Alert {
  id: string;
  organization_id: string;
  agent_id: string;
  device_id: string;
  alert_type: 'brute_force' | 'port_scan' | 'suspicious_login' | 'malware_indicator';
  severity: 'Low' | 'Medium' | 'High' | 'Critical';
  status: 'Open' | 'Acknowledged' | 'Investigating' | 'Resolved' | 'False Positive';
  description: string;
  risk_score: number;
  triggered_at: string;
  created_at: string;
}

export interface DashboardSummary {
  online_agents: number;
  online_devices: number;
  critical_vulnerabilities: number;
  open_alerts: number;
  average_risk_score: number;
}

export interface AlertTrend {
  date: string;
  count: number;
}

export interface VulnerabilityDistribution {
  Low: number;
  Medium: number;
  High: number;
  Critical: number;
}

export interface RiskTrend {
  date: string;
  score: number;
}

export interface Activity {
  event_type: string;
  message: string;
  timestamp: string;
}

// Empty data arrays - will be populated by real API calls
export const agents: Agent[] = [];
export const devices: Device[] = [];
export const vulnerabilities: Vulnerability[] = [];
export const alerts: Alert[] = [];
export const dashboardSummary: DashboardSummary = {
  online_agents: 0,
  online_devices: 0,
  critical_vulnerabilities: 0,
  open_alerts: 0,
  average_risk_score: 0
};
export const alertTrend: AlertTrend[] = [];
export const vulnerabilityDistribution: VulnerabilityDistribution = {
  Low: 0,
  Medium: 0,
  High: 0,
  Critical: 0
};
export const riskTrend: RiskTrend[] = [];
export const activities: Activity[] = [];
