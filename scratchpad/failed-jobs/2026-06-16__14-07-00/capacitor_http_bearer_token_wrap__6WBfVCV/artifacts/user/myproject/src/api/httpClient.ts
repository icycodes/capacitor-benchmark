import { CapacitorHttp } from '@capacitor/core';
import type { HttpOptions } from '@capacitor/core';
import { Preferences } from '@capacitor/preferences';

export interface ApiResponse<T> {
  data: T;
  status: number;
  headers: Record<string, string>;
}

export class UnauthorizedError extends Error {
  status: 401;
  url: string;

  constructor(url: string) {
    super(`Unauthorized request to ${url}`);
    this.name = 'UnauthorizedError';
    this.status = 401;
    this.url = url;
    Object.setPrototypeOf(this, UnauthorizedError.prototype);
  }
}

async function buildAuthHeaders(): Promise<Record<string, string>> {
  const { value } = await Preferences.get({ key: 'auth_token' });
  const headers: Record<string, string> = {};
  if (value !== null && value !== '') {
    headers['Authorization'] = `Bearer ${value}`;
  }
  return headers;
}

async function executeRequest<T>(options: HttpOptions): Promise<ApiResponse<T>> {
  const response = await CapacitorHttp.request(options);

  if (response.status === 401) {
    await Preferences.remove({ key: 'auth_token' });
    throw new UnauthorizedError(options.url);
  }

  if (response.status < 200 || response.status > 299) {
    throw new Error(`HTTP ${response.status}`);
  }

  return {
    data: response.data as T,
    status: response.status,
    headers: response.headers as Record<string, string>,
  };
}

export async function httpGet<T = unknown>(
  url: string,
  params?: Record<string, string>,
): Promise<ApiResponse<T>> {
  const headers = await buildAuthHeaders();

  const options: HttpOptions = {
    method: 'GET',
    url,
    headers,
    ...(params !== undefined ? { params } : {}),
  };

  return executeRequest<T>(options);
}

export async function httpPost<T = unknown, B = unknown>(
  url: string,
  body?: B,
): Promise<ApiResponse<T>> {
  const headers = await buildAuthHeaders();

  const options: HttpOptions = {
    method: 'POST',
    url,
    headers,
    ...(body !== undefined
      ? {
          data: body,
          headers: { ...headers, 'Content-Type': 'application/json' },
        }
      : {}),
  };

  return executeRequest<T>(options);
}
