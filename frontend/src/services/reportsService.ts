/**
 * Reports service for CyberShield AI.
 * Handles generation, listing, retrieval, and binary PDF/CSV download.
 */

import { apiFetch, getStoredToken, API_BASE_URL, ApiError } from './api';

export interface ReportItem {
  id: string;
  organization_id: string;
  created_by_user_id: string;
  report_type: 'security_overview' | 'vulnerability' | 'alert';
  period_start: string;
  period_end: string;
  file_name: string | null;
  mime_type: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface GenerateReportPayload {
  type: 'security_overview' | 'vulnerability' | 'alert';
  from_date: string;
  to_date: string;
}

export const reportsService = {
  /**
   * List reports for user's organization.
   */
  async listReports(params?: { type?: string; limit?: number; offset?: number }): Promise<ReportItem[]> {
    const q = new URLSearchParams();
    if (params?.type && params.type !== 'all') q.set('type', params.type);
    if (params?.limit) q.set('limit', params.limit.toString());
    if (params?.offset) q.set('offset', params.offset.toString());
    const queryStr = q.toString() ? `?${q.toString()}` : '';
    return apiFetch<ReportItem[]>(`/reports/${queryStr}`);
  },

  /**
   * Get single report by ID.
   */
  async getReport(reportId: string): Promise<ReportItem> {
    return apiFetch<ReportItem>(`/reports/${reportId}`);
  },

  /**
   * Request report generation (Analyst or Admin only).
   */
  async generateReport(payload: GenerateReportPayload): Promise<ReportItem> {
    return apiFetch<ReportItem>('/reports/', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  /**
   * Download report file (PDF or CSV) directly as blob and trigger browser save.
   */
  async downloadReport(reportId: string, format: 'pdf' | 'csv' = 'pdf', filenameHint?: string): Promise<void> {
    const token = getStoredToken();
    const downloadUrl = `${API_BASE_URL}/api/v1/reports/${reportId}/download?format=${format}`;

    const response = await fetch(downloadUrl, {
      method: 'GET',
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    });

    if (!response.ok) {
      let errorMsg = `Download failed with status ${response.status}`;
      try {
        const errJson = await response.json();
        if (errJson?.error?.message) {
          errorMsg = errJson.error.message;
        }
      } catch {
        // use default error message
      }
      throw new ApiError(response.status, errorMsg);
    }

    const blob = await response.blob();
    const blobUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = blobUrl;
    link.download = filenameHint || `cybershield_report_${reportId}.${format}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(blobUrl);
  },
};
