// Demo data matching API contract schemas
// All data is clearly labeled as DEMO/DEVELOPMENT data

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

// Demo data generators
export const demoAgents: Agent[] = [
  {
    id: '1',
    organization_id: 'org-1',
    name: 'warehouse-host-01',
    hostname: 'warehouse-host-01',
    status: 'ONLINE',
    version: '1.0.0',
    last_heartbeat_at: '2026-08-30T12:30:00Z',
    is_active: true,
    created_at: '2026-08-24T10:00:00Z'
  },
  {
    id: '2',
    organization_id: 'org-1',
    name: 'office-server-01',
    hostname: 'office-server-01',
    status: 'ONLINE',
    version: '1.0.0',
    last_heartbeat_at: '2026-08-30T12:28:00Z',
    is_active: true,
    created_at: '2026-08-24T10:05:00Z'
  },
  {
    id: '3',
    organization_id: 'org-1',
    name: 'dev-workstation-01',
    hostname: 'dev-workstation-01',
    status: 'OFFLINE',
    version: '1.0.0',
    last_heartbeat_at: '2026-08-30T10:15:00Z',
    is_active: true,
    created_at: '2026-08-24T10:10:00Z'
  }
];

export const demoDevices: Device[] = [
  {
    id: '1',
    organization_id: 'org-1',
    agent_id: '1',
    ip_address: '192.168.1.10',
    mac_address: 'AA:BB:CC:DD:EE:10',
    hostname: 'workstation-1',
    vendor: 'Dell',
    device_type: 'workstation',
    status: 'online',
    last_seen_at: '2026-08-30T12:30:00Z',
    created_at: '2026-08-24T11:00:00Z'
  },
  {
    id: '2',
    organization_id: 'org-1',
    agent_id: '1',
    ip_address: '192.168.1.11',
    mac_address: 'AA:BB:CC:DD:EE:11',
    hostname: 'workstation-2',
    vendor: 'HP',
    device_type: 'workstation',
    status: 'online',
    last_seen_at: '2026-08-30T12:30:00Z',
    created_at: '2026-08-24T11:05:00Z'
  },
  {
    id: '3',
    organization_id: 'org-1',
    agent_id: '2',
    ip_address: '192.168.1.20',
    mac_address: 'AA:BB:CC:DD:EE:20',
    hostname: 'server-1',
    vendor: 'Dell',
    device_type: 'server',
    status: 'online',
    last_seen_at: '2026-08-30T12:28:00Z',
    created_at: '2026-08-24T11:10:00Z'
  }
];

export const demoVulnerabilities: Vulnerability[] = [
  {
    id: '1',
    organization_id: 'org-1',
    device_id: '3',
    severity: 'Critical',
    score: 9.8,
    description: 'CVE-2023-38408: OpenSSH pre-authentication buffer overflow',
    recommendation: 'Upgrade to OpenSSH 9.3 or later',
    status: 'open',
    created_at: '2026-08-30T10:00:00Z'
  },
  {
    id: '2',
    organization_id: 'org-1',
    device_id: '1',
    severity: 'High',
    score: 7.5,
    description: 'CVE-2023-23397: Microsoft Outlook privilege escalation',
    recommendation: 'Apply Microsoft security update',
    status: 'open',
    created_at: '2026-08-30T09:30:00Z'
  },
  {
    id: '3',
    organization_id: 'org-1',
    device_id: '2',
    severity: 'Medium',
    score: 5.2,
    description: 'CVE-2023-22518: Confluence authentication bypass',
    recommendation: 'Upgrade to Confluence 8.3.3 or later',
    status: 'open',
    created_at: '2026-08-30T08:45:00Z'
  },
  {
    id: '4',
    organization_id: 'org-1',
    device_id: '3',
    severity: 'Low',
    score: 3.1,
    description: 'CVE-2023-38409: Apache HTTP Server information disclosure',
    recommendation: 'Upgrade to Apache 2.4.57 or later',
    status: 'open',
    created_at: '2026-08-30T08:00:00Z'
  }
];

export const demoAlerts: Alert[] = [
  {
    id: '1',
    organization_id: 'org-1',
    agent_id: '1',
    device_id: '1',
    alert_type: 'brute_force',
    severity: 'High',
    status: 'Open',
    description: '6 failed SSH logins from 192.168.1.50 within 10 minutes',
    risk_score: 74.5,
    triggered_at: '2026-08-30T12:10:00Z',
    created_at: '2026-08-30T12:10:00Z'
  },
  {
    id: '2',
    organization_id: 'org-1',
    agent_id: '1',
    device_id: '2',
    alert_type: 'port_scan',
    severity: 'Medium',
    status: 'Open',
    description: 'Port scan detected from 192.168.1.51 targeting 15 distinct ports',
    risk_score: 52.3,
    triggered_at: '2026-08-30T11:45:00Z',
    created_at: '2026-08-30T11:45:00Z'
  },
  {
    id: '3',
    organization_id: 'org-1',
    agent_id: '2',
    device_id: '3',
    alert_type: 'suspicious_login',
    severity: 'Low',
    status: 'Acknowledged',
    description: 'SSH login from unusual location (192.168.1.100) at 02:30 UTC',
    risk_score: 35.2,
    triggered_at: '2026-08-30T02:30:00Z',
    created_at: '2026-08-30T02:30:00Z'
  }
];

export const demoDashboardSummary: DashboardSummary = {
  online_agents: 2,
  online_devices: 3,
  critical_vulnerabilities: 1,
  open_alerts: 2,
  average_risk_score: 54.0
};

export const demoAlertTrend: AlertTrend[] = [
  { date: '2026-08-24', count: 3 },
  { date: '2026-08-25', count: 5 },
  { date: '2026-08-26', count: 2 },
  { date: '2026-08-27', count: 4 },
  { date: '2026-08-28', count: 6 },
  { date: '2026-08-29', count: 3 },
  { date: '2026-08-30', count: 2 }
];

export const demoVulnerabilityDistribution: VulnerabilityDistribution = {
  Low: 1,
  Medium: 1,
  High: 1,
  Critical: 1
};

export const demoRiskTrend: RiskTrend[] = [
  { date: '2026-08-24', score: 42.0 },
  { date: '2026-08-25', score: 48.5 },
  { date: '2026-08-26', score: 45.0 },
  { date: '2026-08-27', score: 52.3 },
  { date: '2026-08-28', score: 58.7 },
  { date: '2026-08-29', score: 51.2 },
  { date: '2026-08-30', score: 54.0 }
];

export const demoActivities: Activity[] = [
  {
    event_type: 'device_discovered',
    message: 'New device 192.168.1.20 discovered by agent office-server-01',
    timestamp: '2026-08-30T12:28:00Z'
  },
  {
    event_type: 'alert_generated',
    message: 'High-severity brute-force alert triggered on workstation-1',
    timestamp: '2026-08-30T12:10:00Z'
  },
  {
    event_type: 'vulnerability_found',
    message: 'Critical CVE-2023-38408 detected on server-1',
    timestamp: '2026-08-30T10:00:00Z'
  },
  {
    event_type: 'agent_heartbeat',
    message: 'Agent warehouse-host-01 heartbeat received',
    timestamp: '2026-08-30T12:30:00Z'
  },
  {
    event_type: 'scan_completed',
    message: 'Discovery scan completed on 192.168.1.0/24',
    timestamp: '2026-08-30T11:00:00Z'
  }
];
