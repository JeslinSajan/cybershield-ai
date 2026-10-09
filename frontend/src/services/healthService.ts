import { apiFetch } from './api';

export interface HealthResponse {
  status: string;
}

export interface DatabaseHealthResponse {
  status: string;
  database: string;
  message?: string;
}

export const healthService = {
  async checkHealth(): Promise<HealthResponse> {
    return apiFetch<HealthResponse>('/health');
  },

  async checkDatabaseHealth(): Promise<DatabaseHealthResponse> {
    return apiFetch<DatabaseHealthResponse>('/health/db');
  },
};
