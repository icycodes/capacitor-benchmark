import { CapacitorHttp } from '@capacitor/core';
import type { HttpOptions, HttpResponse } from '@capacitor/core';
import { Preferences } from '@capacitor/preferences';

export interface ApiResponse<T> {
  data: T;
  status: number;
  headers: Record<string, string>;
}

export class UnauthorizedError extends Error {
  status: 401;
  url: string;

  constructor(message: string, url: string) {
    super(message);
    this.status = 401;
    this.url = url;
    Object.setPrototypeOf(this, UnauthorizedError.prototype);
  }
}

async function makeRequest<T = unknown>(
  url: string,
  method: 'GET' | 'POST',
  params?: Record<string, string>,
  body?: unknown,
): Promise<ApiResponse<T>> {
  const { value } = await Preferences.get({ key: 'auth_token' });
  const headers: Record<string, string> = {};

  if (value !== null && value !== '') {
    headers['Authorization'] = `Bearer ${value}`;
  }

  const options: HttpOptions = {
    url,
    method,
    headers,
  };

  if (params !== undefined) {
    options.params = params;
  }

  if (method === 'POST') {
    if (body !== undefined) {
      options.data = body;
      headers['Content-Type'] = 'application/json';
    }
  }

  const response: HttpResponse = await CapacitorHttp.request(options);

  if (response.status === 401) {
    await Preferences.remove({ key: 'auth_token' });
    throw new UnauthorizedError(`Unauthorized request to ${url}`, url);
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

export function httpGet<T = unknown>(
  url: string,
  params?: Record<string, string>,
): Promise<ApiResponse<T>> {
  return makeRequest<T>(url, 'GET', params);
}

export function httpPost<T = unknown, B = unknown>(
  url: string,
  body?: B,
): Promise<ApiResponse<T>> {
  return makeRequest<T>(url, 'POST', undefined, body);
}
