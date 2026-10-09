/**
 * Base API client for CyberShield AI frontend.
 * Communicates with the FastAPI backend at /api/v1.
 */

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export interface ApiErrorDetail {
  code?: string;
  message: string;
  details?: unknown[];
}

export class ApiError extends Error {
  code: string;
  status: number;
  details: unknown[];

  constructor(status: number, message: string, code: string = 'ERROR', details: unknown[] = []) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

const TOKEN_KEY = 'cybershield_token';
const USER_KEY = 'cybershield_user';

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setStoredToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function removeStoredToken(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function getStoredUser(): unknown | null {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function setStoredUser(user: unknown): void {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  let url = path;
  if (!url.startsWith('http')) {
    const cleanPath = path.startsWith('/') ? path : `/${path}`;
    const prefix = cleanPath.startsWith('/api/v1') ? '' : '/api/v1';
    url = `${API_BASE_URL}${prefix}${cleanPath}`;
  }

  const token = getStoredToken();
  const headers = new Headers(options.headers || {});

  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const config: RequestInit = {
    ...options,
    headers,
  };

  let response: Response;
  try {
    response = await fetch(url, config);
  } catch (error) {
    throw new ApiError(
      0,
      'Network error: Unable to reach the CyberShield AI backend. Verify server is running.',
      'NETWORK_ERROR'
    );
  }

  if (response.status === 204) {
    return {} as T;
  }

  const contentType = response.headers.get('content-type');
  const isJson = contentType && contentType.includes('application/json');
  let data: any = null;

  try {
    data = isJson ? await response.json() : await response.text();
  } catch (e) {
    data = null;
  }

  if (!response.ok) {
    let errorCode = `HTTP_${response.status}`;
    let errorMessage = `Request failed with status ${response.status}`;
    let errorDetails: unknown[] = [];

    if (data && typeof data === 'object') {
      if (data.error) {
        errorCode = data.error.code || errorCode;
        errorMessage = data.error.message || errorMessage;
        errorDetails = data.error.details || [];
      } else if (data.detail) {
        if (typeof data.detail === 'object' && data.detail.error) {
          errorCode = data.detail.error.code || errorCode;
          errorMessage = data.detail.error.message || errorMessage;
          errorDetails = data.detail.error.details || [];
        } else if (typeof data.detail === 'string') {
          errorMessage = data.detail;
        }
      } else if (data.message) {
        errorMessage = data.message;
      }
    }

    // Auto-clear invalid credentials
    if (response.status === 401 && !path.includes('/auth/login')) {
      removeStoredToken();
    }

    throw new ApiError(response.status, errorMessage, errorCode, errorDetails);
  }

  return data as T;
}
