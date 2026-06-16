import { CapacitorHttp, HttpOptions, HttpResponse } from '@capacitor/core';
import { Preferences } from '@capacitor/preferences';

export interface ApiResponse<T> {
  data: T;
  status: number;
  headers: Record<string, string>;
}

export class UnauthorizedError extends Error {
  public readonly status: 401 = 401;
  public readonly url: string;

  constructor(url: string) {
    super(`Unauthorized request to ${url}`);
    this.name = 'UnauthorizedError';
    this.url = url;
  }
}

const AUTH_TOKEN_KEY = 'auth_token';

async function request<T = unknown>(
  options: HttpOptions,
): Promise<ApiResponse<T>> {
  const headers: Record<string, string> = { ...options.headers };

  // Read token from Preferences and inject if present
  const { value: token } = await Preferences.get({ key: AUTH_TOKEN_KEY });
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response: HttpResponse = await CapacitorHttp.request({
    ...options,
    headers,
  });

  const { data, status, headers: responseHeaders } = response;

  if (status >= 200 && status < 300) {
    return { data: data as T, status, headers: responseHeaders };
  }

  if (status === 401) {
    await Preferences.remove({ key: AUTH_TOKEN_KEY });
    throw new UnauthorizedError(options.url);
  }

  throw new Error(`HTTP ${status}`);
}

export function httpGet<T = unknown>(
  url: string,
  params?: Record<string, string>,
): Promise<ApiResponse<T>> {
  const options: HttpOptions = {
    method: 'GET',
    url,
  };

  if (params) {
    options.params = params;
  }

  return request<T>(options);
}

export function httpPost<T = unknown, B = unknown>(
  url: string,
  body?: B,
): Promise<ApiResponse<T>> {
  const options: HttpOptions = {
    method: 'POST',
    url,
  };

  if (body !== undefined) {
    options.data = body;
    options.headers = { 'Content-Type': 'application/json' };
  }

  return request<T>(options);
}
