import { apiFetch } from './api';

export interface AgentHeartbeat {
  id: string;
  timestamp: string;
  status: string;
  cpu_percent: number | null;
  memory_percent: number | null;
  details?: Record<string, unknown> | null;
}

export interface Agent {
  id: string;
  name: string;
  hostname: string;
  status: 'ONLINE' | 'OFFLINE' | 'PENDING' | string;
  version: string;
  is_active: boolean;
  last_heartbeat_at: string | null;
  created_at: string;
  updated_at?: string;
  recent_heartbeats?: AgentHeartbeat[];
}

export interface EnrollmentTokenResponse {
  token: string;
  expires_at: string;
}

export interface RevokeAgentResponse {
  id: string;
  is_active: boolean;
  revoked_at: string;
}

export interface AgentNetworkStat {
  id: string;
  timestamp: string;
  cpu_percent: number | null;
  memory_percent: number | null;
  details: Record<string, unknown> | null;
}

export const agentsService = {
  async listAgents(statusFilter?: string): Promise<Agent[]> {
    const params = new URLSearchParams();
    if (statusFilter && statusFilter !== 'ALL') {
      params.append('status', statusFilter);
    }
    const query = params.toString() ? `?${params.toString()}` : '';
    return apiFetch<Agent[]>(`/agents/${query}`);
  },

  async getAgent(agentId: string): Promise<Agent> {
    return apiFetch<Agent>(`/agents/${agentId}`);
  },

  async generateEnrollmentToken(
    agentName: string,
    expiresInMinutes: number = 60
  ): Promise<EnrollmentTokenResponse> {
    return apiFetch<EnrollmentTokenResponse>('/agents/enrollment-token', {
      method: 'POST',
      body: JSON.stringify({
        agent_name: agentName,
        expires_in_minutes: expiresInMinutes,
      }),
    });
  },

  async revokeAgent(agentId: string): Promise<RevokeAgentResponse> {
    return apiFetch<RevokeAgentResponse>(`/agents/${agentId}/revoke`, {
      method: 'POST',
    });
  },

  async getNetworkStats(agentId: string): Promise<AgentNetworkStat[]> {
    return apiFetch<AgentNetworkStat[]>(`/agents/${agentId}/network-stats`);
  },
};
