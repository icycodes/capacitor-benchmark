import { CapacitorHttp } from '@capacitor/core';
import type { HttpOptions, HttpResponse } from '@capacitor/core';
import { Preferences } from '@capacitor/preferences';

const AUTH_TOKEN_KEY = 'auth_token';

export interface ApiResponse<T> {
  data: T;
  status: number;
  headers: Record<string, string>;
}

export class UnauthorizedError extends Error {
  status: 401;
  url: string;

  constructor(url: string) {
    super(`Unauthorized: ${url}`);
    this.name = 'UnauthorizedError';
    this.status = 401;
    this.url = url;
  }
}

async function request<T>(
  method: string,
  url: string,
  options?: {
    params?: Record<string, string>;
    body?: unknown;
  },
): Promise<ApiResponse<T>> {
  const { value: token } = await Preferences.get({ key: AUTH_TOKEN_KEY });

  const headers: Record<string, string> = {};

  if (token !== null && token !== '') {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const requestOptions: HttpOptions = {
    url,
    method,
    headers,
  };

  if (options?.params) {
    requestOptions.params = options.params;
  }

  if (options?.body !== undefined) {
    requestOptions.data = JSON.stringify(options.body);
    headers['Content-Type'] = 'application/json';
  }

  const response: HttpResponse = await CapacitorHttp.request(requestOptions);

  if (response.status === 401) {
    await Preferences.remove({ key: AUTH_TOKEN_KEY });
    throw new UnauthorizedError(url);
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
  return request<T>('GET', url, { params });
}

export function httpPost<T = unknown, B = unknown>(
  url: string,
  body?: B,
): Promise<ApiResponse<T>> {
  return request<T>('POST', url, { body });
}