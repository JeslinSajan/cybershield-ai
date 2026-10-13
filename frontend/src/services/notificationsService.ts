/**
 * Notifications service for CyberShield AI.
 * Handles listing, unread count polling, and marking notifications as read.
 */

import { apiFetch } from './api';

export interface NotificationItem {
  id: string;
  organization_id: string;
  user_id?: string | null;
  alert_id?: string | null;
  notification_type: string;
  channel: string;
  title: string;
  body: string;
  is_read: boolean;
  created_at: string;
  updated_at: string;
}

export const notificationsService = {
  /**
   * List notifications for user with optional is_read filter.
   */
  async listNotifications(params?: { is_read?: boolean; limit?: number; offset?: number }): Promise<NotificationItem[]> {
    const q = new URLSearchParams();
    if (params?.is_read !== undefined) q.set('is_read', params.is_read.toString());
    if (params?.limit) q.set('limit', params.limit.toString());
    if (params?.offset) q.set('offset', params.offset.toString());
    const queryStr = q.toString() ? `?${q.toString()}` : '';
    return apiFetch<NotificationItem[]>(`/notifications/${queryStr}`);
  },

  /**
   * Get unread count for badge indicators.
   */
  async getUnreadCount(): Promise<number> {
    try {
      const res = await apiFetch<{ unread_count: number }>('/notifications/unread-count');
      return res.unread_count || 0;
    } catch {
      return 0;
    }
  },

  /**
   * Mark a single notification as read.
   */
  async markRead(notificationId: string): Promise<NotificationItem> {
    return apiFetch<NotificationItem>(`/notifications/${notificationId}/read`, {
      method: 'PATCH',
    });
  },

  /**
   * Mark all unread notifications as read.
   */
  async markAllRead(): Promise<void> {
    await apiFetch<{ message: string }>('/notifications/mark-all-read', {
      method: 'POST',
    });
  },
};
